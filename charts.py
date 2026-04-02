"""Geração de gráficos Plotly com identidade visual Seazone (light/dark)."""

import json
import re
import plotly.graph_objects as go

# Paleta oficial Seazone
SEAZONE_PALETTE = [
    "#0055FF",  # azul principal
    "#FC6058",  # coral/vermelho
    "#00143D",  # navy escuro
    "#7C7C7C",  # cinza médio
    "#0077CC",  # azul intermediário
    "#E8EFFE",  # azul claro
    "#2E2E2E",  # cinza escuro
    "#FFF6F5",  # rosa claro
]

# Paleta adaptada para dark mode (mais vibrante/clara)
SEAZONE_PALETTE_DARK = [
    "#4D8BFF",  # azul claro vibrante
    "#FC6058",  # coral (mantém)
    "#E8EFFE",  # azul claro
    "#8B949E",  # cinza claro
    "#6EA1FF",  # azul médio
    "#30363D",  # cinza escuro
    "#E6EDF3",  # quase branco
    "#FFF6F5",  # rosa claro
]


def _get_layout(dark_mode: bool = False) -> dict:
    if dark_mode:
        return dict(
            template="plotly_dark",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                size=13,
                color="#E6EDF3",
            ),
            title_font=dict(size=16, color="#E8EFFE"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#30363D"),
            yaxis=dict(gridcolor="#30363D"),
            hoverlabel=dict(
                bgcolor="#161B22",
                font_size=13,
                font_color="#E6EDF3",
                bordercolor="#30363D",
            ),
        )
    else:
        return dict(
            template="plotly_white",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                size=13,
                color="#2E2E2E",
            ),
            title_font=dict(size=16, color="#00143D"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#E8EFFE"),
            yaxis=dict(gridcolor="#E8EFFE"),
            hoverlabel=dict(
                bgcolor="#00143D",
                font_size=13,
                font_color="white",
                bordercolor="#00143D",
            ),
        )


def extract_chart_data(text: str) -> dict | None:
    """Extrai dados de gráfico do bloco [CHART_DATA] na resposta do agente."""
    match = re.search(r"\[CHART_DATA\]\s*(\{.*?\})\s*\[/CHART_DATA\]", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def remove_chart_block(text: str) -> str:
    """Remove o bloco [CHART_DATA] do texto da resposta."""
    return re.sub(r"\[CHART_DATA\].*?\[/CHART_DATA\]", "", text, flags=re.DOTALL).strip()


def create_chart(data: dict, dark_mode: bool = False) -> go.Figure | None:
    """Cria um gráfico Plotly a partir dos dados estruturados."""
    chart_type = data.get("type", "bar")
    title = data.get("title", "")
    x = data.get("x", [])
    y = data.get("y", [])
    x_label = data.get("x_label", "")
    y_label = data.get("y_label", "")

    if not x or not y:
        return None

    palette = SEAZONE_PALETTE_DARK if dark_mode else SEAZONE_PALETTE
    fill_rgba = "rgba(77, 139, 255, 0.12)" if dark_mode else "rgba(0, 85, 255, 0.08)"

    fig = go.Figure()

    if chart_type == "bar":
        fig.add_trace(go.Bar(
            x=x, y=y,
            marker_color=palette[0],
            marker_line=dict(width=0),
            opacity=0.9,
        ))
    elif chart_type == "line":
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines+markers",
            line=dict(color=palette[0], width=2.5),
            marker=dict(size=7, color=palette[0]),
            fill="tozeroy",
            fillcolor=fill_rgba,
        ))
    elif chart_type == "pie":
        fig = go.Figure(data=[go.Pie(
            labels=x,
            values=y,
            marker=dict(colors=palette[:len(x)]),
            hole=0.4,
            textinfo="percent+label",
            textfont_size=12,
        )])
    else:
        fig.add_trace(go.Bar(x=x, y=y, marker_color=palette[0]))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        **_get_layout(dark_mode),
    )

    return fig
