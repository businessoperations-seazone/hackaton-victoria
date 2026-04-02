"""Sistema de memória persistente entre conversas do agente."""

import json
import os
from datetime import datetime, timedelta

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory.json")
MAX_ENTRIES = 50
MAX_AGE_DAYS = 30


def load_memory() -> list[dict]:
    """Carrega entradas de memória do disco."""
    if not os.path.exists(MEMORY_PATH):
        return []
    try:
        with open(MEMORY_PATH) as f:
            entries = json.load(f)
        return _prune(entries)
    except (json.JSONDecodeError, KeyError):
        return []


def save_memory(entries: list[dict]) -> None:
    """Salva entradas de memória no disco."""
    entries = _prune(entries)
    with open(MEMORY_PATH, "w") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_entry(entries: list[dict], fact: str, source: str = "agent") -> list[dict]:
    """Adiciona uma entrada de memória."""
    entry = {
        "fact": fact,
        "source": source,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    entries.append(entry)
    return _prune(entries)


def format_for_prompt(entries: list[dict]) -> str:
    """Formata memória para inclusão no system prompt."""
    if not entries:
        return ""
    lines = ["## Memória de conversas anteriores"]
    for e in entries:
        lines.append(f"- [{e['date']}] {e['fact']}")
    lines.append("")
    lines.append(
        "Use estes fatos como contexto. Se algum estiver desatualizado, "
        "ignore-o e confie nos dados atuais."
    )
    return "\n".join(lines)


def _prune(entries: list[dict]) -> list[dict]:
    """Remove entradas antigas e mantém o limite de tamanho."""
    cutoff = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    entries = [e for e in entries if e.get("date", "") >= cutoff]
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    return entries
