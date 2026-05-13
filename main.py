import streamlit as st
import sqlite3
import random
import pandas as pd
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SESMT - HUC Digital", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { color: #004a87; font-weight: bold; font-size: 28px; border-bottom: 3px solid #004a87; padding-bottom: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS ---
def conectar(): return sqlite3.connect('gestao_epi_sesmt.db', check_same_thread=False)
conn = conectar()
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS funcionarios (id INTEGER PRIMARY KEY, nome TEXT, matricula TEXT UNIQUE, setor TEXT, funcao TEXT, admissao TEXT, turno TEXT, vinculo TEXT, whatsapp TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS epis (id INTEGER PRIMARY KEY, nome TEXT, ca TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS entregas (id INTEGER PRIMARY KEY, id_func INTEGER, id_epi INTEGER, data TEXT, token TEXT, status TEXT DEFAULT "Pendente ⏳")')
c.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, senha TEXT, url_sistema TEXT)')

try:
    c.execute('ALTER TABLE config ADD COLUMN url_sistema TEXT')
    conn.commit()
except: pass

c.execute("INSERT OR IGNORE INTO config (id, senha, url_sistema) VALUES (1, '1234', 'https://sesmt-huc-app.streamlit.app')")
conn.commit()

# --- FUNÇÕES DE APOIO ---
def limpar_texto(texto):
    return str(texto).replace("✅", "").replace("⏳", "").replace("🛡️", "").strip().encode('latin-1', 'replace').decode('latin-1')

def colorir_status(val):
    if not isinstance(val, str): return ""
    color = 'red' if 'Pendente' in val else 'green'
    return f'color: {color}; font-weight: bold'

# --- GERAÇÃO DE PDF INDIVIDUAL (NR-06) ---
def gerar_pdf_ficha(f, df, titulo_doc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, "HOSPITAL UNIVERSITARIO DO CEARA - HUC - ISGH", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, "CNPJ: 05.268.526/0024-67", ln=True, align='C') # CNPJ LIMPO AQUI
    pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f" {titulo_doc}", ln=True, align='L', fill=True); pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(100, 7, f"NOME: {limpar_texto(f['nome'])}", 0)
    pdf.cell(90, 7, f"MATRICULA: {limpar_texto(f['matricula'])}", ln=True)
    pdf.cell(100, 7, f"FUNCAO: {limpar_texto(f['funcao'])}", 0)
    pdf.cell(90, 7, f"ADMISSAO: {limpar_texto(f['admissao'])}", ln=True)
    pdf.cell(100, 7, f"SETOR: {limpar_texto(f['setor'])}", 0)
    pdf.cell(90, 7, f"VINCULO: {limpar_texto(f['vinculo'])}", ln=True); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(25, 8, "DATA", 1, 0, 'C', fill=True); pdf.cell(75, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True)
    pdf.cell(25, 8, "C.A.", 1, 0, 'C', fill=True); pdf.cell(30, 8, "TOKEN", 1, 0, 'C', fill=True)
    pdf.cell(35, 8, "STATUS", 1, ln=True, align='C', fill=True)
    
    pdf.set_font("Arial", size=8)
    for _, r in df.iterrows():
        pdf.cell(25, 8, limpar_texto(r['data']), 1, 0, 'C')
        pdf.cell(75, 8, limpar_texto(r['nome'])[:40], 1)
        pdf.cell(25, 8, limpar_texto(r['ca']), 1, 0, 'C')
        pdf.cell(30, 8, limpar_texto(r['token']), 1, 0, 'C')
        pdf.cell(35, 8, limpar_texto(r['status']), 1, ln=True, align='C')
    
    pdf.set_y(-25); pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Rua Betel, s/n, no bairro Itaperi, em Fortaleza - CE", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- GERAÇÃO DE PDF RESUMO POR SETOR ---
def gerar_pdf_resumo_setor(df, setor_nome):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, "RESUMO DE CONSUMO DE EPI POR SETOR", ln=True, align='C')
    pdf.set_font("Arial", '', 10); pdf.cell(0, 6, f"SETOR: {limpar_texto(setor_nome)} | CNPJ: 05.268.526/0024-67", ln=True, align='C'); pdf.ln(5)
    pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(100, 8, "DESCRICAO DO EPI", 1, 0, 'C', fill=True); pdf.cell(40, 8, "QUANTIDADE", 1, ln=True, align='C', fill=True)
    pdf.set_font("Arial", size=9)
    for _, r in df.iterrows():
        pdf.cell(100, 8, limpar_texto(r['EPI']), 1); pdf.cell(40, 8, str(r['Qtd']), 1, ln=True, align='C')
    pdf.set_y(-25); pdf.set_font("Arial", 'I', 8); pdf.cell(0, 10, f"HUC SESMT - Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE ASSINATURA ---
if "confirmar" in st.query_params:
    tk = st.query_params["confirmar"]
    c.execute("UPDATE entregas SET status = 'Confirmado ✅' WHERE token = ?", (tk,))
    conn.commit(); st.balloons(); st.success("Assinatura NR-06 Confirmada!"); st.stop()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.markdown('<h1 style="text-align:center;">🛡️ SESMT HUC</h1>', unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        c.execute("SELECT senha FROM config WHERE id=1")
        if senha == c.fetchone()[0]: st.session_state.logado = True; st.rerun()
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("SESMT MENU", ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "📑 Relatórios", "⚙️ Configurações"])

# --- DASHBOARD ---
if menu == "📊 Dashboard":
    st.markdown('<div class="main-header">📊 Resumo Operacional</div>', unsafe_allow_html=True)
    res = pd.read_sql_query('''SELECT f.nome as Colaborador, f.setor, ep.nome as EPI, e.data, e.status FROM entregas e 
                                JOIN funcionarios f ON e.id_func = f.id JOIN epis ep ON e.id_epi = ep.id 
                                ORDER BY e.id DESC LIMIT 10''', conn)
    st.dataframe(res.style.map(colorir_status, subset=['status']), use_container_width=True)

# --- ENTREGAR EPI ---
elif menu == "🚀 Entregar EPI":
    st.markdown('<div class="main-header">🚀 Registrar Entrega</div>', unsafe_allow_html=True)
    df_f = pd.read_sql_query("SELECT id, matricula, nome, whatsapp FROM funcionarios", conn)
    df_e = pd.read_sql_query("SELECT id, nome, ca FROM epis", conn)
    c.execute("SELECT url_sistema FROM config WHERE id=1"); url_base = c.fetchone()[0]
    busca = st.text_input("🔍 Localizar Colaborador (Nome ou Matrícula)")
    df_filt = df_f[df_f['nome'].str.contains(busca, case=False) | df_f['matricula'].str.contains(busca)] if busca else df_f
    if not df_filt.empty:
        f_sel = st.selectbox("Selecione", df_filt['matricula'] + " - " + df_filt['nome'])
        e_sel = st.multiselect("EPIs", df_e['nome'] + " (CA: " + df_e['ca'] + ")")
        if st.button("Gerar Entrega"):
            if e_sel:
                tk = str(random.randint(100000, 999999)); dt = datetime.now().strftime("%d/%m/%Y %H:%M") # DATA BR AQUI
                f_d = df_filt[df_filt['matricula'] == f_sel.split(" - ")[0]].iloc[0]
                for item in e_sel:
                    epi_id = df_e[df_e['nome'] == item.split(" (CA: ")[0]].iloc[0]['id']
                    c.execute("INSERT INTO entregas (id_func, id_epi, data, token) VALUES (?,?,?,?)", (int(f_d['id']), int(epi_id), dt, tk))
                conn.commit()
                link = f"{url_base}/?confirmar={tk}"
                msg = urllib.parse.quote(f"🛡️ *SESMT HUC*\nConfirme seu EPI: {', '.join(e_sel)}\nLink: {link}")
                st.markdown(f'<a href="https://api.whatsapp.com/send?phone=55{f_d["whatsapp"]}&text={msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:5px; font-weight:bold;">📲 WHATSAPP</button></a>', unsafe_allow_html=True)

# --- CENTRAL DE FUNCIONÁRIOS ---
elif menu == "👥 Funcionários":
    st.markdown('<div class="main-header">👥 Central de Cadastro</div>', unsafe_allow_html=True)
    t_c, t_u = st.tabs(["➕ Novo Cadastro", "🔧 Consultar, Editar e Excluir"])
    with t_c:
        with st.form("cad", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            n, m, s = c1.text_input("Nome"), c2.text_input("Matrícula"), c3.text_input("Setor")
            c4, c5, c6 = st.columns(3)
            f, adm, w = c4.text_input("Função"), c5.text_input("Admissão (DD/MM/AAAA)"), c6.text_input("WhatsApp") # FORMATO BR AQUI
            v = st.selectbox("Vínculo", ["ISGH", "Cooperado", "Terceirizado"]) # ISGH COMO PRIMEIRA OPÇÃO
            if st.form_submit_button("Salvar"):
                c.execute("INSERT INTO funcionarios (nome, matricula, setor, funcao, admissao, vinculo, whatsapp) VALUES (?,?,?,?,?,?,?)", (n,m,s,f,adm,v,w))
                conn.commit(); st.success("Cadastrado com sucesso!"); st.rerun()
    with t_u:
        df_f = pd.read_sql_query("SELECT * FROM funcionarios", conn)
        setor_f = st.selectbox("🏢 Filtrar por Setor", ["Todos"] + sorted(df_f['setor'].unique().tolist()))
        df_res = df_f[df_f['setor'] == setor_f] if setor_f != "Todos" else df_f
        # A OPÇÃO DE EXCLUIR ESTÁ ATIVA AQUI (Basta selecionar a linha e apertar delete no teclado)
        ed = st.data_editor(df_res, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Salvar Alterações (Sincronizar Banco)"):
            ed.to_sql('funcionarios', conn, if_exists='replace', index=False)
            st.success("Banco de dados atualizado!"); st.rerun()

# --- RELATÓRIOS ---
elif menu == "📑 Relatórios":
    st.markdown('<div class="main-header">📑 Central de Prontuários e Consumo</div>', unsafe_allow_html=True)
    t_i, t_s = st.tabs(["📄 Ficha Individual", "📊 Consumo por Setor"]) # RELATÓRIO POR SETOR AQUI
    with t_i:
        df_f = pd.read_sql_query("SELECT * FROM funcionarios", conn)
        if not df_f.empty:
            sel = st.selectbox("Colaborador", df_f['matricula'] + " - " + df_f['nome'])
            f_d = df_f[df_f['matricula'] == sel.split(" - ")[0]].iloc[0]
            h = pd.read_sql_query('''SELECT e.data, ep.nome, ep.ca, e.token, e.status FROM entregas e 
                                     JOIN epis ep ON e.id_epi = ep.id WHERE e.id_func = ? ORDER BY e.id DESC''', conn, params=(int(f_d['id']),))
            st.dataframe(h.style.map(colorir_status, subset=['status']), use_container_width=True)
            if st.button("📥 Baixar FICHA DE ENTREGA DE EPI - NR 06"): # TÍTULO NR-06 AQUI
                st.download_button("Download", gerar_pdf_ficha(f_d, h, "FICHA DE ENTREGA DE EPI - NR 06"), f"Ficha_{f_d['matricula']}.pdf")
    with t_s:
        df_setores = pd.read_sql_query("SELECT DISTINCT setor FROM funcionarios", conn)
        if not df_setores.empty:
            setor_sel = st.selectbox("Selecione o Setor para Resumo", df_setores['setor'])
            # QUANTIDADE POR TIPO DE EPI AQUI
            query_resumo = '''SELECT ep.nome as EPI, COUNT(e.id) as Qtd FROM entregas e 
                              JOIN funcionarios f ON e.id_func = f.id JOIN epis ep ON e.id_epi = ep.id 
                              WHERE f.setor = ? GROUP BY ep.nome'''
            df_resumo = pd.read_sql_query(query_resumo, conn, params=(setor_sel,))
            st.table(df_resumo)
            if st.button(f"📥 Baixar Resumo do Setor {setor_sel}"):
                pdf_res = gerar_pdf_resumo_setor(df_resumo, setor_sel)
                st.download_button("Confirmar Download", pdf_res, f"Resumo_Consumo_{setor_sel}.pdf")

# --- CATÁLOGO E CONFIG ---
elif menu == "📦 Catálogo":
    df_e = pd.read_sql_query("SELECT * FROM epis", conn)
    ed_e = st.data_editor(df_e, num_rows="dynamic", use_container_width=True)
    if st.button("Salvar Catálogo"): ed_e.to_sql('epis', conn, if_exists='replace', index=False); st.success("OK!")

elif menu == "⚙️ Configurações":
    c.execute("SELECT url_sistema FROM config WHERE id=1"); url_at = c.fetchone()[0]
    nova = st.text_input("URL Pública", url_at)
    if st.button("Salvar URL"): c.execute("UPDATE config SET url_sistema = ?", (nova,)); conn.commit(); st.success("OK!")
