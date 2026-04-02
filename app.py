"""Interface de chat Streamlit para o Agente de Perguntas de Negócio."""

import streamlit as st
from agent import run_agent
from charts import extract_chart_data, remove_chart_block, create_chart
from memory import load_memory, save_memory

# --- Page config ---
st.set_page_config(
    page_title="Agente BI Seazone",
    page_icon="📊",
    layout="centered",
)

# --- Dark mode: usa a key do toggle diretamente ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- Sidebar (renderiza primeiro para capturar o toggle) ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0 1rem;">
        <span style="font-size: 2.2rem;">📊</span>
        <h3 id="sidebar-title" style="margin: 0.3rem 0 0; font-weight: 700;">
            Agente BI Seazone
        </h3>
        <span style="font-size: 0.8rem; opacity: 0.6;">
            Powered by Nekt Data Lakehouse
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    dark = st.toggle("🌙 Modo escuro", key="dark_mode")

    st.divider()

    if st.button("🗑️  Nova conversa", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.divider()

    st.markdown("##### O que posso fazer")
    st.caption(
        "🔍 Consultar KPIs de qualquer setor\n\n"
        "📈 Gerar gráficos automaticamente\n\n"
        "🏠 Dados de imóveis, reservas, churn\n\n"
        "👥 Métricas de People e Financeiro\n\n"
        "📊 Comparar períodos e tendências"
    )

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
            if st.button("🗑️ Limpar memória", use_container_width=True):
                save_memory([])
                st.rerun()
        else:
            st.caption("Nenhum aprendizado registrado ainda.")

    st.caption("v1.0 · Dados atualizados diariamente")

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

    /* === Chat input — container, textarea, botão, tudo === */
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
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

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
    <div style="text-align: center; padding: 3rem 1rem 1rem;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
        <h2 style="color: {T["heading"]}; margin-bottom: 0.25rem;">Agente BI Seazone</h2>
        <p style="color: {T["text_secondary"]}; font-size: 1.05rem;">
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
                status.update(label="Consultando dados do Nekt...", state="running")
                response_text, new_session_id = run_agent(
                    prompt, st.session_state.session_id
                )
                st.session_state.session_id = new_session_id

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
                st.rerun()

            except Exception as e:
                status.update(label="Erro na consulta", state="error", expanded=False)
                st.error(
                    f"😕 Não consegui processar sua pergunta. "
                    f"Tente reformular ou pergunte de outra forma.\n\n"
                    f"Detalhe técnico: `{e}`"
                )
