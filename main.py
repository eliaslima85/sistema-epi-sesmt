import streamlit as st
from supabase import create_client, Client
import random
import pandas as pd
from datetime import datetime, date
import urllib.parse
from fpdf import FPDF

# --- CREDENCIAIS SUPABASE ---
SUPABASE_URL = "aatkjhtrafuepwzzlrbm"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdGtqaHRyYWZ1ZXB3enpscmJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2Mjg5MTYsImV4cCI6MjA5NDIwNDkxNn0.65izu7Zhc3kUZrVIRXGvVQ5o-Lhk-7PCK9CMg4zIwuk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="SESMT - HUC Digital", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="metric-container"] {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 10px;
        border-left: 4px solid #1a56db;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def formatar_data_br(data_str):
    if not data_str or str(data_str).strip() in ("None", "nan", ""):
        return "—"
    try:
        dt = datetime.strptime(str(data_str).split('T')[0], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return str(data_str)


# --- GERAÇÃO DE PDF (FICHA DE ENTREGA DE EPI - NR 06) ---
def gerar_pdf_ficha(f, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    pdf.set_fill_color(30, 64, 130)   # azul institucional
    pdf.rect(0, 0, 210, 28, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_xy(0, 5)
    pdf.cell(0, 8, "HOSPITAL UNIVERSITÁRIO DO CEARÁ — HUC", ln=True, align='C')

    pdf.set_font("Arial", '', 9)
    pdf.set_xy(0, 13)
    pdf.cell(0, 6, "Instituto de Saúde e Gestão Hospitalar — ISGH", ln=True, align='C')

    pdf.set_font("Arial", '', 8)
    pdf.set_xy(0, 19)
    # APENAS O CNPJ, sem "NOME E" na frente
    pdf.cell(0, 6, "CNPJ: 05.268.526/0024-67", ln=True, align='C')

    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # ── Título da ficha ────────────────────────────────────────────────────────
    pdf.set_fill_color(220, 230, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 9, "  FICHA DE ENTREGA DE EPI — NR 06", ln=True, align='L', fill=True)
    pdf.ln(3)

    # ── Dados do colaborador ───────────────────────────────────────────────────
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 9)

    def row_duplo(label1, val1, label2, val2):
        pdf.set_font("Arial", 'B', 8)
        pdf.set_fill_color(240, 240, 248)
        pdf.cell(25, 7, label1, 1, 0, 'L', fill=True)
        pdf.set_font("Arial", '', 8)
        pdf.cell(75, 7, str(val1), 1, 0, 'L')
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(25, 7, label2, 1, 0, 'L', fill=True)
        pdf.set_font("Arial", '', 8)
        pdf.cell(65, 7, str(val2), 1, ln=True, align='L')

    row_duplo("NOME:", f.get('nome', ''), "MATRÍCULA:", f.get('matricula', ''))
    row_duplo("FUNÇÃO:", f.get('funcao', ''), "ADMISSÃO:", formatar_data_br(f.get('admissao', '')))
    row_duplo("SETOR:", f.get('setor', ''), "VÍNCULO:", f.get('vinculo', ''))
    pdf.ln(5)

    # ── Tabela de entregas ─────────────────────────────────────────────────────
    pdf.set_fill_color(30, 64, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 7)

    # Cabeçalhos da tabela — agora com coluna VALIDADE DO EPI
    col_w = [22, 52, 18, 22, 22, 18, 36]
    headers = ["DATA", "DESCRIÇÃO DO EPI", "C.A.", "VALID. C.A.", "VALID. EPI", "TOKEN", "STATUS"]
    for h, w in zip(headers, col_w):
        pdf.cell(w, 8, h, 1, 0, 'C', fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=7)

    for i, (_, r) in enumerate(df.iterrows()):
        fill = i % 2 == 0
        pdf.set_fill_color(248, 250, 255) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_w[0], 7, str(r.get('data_entrega', '')), 1, 0, 'C', fill=fill)
        pdf.cell(col_w[1], 7, str(r.get('epi_nome', ''))[:32], 1, 0, 'L', fill=fill)
        pdf.cell(col_w[2], 7, str(r.get('ca', '')), 1, 0, 'C', fill=fill)
        pdf.cell(col_w[3], 7, formatar_data_br(r.get('validade_ca', '')), 1, 0, 'C', fill=fill)
        pdf.cell(col_w[4], 7, formatar_data_br(r.get('validade_epi', '')), 1, 0, 'C', fill=fill)
        pdf.cell(col_w[5], 7, str(r.get('token', '')), 1, 0, 'C', fill=fill)
        pdf.cell(col_w[6], 7, str(r.get('status', '')), 1, ln=True, align='C', fill=fill)

    pdf.ln(8)

    # ── Texto legal NR-6 ──────────────────────────────────────────────────────
    pdf.set_fill_color(255, 248, 220)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 6, "  BASE LEGAL", ln=True, fill=True)
    pdf.set_font("Arial", 'I', 8)
    nr6_text = (
        '6.5.1 alínea d da NR 6: "d) registrar o seu fornecimento ao empregado, '
        'podendo ser adotados livros, fichas ou sistema eletrônico, inclusive, '
        'por sistema biométrico;"'
    )
    pdf.multi_cell(0, 5, nr6_text, border=1, align='J')

    pdf.ln(5)

    # ── Assinatura ────────────────────────────────────────────────────────────
    pdf.set_draw_color(100, 100, 100)
    pdf.line(20, pdf.get_y() + 12, 95, pdf.get_y() + 12)
    pdf.line(115, pdf.get_y() + 12, 190, pdf.get_y() + 12)
    pdf.set_font("Arial", '', 7)
    y_sig = pdf.get_y() + 14
    pdf.set_xy(20, y_sig)
    pdf.cell(75, 5, "Assinatura do Colaborador", 0, 0, 'C')
    pdf.set_xy(115, y_sig)
    pdf.cell(75, 5, "Assinatura do Responsável SESMT", 0, ln=True, align='C')
    pdf.ln(6)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    pdf.set_y(-18)
    pdf.set_fill_color(30, 64, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'I', 7)
    pdf.cell(0, 8, "  Documento gerado eletronicamente via Token de Segurança — SESMT HUC / ISGH", 0, 0, 'L', fill=True)

    return pdf.output(dest='S').encode('latin-1')


# --- LÓGICA DE ASSINATURA (via link) ---
if "confirmar" in st.query_params:
    tk = st.query_params["confirmar"]
    supabase.table("entregas").update({"status": "Confirmado ✅"}).eq("token", tk).execute()
    st.balloons()
    st.success("🛡️ RECEBIMENTO CONFIRMADO NO SISTEMA!")
    st.stop()

# --- LOGIN ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    col_login = st.columns([1, 2, 1])[1]
    with col_login:
        st.markdown('<h2 style="text-align:center; margin-top:60px;">🛡️ SESMT HUC</h2>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#666;">Sistema de Gestão de EPI</p>', unsafe_allow_html=True)
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha == "1234":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# --- URL BASE DO APP ---
res_url = supabase.table("oficiais").select("whatsapp").eq("matricula", "URL_SISTEMA").execute()
url_base = res_url.data[0]['whatsapp'] if res_url.data else "https://sesmt-huc-app.streamlit.app"

# --- MENU LATERAL ---
st.sidebar.markdown("## 🛡️ SESMT HUC")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard", "🚀 Entregar EPI", "👥 Funcionários", "📦 Catálogo", "📄 Ficha de EPI", "⚙️ Configurações"]
)
st.sidebar.markdown("---")
if st.sidebar.button("🔒 Sair"):
    st.session_state.logado = False
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if menu == "📊 Dashboard":
    st.markdown("### 📊 Monitoramento de Entregas")

    # Métricas rápidas
    total_res = supabase.table("entregas").select("id", count="exact").execute()
    conf_res  = supabase.table("entregas").select("id", count="exact").eq("status", "Confirmado ✅").execute()
    pend_res  = supabase.table("entregas").select("id", count="exact").eq("status", "Pendente ⏳").execute()
    func_res  = supabase.table("oficiais").select("id", count="exact").not_.eq("matricula", "URL_SISTEMA").execute()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Entregas", total_res.count or 0)
    c2.metric("Confirmadas ✅", conf_res.count or 0)
    c3.metric("Pendentes ⏳", pend_res.count or 0)
    c4.metric("Colaboradores", func_res.count or 0)
    st.markdown("---")

    # Última confirmação
    recentes = supabase.table("entregas").select("*, oficiais(nome), ep(nome)").eq("status", "Confirmado ✅").order("id", desc=True).limit(1).execute()
    if recentes.data:
        d = recentes.data[0]
        st.success(f"✅ **Última confirmação:** {d['oficiais']['nome']} confirmou o recebimento de **{d['ep']['nome']}**")

    # Lista recente com botão reenviar
    st.markdown("#### Últimas 20 Entregas")
    res = supabase.table("entregas").select("*, oficiais(nome, whatsapp), ep(nome)").order("id", desc=True).limit(20).execute()
    if res.data:
        for row in res.data:
            c1, c2 = st.columns([5, 1])
            status_txt = row['status']
            icon = "🟢" if "Confirmado" in status_txt else "🔴"
            c1.markdown(f"{icon} **{row['oficiais']['nome']}** — {row['ep']['nome']} — `{status_txt}`")
            if "Pendente" in status_txt:
                link = f"{url_base}/?confirmar={row['token']}"
                msg  = urllib.parse.quote(
                    f"🛡️ *SESMT HUC*\nAssinatura de EPI pendente: {row['ep']['nome']}\nLink para assinar: {link}"
                )
                c2.markdown(
                    f'<a href="https://api.whatsapp.com/send?phone=55{row["oficiais"]["whatsapp"]}&text={msg}" target="_blank">'
                    f'<button style="background:#25D366;color:white;border:none;padding:5px 10px;border-radius:6px;cursor:pointer;width:100%;font-weight:bold;">📲 Reenviar</button></a>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE EPIs
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📦 Catálogo":
    st.markdown("### 📦 Cadastro de EPIs")
    t1, t2 = st.tabs(["➕ Novo EPI", "🔧 Gerenciar"])

    with t1:
        with st.form("cad_epi"):
            col1, col2 = st.columns(2)
            nome_e = col1.text_input("Nome do EPI *")
            ca_e   = col2.text_input("Número do C.A. *")
            val_ca = st.date_input("Validade do C.A.", min_value=date.today())

            st.markdown("---")
            if st.form_submit_button("💾 Salvar EPI", use_container_width=True):
                if nome_e and ca_e:
                    supabase.table("ep").insert({
                        "nome":     nome_e,
                        "ca":       ca_e,
                        "validade": str(val_ca)
                    }).execute()
                    st.success(f"✅ EPI **{nome_e}** cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha Nome e C.A.")

    with t2:
        df_cat = pd.DataFrame(supabase.table("ep").select("*").execute().data)
        if not df_cat.empty:
            st.data_editor(df_cat, num_rows="dynamic", use_container_width=True)
        else:
            st.info("Nenhum EPI cadastrado ainda.")


# ══════════════════════════════════════════════════════════════════════════════
# FICHA DE EPI
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📄 Ficha de EPI":
    st.markdown("### 📄 Ficha de Entrega de EPI")

    df_f = pd.DataFrame(
        supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute().data
    )
    if df_f.empty:
        st.warning("Nenhum colaborador cadastrado.")
    else:
        sel = st.selectbox("Selecionar Colaborador", df_f['matricula'] + " — " + df_f['nome'])
        mat = sel.split(" — ")[0]
        f_d = df_f[df_f['matricula'] == mat].iloc[0]

        # Busca histórico com join em ep (nome, ca, validade do C.A.)
        h_res = supabase.table("entregas").select(
            "data_entrega, token, status, validade_epi, ep(nome, ca, validade)"
        ).eq("id_func", int(f_d['id'])).execute()

        if h_res.data:
            h_data = []
            for r in h_res.data:
                h_data.append({
                    "data_entrega": formatar_data_br(r['data_entrega']),
                    "epi_nome":     r['ep']['nome'],
                    "ca":           r['ep']['ca'],
                    "validade_ca":  r['ep'].get('validade', ''),   # validade do C.A.
                    "validade_epi": r.get('validade_epi', ''),      # validade do EPI entregue
                    "token":        r['token'],
                    "status":       r['status'],
                })
            df_h = pd.DataFrame(h_data)

            st.dataframe(df_h, use_container_width=True)

            col_btn, _ = st.columns([1, 3])
            if col_btn.button("📄 Gerar PDF"):
                pdf_bytes = gerar_pdf_ficha(f_d, df_h)
                st.download_button(
                    "⬇️ Baixar Ficha de EPI",
                    pdf_bytes,
                    file_name=f"Ficha_EPI_{f_d['matricula']}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("Nenhuma entrega registrada para este colaborador.")


# ══════════════════════════════════════════════════════════════════════════════
# ENTREGAR EPI
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🚀 Entregar EPI":
    st.markdown("### 🚀 Registrar Entrega de EPI")

    df_f = pd.DataFrame(
        supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute().data
    )
    df_e = pd.DataFrame(supabase.table("ep").select("*").execute().data)

    if df_f.empty or df_e.empty:
        st.warning("Cadastre colaboradores e EPIs antes de registrar entregas.")
    else:
        colab     = st.selectbox("Selecione o Colaborador", df_f['matricula'] + " — " + df_f['nome'])
        df_e['disp'] = df_e['nome'].astype(str) + "  (C.A.: " + df_e['ca'].astype(str) + ")"
        sel_items = st.multiselect("EPIs para Entrega", options=df_e['disp'])

        # ── NOVO: campo de data de validade do EPI entregue ──────────────────
        st.markdown("#### 📅 Data de Validade do EPI Entregue")
        st.caption("Informe a validade impressa no produto/embalagem (ex.: luva, bota, capacete).")
        validade_epi_input = st.date_input(
            "Validade do EPI",
            value=None,
            min_value=date.today(),
            help="Data de validade do EPI físico entregue ao colaborador."
        )

        st.markdown("---")
        if st.button("📲 Gerar Entrega e Enviar WhatsApp", use_container_width=True):
            if not sel_items:
                st.warning("Selecione pelo menos um EPI.")
            else:
                tk  = str(random.randint(100000, 999999))
                mat = colab.split(" — ")[0]
                f_d = df_f[df_f['matricula'] == mat].iloc[0]
                val_str = str(validade_epi_input) if validade_epi_input else None

                for item in sel_items:
                    nome_epi = item.split("  (C.A.:")[0]
                    e_id = df_e[df_e['nome'] == nome_epi].iloc[0]['id']
                    supabase.table("entregas").insert({
                        "id_func":     int(f_d['id']),
                        "id_epi":      int(e_id),
                        "token":       tk,
                        "validade_epi": val_str,   # ← NOVO CAMPO GRAVADO
                        "status":      "Pendente ⏳"
                    }).execute()

                link = f"{url_base}/?confirmar={tk}"
                nomes_epi = ', '.join([i.split("  (C.A.:")[0] for i in sel_items])
                msg  = urllib.parse.quote(
                    f"🛡️ *SESMT HUC — Hospital Universitário do Ceará*\n\n"
                    f"Olá, *{f_d['nome']}*!\n\n"
                    f"Foi registrada a entrega dos seguintes EPIs:\n"
                    f"• {nomes_epi}\n\n"
                    f"Por favor, confirme o recebimento clicando no link abaixo:\n{link}\n\n"
                    f"Token: *{tk}*"
                )
                st.success(f"✅ Entrega registrada! Token: **{tk}**")
                st.markdown(
                    f'<a href="https://api.whatsapp.com/send?phone=55{f_d["whatsapp"]}&text={msg}" target="_blank">'
                    f'<button style="width:100%;background:#25D366;color:white;border:none;padding:15px;'
                    f'border-radius:8px;font-weight:bold;font-size:16px;cursor:pointer;">📲 ENVIAR AGORA PELO WHATSAPP</button></a>',
                    unsafe_allow_html=True
                )


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONÁRIOS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "👥 Funcionários":
    st.markdown("### 👥 Gestão de Colaboradores")
    t1, t2 = st.tabs(["➕ Novo Colaborador", "🔧 Editar / Excluir"])

    with t1:
        with st.form("cad_f"):
            col1, col2 = st.columns(2)
            n   = col1.text_input("Nome Completo *")
            m   = col2.text_input("Matrícula *")
            s   = col1.text_input("Setor *")
            f   = col2.text_input("Função *")
            adm = col1.date_input("Data de Admissão")
            w   = col2.text_input("WhatsApp (somente números)", placeholder="85999999999")
            v   = st.selectbox("Vínculo Empregatício", ["ISGH", "Cooperado", "Terceirizado"])

            st.markdown("---")
            if st.form_submit_button("💾 Cadastrar Colaborador", use_container_width=True):
                if n and m and s and f and w:
                    supabase.table("oficiais").insert({
                        "nome":      n,
                        "matricula": m,
                        "setor":     s,
                        "funcao":    f,
                        "admissao":  str(adm),
                        "vinculo":   v,
                        "whatsapp":  w
                    }).execute()
                    st.success(f"✅ Colaborador **{n}** cadastrado!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios (*).")

    with t2:
        df_edit = pd.DataFrame(
            supabase.table("oficiais").select("*").not_.eq("matricula", "URL_SISTEMA").execute().data
        )
        if not df_edit.empty:
            st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        else:
            st.info("Nenhum colaborador cadastrado.")


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "⚙️ Configurações":
    st.markdown("### ⚙️ Configurações do Sistema")

    st.markdown("#### 🔗 URL Oficial do App")
    st.caption("Cole aqui o endereço do seu app no Streamlit Cloud para que os links de confirmação funcionem corretamente.")
    url_input = st.text_input("URL do App", value=url_base, placeholder="https://seu-app.streamlit.app")

    if st.button("💾 Salvar URL Oficial"):
        supabase.table("oficiais").upsert({"matricula": "URL_SISTEMA", "whatsapp": url_input}).execute()
        st.success("✅ URL salva com sucesso!")

    st.markdown("---")
    st.markdown("#### ℹ️ Sobre o Sistema")
    st.info(
        "**SESMT HUC Digital** — Sistema de Gestão de EPI\n\n"
        "Desenvolvido para o Hospital Universitário do Ceará / ISGH.\n\n"
        "Conforme **NR-06**, item 6.5.1, alínea d — registro eletrônico de fornecimento de EPI."
    )
