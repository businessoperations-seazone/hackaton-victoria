"""Interface de chat Streamlit para o Nektar - Agente de Negócio Seazone."""

import os
import base64
import streamlit as st
from dotenv import load_dotenv
from agent import run_agent
from charts import extract_chart_data, remove_chart_block, create_chart
from memory import load_memory, save_memory
from chat_history import (
    save_conversation, load_conversation, list_conversations,
    delete_conversation, new_conversation_id,
)
from auth import login, register, validate_email

# --- Logo em base64 para uso inline ---
_LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
with open(_LOGO_PATH, "rb") as _f:
    _LOGO_B64 = base64.b64encode(_f.read()).decode()

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Page config ---
st.set_page_config(
    page_title="Nektar - Agente de Negócio Seazone",
    page_icon=_LOGO_PATH,
    layout="centered",
)

# --- State defaults ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

dark = st.session_state.dark_mode
_disabled = st.session_state.is_processing

# --- Tokens de cor por tema ---
if dark:
    T = {
        "bg": "#111827",
        "bg_secondary": "#1E293B",
        "sidebar_top": "#1E293B",
        "sidebar_bottom": "#162032",
        "text": "#F1F5F9",
        "text_secondary": "#94A3B8",
        "heading": "#E8EFFE",
        "accent": "#4D8BFF",
        "border": "#334155",
        "btn_bg": "#1E293B",
        "btn_border": "#334155",
        "chart_border": "#334155",
    }
else:
    T = {
        "bg": "#FFFFFF",
        "bg_secondary": "#E8EFFE",
        "sidebar_top": "#E8EFFE",
        "sidebar_bottom": "#FFFFFF",
        "text": "#2E2E2E",
        "text_secondary": "#7C7C7C",
        "heading": "#00143D",
        "accent": "#0055FF",
        "border": "#E8EFFE",
        "btn_bg": "#FFF6F5",
        "btn_border": "#E8EFFE",
        "chart_border": "#E8EFFE",
    }

# --- Custom CSS ---
st.markdown(f"""
<style>
    /* === Sidebar history buttons === */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {{
        font-size: 0.78rem !important;
        padding: 0.35rem 0.5rem !important;
        border-radius: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* === Nektar sidebar header === */
    #nektar-sidebar-header {{
        text-align: center !important;
        padding: 0.5rem 0 1rem;
    }}
    #nektar-sidebar-header img {{
        width: 60px;
        height: 60px;
        object-fit: contain;
        margin: 0 auto;
        display: block;
    }}
    #nektar-sidebar-header h3 {{
        margin: 0.3rem 0 0;
        font-weight: 700;
        text-align: center !important;
    }}
    #nektar-sidebar-header span {{
        font-size: 0.8rem;
        opacity: 0.6;
        text-align: center !important;
        display: block;
    }}

    /* === Nektar welcome/login screen === */
    #nektar-welcome, #nektar-login-header {{
        text-align: center !important;
        padding: 3rem 1rem 1rem;
    }}
    #nektar-welcome img, #nektar-login-header img {{
        width: 80px;
        height: 80px;
        object-fit: contain;
        margin: 0 auto 0.5rem;
        display: block;
    }}
    #nektar-welcome h2, #nektar-login-header h2 {{
        margin-bottom: 0.25rem;
        text-align: center !important;
    }}
    #nektar-welcome p, #nektar-login-header p {{
        font-size: 1.05rem;
        text-align: center !important;
    }}

    /* === Base === */
    .stApp, .main .block-container {{
        background-color: {T["bg"]};
        color: {T["text"]};
    }}

    /* === Sidebar === */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {T["sidebar_top"]} 0%, {T["sidebar_bottom"]} 100%);
        border-right: 1px solid {T["border"]};
    }}
    [data-testid="stSidebar"] * {{
        color: {T["text"]} !important;
    }}
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{
        color: {T["text_secondary"]} !important;
    }}

    /* === Chat messages === */
    [data-testid="stChatMessage"] {{
        border-radius: 12px;
        padding: 0.75rem 1rem;
        background-color: {T["bg"]} !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] td,
    [data-testid="stChatMessage"] th,
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3 {{
        color: {T["text"]} !important;
    }}

    /* === Suggestion buttons === */
    .stButton > button {{
        border: 1px solid {T["btn_border"]};
        border-radius: 10px;
        background-color: {T["btn_bg"]} !important;
        color: {T["text"]} !important;
        font-size: 0.85rem;
        text-align: left;
        padding: 0.6rem 0.8rem;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        background-color: {T["bg_secondary"]} !important;
        border-color: {T["accent"]} !important;
        color: {T["accent"]} !important;
    }}

    /* === Chat input === */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div,
    [data-testid="stChatInput"] form,
    [data-testid="stChatInput"] form > div {{
        background-color: {T["bg"]} !important;
        border-color: {T["border"]} !important;
    }}
    [data-testid="stChatInput"] textarea {{
        border-radius: 12px;
        background-color: {T["bg_secondary"]} !important;
        color: {T["text"]} !important;
        border-color: {T["border"]} !important;
    }}
    [data-testid="stChatInput"] button {{
        background-color: {T["bg_secondary"]} !important;
        color: {T["accent"]} !important;
        border-color: {T["border"]} !important;
    }}

    /* === Status widget === */
    [data-testid="stStatusWidget"] {{
        background-color: {T["bg_secondary"]} !important;
        border-color: {T["border"]} !important;
    }}
    [data-testid="stStatusWidget"] * {{
        color: {T["text"]} !important;
    }}

    /* === Expander === */
    [data-testid="stExpander"] {{
        border-color: {T["border"]} !important;
        background-color: {T["bg_secondary"]} !important;
    }}
    [data-testid="stExpander"] summary {{
        color: {T["text"]} !important;
    }}

    /* === Dividers === */
    hr {{
        border-color: {T["border"]} !important;
    }}

    /* === Charts === */
    [data-testid="stPlotlyChart"] {{
        border: 1px solid {T["chart_border"]};
        border-radius: 12px;
        padding: 0.5rem;
        margin-top: 0.5rem;
    }}

    /* === Toggle === */
    [data-testid="stToggle"] label span {{
        color: {T["text"]} !important;
    }}

    /* === General overrides === */
    footer {{visibility: hidden;}}
    #sidebar-title {{
        color: {T["heading"]};
    }}
    h1 a, h2 a, h3 a, h4 a,
    [data-testid="stMarkdownContainer"] a.header-link,
    .stMarkdown h2 a {{
        display: none !important;
    }}
    .stMarkdown, .stMarkdown p {{
        color: {T["text"]};
    }}

    /* === Tables in chat === */
    table {{
        color: {T["text"]} !important;
    }}
    th {{
        background-color: {T["bg_secondary"]} !important;
        color: {T["text"]} !important;
    }}
    td {{
        border-color: {T["border"]} !important;
    }}

    /* === Header / toolbar / top bar === */
    header, header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    .stApp > header {{
        background-color: {T["bg"]} !important;
        border-bottom: 1px solid {T["border"]};
    }}

    /* === Nuclear: qualquer fundo branco restante === */
    .stApp .main,
    .stApp .main > div,
    .stApp .main .block-container,
    .stApp [data-testid="stBottom"],
    .stApp [data-testid="stBottom"] > div,
    .stApp [data-testid="stBottomBlockContainer"],
    .stApp [data-testid="stBottomBlockContainer"] > div,
    .stApp section[data-testid="stMain"],
    .stApp section[data-testid="stMain"] > div {{
        background-color: {T["bg"]} !important;
    }}

    /* === Login form submit button === */
    [data-testid="stForm"] .stButton > button,
    [data-testid="stFormSubmitButton"] > button {{
        background-color: {T["accent"]} !important;
        color: white !important;
        border: none !important;
        font-weight: 600;
    }}
    [data-testid="stForm"] .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {{
        background-color: {"#3A6FCC" if dark else "#0044CC"} !important;
        color: white !important;
        border: none !important;
    }}

    /* === Login form inputs === */
    .stTextInput input {{
        background-color: {T["bg_secondary"]} !important;
        color: {T["text"]} !important;
        border-color: {T["border"]} !important;
        border-radius: 10px;
    }}
    .stTextInput label {{
        color: {T["text"]} !important;
    }}

    /* === Tabs === */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {T["bg_secondary"]} !important;
        color: {T["text"]} !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {T["accent"]} !important;
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# TELA DE LOGIN
# ============================================================
def show_login_page():
    """Renderiza a tela de login/cadastro."""
    st.markdown(f"""
    <div id="nektar-login-header">
        <img src="data:image/png;base64,{_LOGO_B64}" />
        <h2 style="color: {T["heading"]};">Nektar</h2>
        <p style="color: {T["text_secondary"]}; font-size: 0.95rem;">
            Agente de Negócio Seazone
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Container centralizado para o form
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown(
            f"<p style='text-align:center; color:{T['text_secondary']}; "
            f"font-size:0.8rem; margin-bottom:0.5rem;'>"
            "Acesso exclusivo para colaboradores <b>@seazone.com.br</b></p>",
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["Entrar", "Cadastrar"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input(
                    "Email", placeholder="seu.nome@seazone.com.br"
                )
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button(
                    "Entrar", use_container_width=True
                )

                if submitted:
                    success, msg, name = login(email, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        st.session_state.user_name = name
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_register:
            with st.form("register_form"):
                reg_name = st.text_input("Nome completo")
                reg_email = st.text_input(
                    "Email corporativo",
                    placeholder="seu.nome@seazone.com.br",
                )
                reg_password = st.text_input(
                    "Senha (min. 6 caracteres)", type="password", key="reg_pw"
                )
                reg_password2 = st.text_input(
                    "Confirmar senha", type="password", key="reg_pw2"
                )
                reg_submitted = st.form_submit_button(
                    "Cadastrar", use_container_width=True
                )

                if reg_submitted:
                    if reg_password != reg_password2:
                        st.error("As senhas não coincidem.")
                    else:
                        success, msg = register(reg_email, reg_name, reg_password)
                        if success:
                            st.success(
                                "Cadastro realizado! Volte na aba Entrar."
                            )
                        else:
                            st.error(msg)


# ============================================================
# VERIFICAÇÃO DE AUTENTICAÇÃO
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login_page()
    st.stop()


# ============================================================
# APP PRINCIPAL (só aparece após login)
# ============================================================

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"""
    <div id="nektar-sidebar-header">
        <img src="data:image/png;base64,{_LOGO_B64}" />
        <h3 id="sidebar-title">Nektar</h3>
        <span>Agente de Negócio Seazone</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    _user = st.session_state.get("user_email", "")

    if st.button("➕  Nova conversa", use_container_width=True, type="secondary", disabled=_disabled):
        if st.session_state.messages:
            save_conversation(st.session_state.conv_id, st.session_state.messages, _user)
        st.session_state.messages = []
        st.session_state.conv_id = new_conversation_id()
        st.rerun()

    st.divider()

    # --- Histórico de conversas ---
    st.markdown("##### Conversas anteriores")
    conversations = list_conversations(_user)
    if conversations:
        for conv in conversations:
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(
                    f"💬 {conv['title']}",
                    key=f"conv_{conv['id']}",
                    use_container_width=True,
                    disabled=_disabled,
                ):
                    if st.session_state.messages:
                        save_conversation(
                            st.session_state.conv_id, st.session_state.messages, _user
                        )
                    st.session_state.messages = load_conversation(conv["id"], _user)
                    st.session_state.conv_id = conv["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}",  disabled=_disabled):
                    delete_conversation(conv["id"], _user)
                    if st.session_state.conv_id == conv["id"]:
                        st.session_state.messages = []
                        st.session_state.conv_id = new_conversation_id()
                    st.rerun()
    else:
        st.caption("Nenhuma conversa salva ainda.")

    st.divider()

    with st.expander("💡 Dicas de uso"):
        st.markdown("""
- Seja **específico com datas**: "em março de 2026"
- Peça **comparações**: "compare janeiro e fevereiro"
- Mencione o **setor**: "KPIs de Marketing"
- Para **gráficos**, peça dados com 3+ itens
""")

    with st.expander("🧠 Memória do agente"):
        mem = load_memory()
        if mem:
            for e in mem:
                st.caption(f"[{e['date']}] {e['fact']}")
            if st.button("🗑️ Limpar memória", use_container_width=True, disabled=_disabled):
                save_memory([])
                st.rerun()
        else:
            st.caption("Nenhum aprendizado registrado ainda.")

    # --- Indicador de custo da sessão ---
    session_cost = st.session_state.get("session_cost", 0.0)
    if session_cost > 0:
        st.caption(f"Custo da sessão: **${session_cost:.4f}**")

    st.caption("Nektar v1.0 · Dados atualizados diariamente")

    def _on_dark_toggle():
        st.session_state.dark_mode = not st.session_state.dark_mode

    st.toggle(
        "🌙 Modo escuro",
        value=st.session_state.dark_mode,
        key="_dark_toggle",
        on_change=_on_dark_toggle,
        disabled=_disabled,
    )

    st.divider()

    if st.button("🚪 Sair", use_container_width=True, disabled=_disabled):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.messages = []
        st.rerun()

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = new_conversation_id()

SUGGESTIONS = [
    "Qual o valor do churn de imóveis este mês?",
    "Quantos imóveis ativos temos?",
    "Compare o faturamento de Fevereiro e Março",
    "Como está o turnover de colaboradores?",
    "Quantas reservas tivemos no último mês?",
    "Quais KPIs do setor de Marketing estão ativos?",
]

# --- Welcome screen ---
if not st.session_state.messages:
    st.markdown(f"""
    <div id="nektar-welcome">
        <img src="data:image/png;base64,{_LOGO_B64}" />
        <h2 style="color: {T["heading"]};">Olá, {st.session_state.get('user_name', '').split()[0]}</h2>
        <p style="color: {T["text_secondary"]};">
            Pergunte qualquer coisa sobre os dados da Seazone em linguagem natural.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<p style='text-align:center; color:{T['text_secondary']}; font-size:0.9rem; margin-top:1.5rem;'>"
        "Experimente uma destas perguntas:</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(
                f"💬  {suggestion}",
                key=f"suggestion_{i}",
                use_container_width=True,
            ):
                st.session_state["_pending_prompt"] = suggestion
                st.rerun()

# --- Chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart_data"):
            fig = create_chart(msg["chart_data"], dark_mode=dark)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

# --- User input ---
pending = st.session_state.pop("_pending_prompt", None)
prompt = pending or st.chat_input("Faça uma pergunta sobre os dados da Seazone...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Analisando sua pergunta...", expanded=True) as status:
            try:
                st.session_state.is_processing = True

                def on_status(label):
                    status.update(label=label, state="running")

                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]

                response_text, cost = run_agent(
                    prompt,
                    history=history,
                    on_status=on_status,
                )
                st.session_state.session_cost = st.session_state.get("session_cost", 0.0) + cost
                st.session_state.is_processing = False

                status.update(label="Processando resposta...", state="running")
                chart_data = extract_chart_data(response_text)
                clean_text = remove_chart_block(response_text)

                status.update(label="Concluído!", state="complete", expanded=False)

                st.markdown(clean_text)
                if chart_data:
                    fig = create_chart(chart_data, dark_mode=dark)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": clean_text,
                    "chart_data": chart_data,
                })
                save_conversation(
                    st.session_state.conv_id,
                    st.session_state.messages,
                    st.session_state.get("user_email", ""),
                )
                st.rerun()

            except Exception as e:
                st.session_state.is_processing = False
                status.update(label="Erro na consulta", state="error", expanded=False)
                st.error(
                    f"Não consegui processar sua pergunta. "
                    f"Tente reformular ou pergunte de outra forma.\n\n"
                    f"Detalhe técnico: `{e}`"
                )
