"""Persistência e refresh de painéis do dashboard por usuário."""

import json
import uuid
from datetime import datetime
from nekt_client import call_tool

import storage

STORE_KEY = "dashboards"
MAX_PANELS_PER_USER = 20


def _load_all() -> list[dict]:
    return storage.load(STORE_KEY, default=[])


def _save_all(panels: list[dict]) -> None:
    storage.save(STORE_KEY, panels)


def new_panel_id() -> str:
    return uuid.uuid4().hex[:12]


def save_panel(panel: dict) -> None:
    """Salva um novo painel."""
    panels = _load_all()

    # Verifica se já existe (update)
    for i, p in enumerate(panels):
        if p["id"] == panel["id"]:
            panels[i] = panel
            _save_all(panels)
            return

    panels.append(panel)

    # Limitar por usuário
    user_email = panel.get("user_email", "")
    if user_email:
        user_panels = [p for p in panels if p.get("user_email") == user_email]
        if len(user_panels) > MAX_PANELS_PER_USER:
            oldest_ids = {p["id"] for p in user_panels[:-MAX_PANELS_PER_USER]}
            panels = [p for p in panels if p["id"] not in oldest_ids]

    _save_all(panels)


def list_panels(user_email: str) -> list[dict]:
    """Lista painéis do usuário."""
    panels = _load_all()
    return [p for p in panels if p.get("user_email") == user_email]


def delete_panel(panel_id: str, user_email: str) -> None:
    """Remove um painel (verifica dono)."""
    panels = _load_all()
    panels = [
        p for p in panels
        if not (p["id"] == panel_id and p.get("user_email") == user_email)
    ]
    _save_all(panels)


def _parse_sql_result(result_text: str, chart_data: dict) -> dict | None:
    """Parseia resultado do MCP execute_sql e reconstrói chart_data."""
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        return None

    columns = result.get("columns", [])
    data = result.get("data", [])

    if not columns or not data or len(columns) < 2:
        return None

    # Primeira coluna = labels (x), segunda coluna = valores (y)
    x = [str(row[0]) for row in data]
    y = []
    for row in data:
        val = row[1]
        try:
            y.append(float(str(val).replace(",", "").replace(".", "", str(val).count(".") - 1)))
        except (ValueError, TypeError):
            try:
                y.append(float(val))
            except (ValueError, TypeError):
                y.append(0)

    if not x or not y:
        return None

    # Manter tipo, título e labels originais
    return {
        "type": chart_data.get("type", "bar"),
        "title": chart_data.get("title", ""),
        "x": x,
        "y": y,
        "x_label": chart_data.get("x_label", ""),
        "y_label": chart_data.get("y_label", ""),
    }


def refresh_panel(panel_id: str, user_email: str) -> tuple[bool, str]:
    """
    Re-executa o SQL do painel e atualiza os dados.

    Returns:
        (sucesso, mensagem_de_erro)
    """
    panels = _load_all()
    panel = None
    panel_idx = None
    for i, p in enumerate(panels):
        if p["id"] == panel_id and p.get("user_email") == user_email:
            panel = p
            panel_idx = i
            break

    if panel is None:
        return False, "Painel não encontrado."

    sql = panel.get("sql_query")
    if not sql:
        return False, "Painel sem query SQL salva."

    try:
        result_text = call_tool("execute_sql", {"sql_query": sql})
    except Exception as e:
        return False, f"Erro ao executar SQL: {e}"

    new_chart = _parse_sql_result(result_text, panel.get("chart_data", {}))
    if new_chart is None:
        return False, "Não foi possível interpretar os dados retornados."

    panel["chart_data"] = new_chart
    panel["last_refreshed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    panels[panel_idx] = panel
    _save_all(panels)

    return True, ""
