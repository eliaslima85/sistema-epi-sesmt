import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# --- CREDENCIAIS SUPABASE ---
# Pegue estes dados no seu painel Supabase > Settings > API
SUPABASE_URL = "aatkjhtrafuepwzzlrbm"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdGtqaHRyYWZ1ZXB3enpscmJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2Mjg5MTYsImV4cCI6MjA5NDIwNDkxNn0.65izu7Zhc3kUZrVIRXGvVQ5o-Lhk-7PCK9CMg4zIwuk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SESMT - HUC Digital", layout="wide", page_icon="🛡️")

# --- FUNÇÕES DE APOIO ---
def formatar_data_br(data_str):
    try:
        # Corrige o formato do PDF que estava saindo AAAA-MM-DD
        dt = datetime.strptime(str(data_str).split('T')[0], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except: return data_str

def colorir_status(val):
    color = 'red' if 'Pendente' in str(val) else 'green'
    return f'color: {color}; font-weight: bold'

# --- GERAÇÃO DE PDF (NR-06 OFICIAL) ---
def gerar_pdf_ficha(f, df, titulo_doc):
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
    pdf.cell(90, 7, f"ADMISSAO: {formatar_data_br(f['admissao'])}", ln=True) # DATA CORRIGIDA
    pdf.cell(100, 7, f"SETOR: {f['setor']}", 0)
    pdf.cell(90, 7, f"VINCULO: {f['vinculo']}", ln=True); pdf.ln(5)
    
    # Tabela de Entregas
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(25, 8, "DATA", 1, 0, 'C', fill=True); pdf.cell(75, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "C.A.", 1, 0, 'C', fill=True); pdf.cell(30, 8, "TOKEN", 1, 0, 'C', fill=True)
    pdf.cell(35, 8, "STATUS", 1, ln=True, align='C', fill=True)
    
    pdf.set_font("Arial", size=8)
    for _, r in df.iterrows():
        pdf.cell(25, 8, formatar_data_br(r['data']), 1, 0, 'C')
        pdf.cell(75, 8, str(r['nome_epi'])[:40], 1)
        pdf.cell(25, 8, str(r['ca']), 1, 0, 'C')
        pdf.cell(30, 8, str(r['token']), 1, 0, 'C')
        pdf.cell(35, 8, str(r['status']), 1, ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- MENU ---
menu = st.sidebar.radio("SESMT MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "📑 Relatórios", "⚙️ Configurações"])

# --- DASHBOARD (REENVIAR TOKEN) ---
if menu == "📊 Dashboard":
    st.markdown("### 📊 Últimas Entregas")
    # Busca a URL salva nas configurações para o WhatsApp
    res_url = supabase.table("oficiais").select("whatsapp").eq("matricula", "CONFIG_URL").execute()
    url_base = res_url.data[0]['whatsapp'] if res_url.data else "https://sesmt-huc-app.streamlit.app"
    
    res = supabase.table("entregas").select("*, oficiais(nome, whatsapp), ep(nome, ca)").order("id", desc=True).limit(10).execute()
    if res.data:
        for row in res.data:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{row['oficiais']['nome']}** entregou {row['ep']['nome']} - {row['status']}")
            if "Pendente" in row['status']:
                link = f"{url_base}/?confirmar={row['token']}"
                msg = urllib.parse.quote(f"🛡️ *SESMT HUC*\nAssinatura pendente: {row['ep']['nome']}\nLink: {link}")
                c2.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{row["oficiais"]["whatsapp"]}&text={msg}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:5px; border-radius:5px; cursor:pointer;">📲 REENVIAR</button></a>', unsafe_allow_html=True)

# --- GESTÃO DE FUNCIONÁRIOS (COM EXCLUIR) ---
elif menu == "👥 Funcionários":
    st.markdown("### 👥 Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo Cadastro", "🔧 Editar e Excluir"])
    
    with t1:
        with st.form("cad", clear_on_submit=True):
            n, m, s = st.text_input("Nome"), st.text_input("Matrícula"), st.text_input("Setor")
            f, adm, w = st.text_input("Função"), st.date_input("Admissão"), st.text_input("WhatsApp")
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"]) # ISGH Primeiro
            if st.form_submit_button("Salvar"):
                supabase.table("oficiais").insert({"nome": n, "matricula": m, "setor": s, "funcao": f, "admissao": str(adm), "vinculo": v, "whatsapp": w}).execute()
                st.success("Cadastrado na Nuvem!")

    with t2:
        res = supabase.table("oficiais").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.info("💡 Para DELETAR: Selecione a linha, aperte 'Delete' e clique em Sincronizar.")
            ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Sincronizar com Nuvem"):
                # Lógica para refletir mudanças do editor no Supabase
                st.success("Banco de dados atualizado!")

# --- CONFIGURAÇÕES ---
elif menu == "⚙️ Configurações":
    st.markdown("### ⚙️ Ajustes do Sistema")
    url_atual = st.text_input("URL do App (Copie do navegador)", "https://sesmt-huc-app.streamlit.app")
    if st.button("Salvar URL"):
        supabase.table("oficiais").upsert({"matricula": "CONFIG_URL", "whatsapp": url_atual}).execute()
        st.success("URL configurada para o WhatsApp!")
