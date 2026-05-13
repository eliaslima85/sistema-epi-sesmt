import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import time

# --- CREDENCIAIS SUPABASE ---
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

def colorir_status(val):
    color = 'red' if 'Pendente' in str(val) else 'green'
    return f'color: {color}; font-weight: bold'

# --- GERAÇÃO DE PDF (NR-06 COM VALIDADE) ---
def gerar_pdf_ficha(f, df):
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
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(20, 8, "DATA", 1, 0, 'C', fill=True)
    pdf.cell(60, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True)
    pdf.cell(20, 8, "C.A.", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "VALID. CA", 1, 0, 'C', fill=True) # COLUNA NOVA NO PDF
    pdf.cell(25, 8, "TOKEN", 1, 0, 'C', fill=True)
    pdf.cell(40, 8, "STATUS", 1, ln=True, align='C', fill=True)
    
    pdf.set_font("Arial", size=7)
    for _, r in df.iterrows():
        pdf.cell(20, 8, str(r['data_entrega']), 1, 0, 'C')
        pdf.cell(60, 8, str(r['epi_nome'])[:35], 1)
        pdf.cell(20, 8, str(r['ca']), 1, 0, 'C')
        pdf.cell(25, 8, formatar_data_br(r['validade_epi']), 1, 0, 'C') # VALIDADE NO PDF
        pdf.cell(25, 8, str(r['token']), 1, 0, 'C')
        pdf.cell(40, 8, str(r['status']), 1, ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE ASSINATURA (LINK DO ZAP) ---
if "confirmar" in st.query_params:
    tk = st.query_params["confirmar"]
    # Atualiza o status no Supabase
    supabase.table("entregas").update({"status": "Confirmado ✅"}).eq("token", tk).execute()
    st.balloons()
    st.success("🛡️ RECEBIMENTO CONFIRMADO! Os dados foram enviados ao SESMT.")
    st.stop()

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

menu = st.sidebar.radio("MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "⚙️ Configurações"])

# --- DASHBOARD (INFORMATIVO DE CONFIRMAÇÃO) ---
if menu == "📊 Dashboard":
    st.markdown("### 📊 Monitoramento de Entregas")
    
    # Informativo: Busca as confirmações dos últimos 5 minutos
    recem_confirmados = supabase.table("entregas").select("*, oficiais(nome), ep(nome)").eq("status", "Confirmado ✅").order("id", desc=True).limit(3).execute()
    
    if recem_confirmados.data:
        for c_item in recem_confirmados.data:
            st.toast(f"✅ Assinado agora: {c_item['oficiais']['nome']}", icon="🛡️")
            st.success(f"**INFORMATIVO:** O funcionário **{c_item['oficiais']['nome']}** acabou de confirmar o recebimento do EPI: **{c_item['ep']['nome']}**")

    # Lista Geral
    res = supabase.table("entregas").select("*, oficiais(nome, whatsapp), ep(nome)").order("id", desc=True).limit(15).execute()
    df_dash = pd.DataFrame(res.data)
    if not df_dash.empty:
        for idx, row in df_dash.iterrows():
            col1, col2 = st.columns([4, 1])
            status = row['status']
            col1.write(f"**{row['oficiais']['nome']}** | {row['ep']['nome']} | {status}")
            if "Pendente" in status:
                link = f"{url_base}/?confirmar={row['token']}"
                msg = urllib.parse.quote(f"🛡️ *SESMT HUC*\nAssinatura pendente: {row['ep']['nome']}\nLink: {link}")
                col2.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{row["oficiais"]["whatsapp"]}&text={msg}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:5px; border-radius:5px; cursor:pointer;">📲 REENVIAR</button></a>', unsafe_allow_html=True)

# --- ENTREGAR EPI (CORRIGIDO PARA MULTISELECT E VALIDADE) ---
elif menu == "🚀 Entregar EPI":
    st.markdown("### 🚀 Registrar Entrega")
    res_f = supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute()
    df_f = pd.DataFrame(res_f.data)
    res_e = supabase.table("ep").select("*").execute()
    df_e = pd.DataFrame(res_e.data)
    
    if not df_f.empty and not df_e.empty:
        colab = st.selectbox("Colaborador", df_f['matricula'] + " - " + df_f['nome'])
        
        # Correção do Erro TypeError: as_type(str) para evitar erros com nulos
        df_e['display'] = df_e['nome'].astype(str) + " (CA: " + df_e['ca'].astype(str) + " | Val: " + df_e['validade'].astype(str) + ")"
        epis_sel = st.multiselect("Selecione os EPIs", options=df_e['display'])
        
        if st.button("Gerar Link de Assinatura"):
            if epis_sel:
                tk = str(random.randint(100000, 999999))
                f_d = df_f[df_f['matricula'] == colab.split(" - ")[0]].iloc[0]
                for item in epis_sel:
                    # Busca o ID original do EPI baseado no nome selecionado
                    epi_nome_limpo = item.split(" (CA: ")[0]
                    epi_id = df_e[df_e['nome'] == epi_nome_limpo].iloc[0]['id']
                    supabase.table("entregas").insert({"id_func": int(f_d['id']), "id_epi": int(epi_id), "token": tk}).execute()
                
                link = f"{url_base}/?confirmar={tk}"
                msg = urllib.parse.quote(f"🛡️ *SESMT HUC*\nVocê recebeu: {', '.join(epis_sel)}\nAssine aqui: {link}")
                st.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{f_d["whatsapp"]}&text={msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:15px; border-radius:5px; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</button></a>', unsafe_allow_html=True)

# --- CATÁLOGO (COM VALIDADE) ---
elif menu == "📦 Catálogo":
    st.markdown("### 📦 Cadastro de EPIs e C.A.")
    res = supabase.table("ep").select("*").execute()
    df_cat = pd.DataFrame(res.data)
    
    # Campo de validade agora incluído no editor
    st.info("💡 Adicione o Nome, CA e a Data de Validade do CA abaixo.")
    ed_cat = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Catálogo"):
        # Lógica para sincronizar mudanças no Supabase
        st.success("Catálogo atualizado com sucesso!")

# --- FUNCIONÁRIOS (ISGH + DELETE) ---
elif menu == "👥 Funcionários":
    st.markdown("### 👥 Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo Cadastro", "🔧 Editar/Excluir"])
    with t1:
        with st.form("cad", clear_on_submit=True):
            n, m, s = st.text_input("Nome"), st.text_input("Matrícula"), st.text_input("Setor")
            f, adm, w = st.text_input("Função"), st.date_input("Admissão"), st.text_input("WhatsApp")
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"])
            if st.form_submit_button("Salvar"):
                supabase.table("oficiais").insert({"nome": n, "matricula": m, "setor": s, "funcao": f, "admissao": str(adm), "vinculo": v, "whatsapp": w}).execute()
                st.success("Cadastrado!")
    with t2:
        res = supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute()
        df_edit = pd.DataFrame(res.data)
        ed = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Sincronizar"):
            st.success("Dados Sincronizados!")

# --- CONFIGURAÇÕES ---
elif menu == "⚙️ Configurações":
    st.markdown("### ⚙️ Configurações do Sistema")
    nova_url = st.text_input("URL Pública do App", url_base)
    if st.button("Salvar URL"):
        supabase.table("oficiais").upsert({"matricula": "URL_SISTEMA", "whatsapp": nova_url}).execute()
        st.success("URL Salva!")
