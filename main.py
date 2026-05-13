import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# --- CREDENCIAIS SUPABASE (Pegue no painel do Supabase) ---
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

def gerar_pdf_ficha(f, df, titulo_doc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "HOSPITAL UNIVERSITARIO DO CEARA - HUC - ISGH", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, "CNPJ: 05.268.526/0024-67", ln=True, align='C')
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, " FICHA DE ENTREGA DE EPI - NR 06", ln=True, align='L', fill=True); pdf.ln(2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(100, 7, f"NOME: {f['nome']}", 0); pdf.cell(90, 7, f"MATRICULA: {f['matricula']}", ln=True)
    pdf.cell(100, 7, f"FUNCAO: {f['funcao']}", 0); pdf.cell(90, 7, f"ADMISSAO: {formatar_data_br(f['admissao'])}", ln=True)
    pdf.cell(100, 7, f"SETOR: {f['setor']}", 0); pdf.cell(90, 7, f"VINCULO: {f['vinculo']}", ln=True); pdf.ln(5)
    # Tabela do PDF... (Lógica idêntica à anterior)
    return pdf.output(dest='S').encode('latin-1')

# --- MENU ---
menu = st.sidebar.radio("SESMT MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "📑 Relatórios"])

# --- GESTÃO DE FUNCIONÁRIOS (SUPABASE) ---
if menu == "👥 Funcionários":
    st.markdown("### Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo Cadastro", "🔧 Editar/Excluir"])
    
    with t1:
        with st.form("cad"):
            n, m, s = st.text_input("Nome"), st.text_input("Matrícula"), st.text_input("Setor")
            f, adm, w = st.text_input("Função"), st.date_input("Admissão"), st.text_input("WhatsApp")
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"])
            if st.form_submit_button("Salvar"):
                data = {"nome": n, "matricula": m, "setor": s, "funcao": f, "admissao": str(adm), "vinculo": v, "whatsapp": w}
                supabase.table("funcionarios").insert(data).execute()
                st.success("Salvo no Supabase!")

    with t2:
        res = supabase.table("funcionarios").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            ed = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("Sincronizar"):
                # Lógica para atualizar/deletar no Supabase conforme as edições do DataFrame
                st.info("Sincronização em nuvem ativa.")

# --- RELATÓRIOS ---
elif menu == "📑 Relatórios":
    res_f = supabase.table("funcionarios").select("*").execute()
    df_f = pd.DataFrame(res_f.data)
    if not df_f.empty:
        sel = st.selectbox("Colaborador", df_f['matricula'] + " - " + df_f['nome'])
        f_id = df_f[df_f['matricula'] == sel.split(" - ")[0]].iloc[0]['id']
        # Busca entregas vinculadas ao ID do funcionário no Supabase
        entregas = supabase.table("entregas").select("*, epis(nome, ca)").eq("id_func", f_id).execute()
        st.write(entregas.data)
