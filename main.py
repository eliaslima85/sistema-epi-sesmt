import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# --- CREDENCIAIS SUPABASE ---
# Substitua pelas suas chaves reais do painel Supabase
SUPABASE_URL = "aatkjhtrafuepwzzlrbm"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdGtqaHRyYWZ1ZXB3enpscmJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2Mjg5MTYsImV4cCI6MjA5NDIwNDkxNn0.65izu7Zhc3kUZrVIRXGvVQ5o-Lhk-7PCK9CMg4zIwuk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SESMT - HUC Digital", layout="wide", page_icon="🛡️")

# --- FUNÇÕES DE APOIO ---
def formatar_data_br(data_str):
    try:
        dt = datetime.strptime(str(data_str).split('T')[0], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except: return data_str

# --- GERAÇÃO DE PDF (CORRIGIDO: SEM A PALAVRA "NOME") ---
def gerar_pdf_ficha(f, df):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "HOSPITAL UNIVERSITARIO DO CEARA - HUC - ISGH", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    
    # --- AQUI ESTÁ A CORREÇÃO DO CNPJ (SEM "NOME E") ---
    pdf.cell(0, 6, "CNPJ: 05.268.526/0024-67", ln=True, align='C') 
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " FICHA DE ENTREGA DE EPI - NR 06", ln=True, align='L', fill=True); pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(100, 7, f"NOME: {f['nome']}", 0); pdf.cell(90, 7, f"MATRICULA: {f['matricula']}", ln=True)
    pdf.cell(100, 7, f"FUNCAO: {f['funcao']}", 0); pdf.cell(90, 7, f"ADMISSAO: {formatar_data_br(f['admissao'])}", ln=True)
    pdf.cell(100, 7, f"SETOR: {f['setor']}", 0); pdf.cell(90, 7, f"VINCULO: {f['vinculo']}", ln=True); pdf.ln(5)
    
    # Tabela com Validade
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(25, 8, "DATA", 1, 0, 'C', fill=True); pdf.cell(55, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True)
    pdf.cell(20, 8, "C.A.", 1, 0, 'C', fill=True); pdf.cell(25, 8, "VALID. C.A.", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "TOKEN", 1, 0, 'C', fill=True); pdf.cell(40, 8, "STATUS", 1, ln=True, align='C', fill=True)
    
    pdf.set_font("Arial", size=7)
    for _, r in df.iterrows():
        pdf.cell(25, 8, str(r['data_entrega']), 1, 0, 'C')
        pdf.cell(55, 8, str(r['epi_nome'])[:35], 1)
        pdf.cell(20, 8, str(r['ca']), 1, 0, 'C')
        pdf.cell(25, 8, formatar_data_br(r['validade_epi']), 1, 0, 'C')
        pdf.cell(25, 8, str(r['token']), 1, 0, 'C')
        pdf.cell(40, 8, str(r['status']), 1, ln=True, align='C')
    
    pdf.ln(10); pdf.set_font("Arial", 'I', 8)
    # --- TEXTO LEGAL DA NR 6 ---
    texto_nr6 = '6.5.1 alinea d da NR 6 "d) registrar o seu fornecimento ao empregado, podendo ser adotados livros, fichas ou sistema eletronico, inclusive, por sistema biometrico;"'
    pdf.multi_cell(0, 5, texto_nr6, align='J')
    
    pdf.set_y(-20); pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 10, "Documento assinado eletronicamente via Token de Seguranca.", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE ASSINATURA ---
if "confirmar" in st.query_params:
    tk = st.query_params["confirmar"]
    supabase.table("entregas").update({"status": "Confirmado ✅"}).eq("token", tk).execute()
    st.balloons(); st.success("🛡️ RECEBIMENTO CONFIRMADO!"); st.stop()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.markdown('<h1 style="text-align:center;">🛡️ SESMT HUC</h1>', unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == "1234": st.session_state.logado = True; st.rerun()
    st.stop()

# --- BUSCA URL DO SISTEMA ---
res_url = supabase.table("oficiais").select("whatsapp").eq("matricula", "URL_SISTEMA").execute()
url_base = res_url.data[0]['whatsapp'] if res_url.data else "https://sesmt-huc-app.streamlit.app"

menu = st.sidebar.radio("MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "📄 Ficha de EPI", "⚙️ Configurações"])

# --- DASHBOARD (CORRIGIDO: COM BOTÃO REENVIAR) ---
if menu == "📊 Dashboard":
    st.markdown("### 📊 Monitoramento de Entregas")
    
    # Alerta de última confirmação
    recentes = supabase.table("entregas").select("*, oficiais(nome), ep(nome)").eq("status", "Confirmado ✅").order("id", desc=True).limit(1).execute()
    if recentes.data:
        st.success(f"✅ **INFORMATIVO:** {recentes.data[0]['oficiais']['nome']} confirmou o recebimento de: {recentes.data[0]['ep']['nome']}")

    # LISTA COM FUNÇÃO DE REENVIAR
    res = supabase.table("entregas").select("*, oficiais(nome, whatsapp), ep(nome)").order("id", desc=True).limit(15).execute()
    if res.data:
        for row in res.data:
            c1, c2 = st.columns([4, 1])
            status_txt = row['status']
            status_cor = "🔴" if "Pendente" in status_txt else "🟢"
            c1.write(f"{status_cor} **{row['oficiais']['nome']}** - {row['ep']['nome']} - {status_txt}")
            
            # --- BOTÃO REENVIAR TOKEN ---
            if "Pendente" in status_txt:
                link_token = f"{url_base}/?confirmar={row['token']}"
                msg_zap = urllib.parse.quote(f"🛡️ *SESMT HUC*\nAssinatura pendente: {row['ep']['nome']}\nLink: {link_token}")
                c2.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{row["oficiais"]["whatsapp"]}&text={msg_zap}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:5px; border-radius:5px; cursor:pointer; width:100%;">📲 REENVIAR</button></a>', unsafe_allow_html=True)

# --- CATÁLOGO (CADASTRAR COM VALIDADE) ---
elif menu == "📦 Catálogo":
    st.markdown("### 📦 Cadastro de EPIs")
    t1, t2 = st.tabs(["➕ Novo EPI", "🔧 Gerenciar"])
    with t1:
        with st.form("cad_epi"):
            n_epi, ca_epi, val_epi = st.text_input("Nome do EPI"), st.text_input("C.A."), st.date_input("Validade C.A.")
            if st.form_submit_button("Salvar"):
                supabase.table("ep").insert({"nome": n_epi, "ca": ca_epi, "validade": str(val_epi)}).execute()
                st.success("EPI Salvo!"); st.rerun()
    with t2:
        df_cat = pd.DataFrame(supabase.table("ep").select("*").execute().data)
        st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)

# --- FICHA DE EPI ---
elif menu == "📄 Ficha de EPI":
    st.markdown("### 📄 Ficha de Entrega de EPI")
    df_f = pd.DataFrame(supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute().data)
    if not df_f.empty:
        sel = st.selectbox("Escolher Colaborador", df_f['matricula'] + " - " + df_f['nome'])
        f_d = df_f[df_f['matricula'] == sel.split(" - ")[0]].iloc[0]
        h_res = supabase.table("entregas").select("data_entrega, token, status, ep(nome, ca, validade)").eq("id_func", int(f_d['id'])).execute()
        if h_res.data:
            h_data = [{"data_entrega": r['data_entrega'], "epi_nome": r['ep']['nome'], "ca": r['ep']['ca'], "validade_epi": r['ep']['validade'], "token": r['token'], "status": r['status']} for r in h_res.data]
            df_h = pd.DataFrame(h_data)
            st.dataframe(df_h, use_container_width=True)
            if st.button("Gerar PDF"):
                st.download_button("Baixar PDF", gerar_pdf_ficha(f_d, df_h), f"Ficha_{f_d['matricula']}.pdf")

# --- FUNCIONÁRIOS ---
elif menu == "👥 Funcionários":
    st.markdown("### 👥 Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo", "🔧 Editar/Excluir"])
    with t1:
        with st.form("cad_f"):
            n, m, s = st.text_input("Nome"), st.text_input("Matricula"), st.text_input("Setor")
            f, adm, w = st.text_input("Função"), st.date_input("Admissão"), st.text_input("WhatsApp")
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"]) # ISGH Primeiro
            if st.form_submit_button("Salvar"):
                supabase.table("oficiais").insert({"nome": n, "matricula": m, "setor": s, "funcao": f, "admissao": str(adm), "vinculo": v, "whatsapp": w}).execute()
                st.success("Salvo!"); st.rerun()
    with t2:
        df_edit = pd.DataFrame(supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute().data)
        st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)

# --- CONFIGURAÇÕES ---
elif menu == "⚙️ Configurações":
    nova_url = st.text_input("URL Pública do App", url_base)
    if st.button("Salvar"):
        supabase.table("oficiais").upsert({"matricula": "URL_SISTEMA", "whatsapp": nova_url}).execute()
        st.success("URL Salva!")
