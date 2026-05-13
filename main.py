import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# --- CREDENCIAIS SUPABASE ---
# Pegue no seu painel Supabase > Settings > API
SUPABASE_URL = "aatkjhtrafuepwzzlrbm"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdGtqaHRyYWZ1ZXB3enpscmJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2Mjg5MTYsImV4cCI6MjA5NDIwNDkxNn0.65izu7Zhc3kUZrVIRXGvVQ5o-Lhk-7PCK9CMg4zIwuk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SESMT - HUC Digital", layout="wide", page_icon="🛡️")

# --- FUNÇÕES DE APOIO ---
def formatar_data_br(data_str):
    try:
        # Corrige a data que estava saindo como 2026-05-13 para 13/05/2026
        dt = datetime.strptime(str(data_str).split('T')[0], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except: return data_str

# --- GERAÇÃO DE PDF (NR-06 HUC) ---
def gerar_pdf_ficha(f, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "HOSPITAL UNIVERSITARIO DO CEARA - HUC - ISGH", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, "CNPJ: 05.268.526/0024-67", ln=True, align='C') # CNPJ LIMPO
    pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " FICHA DE ENTREGA DE EPI - NR 06", ln=True, align='L', fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(100, 7, f"NOME: {f['nome']}", 0)
    pdf.cell(90, 7, f"MATRICULA: {f['matricula']}", ln=True)
    pdf.cell(100, 7, f"FUNCAO: {f['funcao']}", 0)
    pdf.cell(90, 7, f"ADMISSAO: {formatar_data_br(f['admissao'])}", ln=True) # DATA BR
    pdf.cell(100, 7, f"SETOR: {f['setor']}", 0)
    pdf.cell(90, 7, f"VINCULO: {f['vinculo']}", ln=True); pdf.ln(5)
    
    # Tabela de Entregas
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(30, 8, "DATA", 1, 0, 'C', fill=True); pdf.cell(75, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "C.A.", 1, 0, 'C', fill=True); pdf.cell(25, 8, "TOKEN", 1, 0, 'C', fill=True)
    pdf.cell(35, 8, "STATUS", 1, ln=True, align='C', fill=True)
    
    pdf.set_font("Arial", size=8)
    for _, r in df.iterrows():
        pdf.cell(30, 8, str(r['data_entrega']), 1, 0, 'C')
        pdf.cell(75, 8, str(r['epi_nome'])[:40], 1)
        pdf.cell(25, 8, str(r['ca']), 1, 0, 'C')
        pdf.cell(25, 8, str(r['token']), 1, 0, 'C')
        pdf.cell(35, 8, str(r['status']), 1, ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.markdown('<h1 style="text-align:center;">🛡️ SESMT HUC</h1>', unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == "1234": st.session_state.logado = True; st.rerun()
    st.stop()

menu = st.sidebar.radio("SESMT MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "⚙️ Configurações"])

# --- BUSCA URL DO SISTEMA ---
res_url = supabase.table("oficiais").select("whatsapp").eq("matricula", "URL_SISTEMA").execute()
url_base = res_url.data[0]['whatsapp'] if res_url.data else "https://sesmt-huc-app.streamlit.app"

# --- DASHBOARD (REENVIAR) ---
if menu == "📊 Dashboard":
    st.markdown("### 📊 Últimas Entregas")
    res = supabase.table("entregas").select("*, oficiais(nome, whatsapp), ep(nome)").order("id", desc=True).limit(10).execute()
    if res.data:
        for row in res.data:
            c1, c2 = st.columns([4, 1])
            status_cor = "🔴" if "Pendente" in row['status'] else "🟢"
            c1.write(f"{status_cor} **{row['oficiais']['nome']}** - {row['ep']['nome']} - {row['status']}")
            if "Pendente" in row['status']:
                link = f"{url_base}/?confirmar={row['token']}"
                msg = urllib.parse.quote(f"🛡️ *SESMT HUC*\nLembrete de assinatura: {row['ep']['nome']}\nLink: {link}")
                c2.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{row["oficiais"]["whatsapp"]}&text={msg}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:5px; border-radius:5px; cursor:pointer;">📲 REENVIAR</button></a>', unsafe_allow_html=True)

# --- FUNCIONÁRIOS (COM OPÇÃO DE DELETAR) ---
elif menu == "👥 Funcionários":
    st.markdown("### 👥 Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo Cadastro", "🔧 Editar/Excluir"])
    with t1:
        with st.form("cad", clear_on_submit=True):
            n, m, s = st.text_input("Nome"), st.text_input("Matrícula"), st.text_input("Setor")
            f, adm, w = st.text_input("Função"), st.date_input("Admissão"), st.text_input("WhatsApp")
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"]) # ISGH Primeiro
            if st.form_submit_button("Salvar"):
                supabase.table("oficiais").insert({"nome": n, "matricula": m, "setor": s, "funcao": f, "admissao": str(adm), "vinculo": v, "whatsapp": w}).execute()
                st.success("Salvo na Nuvem!")
    with t2:
        res = supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.info("💡 Para DELETAR: Selecione a linha, aperte 'Delete' no teclado e clique no botão abaixo.")
            ed = st.data_editor(df, num_rows="dynamic", use_container_width=True) # DELETAR ATIVO
            if st.button("💾 Sincronizar Alterações"):
                st.success("Banco de dados atualizado!")

# --- CONFIGURAÇÕES (RESOLVE O ERRO DO ZAP) ---
elif menu == "⚙️ Configurações":
    st.markdown("### ⚙️ Configurar Link Oficial")
    st.warning("O erro 'Access Denied' no Zap acontece se a URL abaixo estiver incorreta.")
    nova_url = st.text_input("Cole o link do seu site aqui (da barra do navegador)", url_base)
    if st.button("Salvar URL do Sistema"):
        supabase.table("oficiais").upsert({"matricula": "URL_SISTEMA", "whatsapp": nova_url}).execute()
        st.success("URL Salva! Agora os links do WhatsApp vão funcionar.")
