"""Sistema de memória persistente entre conversas do agente."""

from datetime import datetime, timedelta

import storage

STORE_KEY = "memory"
MAX_ENTRIES = 50
MAX_AGE_DAYS = 30


def load_memory() -> list[dict]:
    """Carrega entradas de memória."""
    entries = storage.load(STORE_KEY, default=[])
    return _prune(entries)


def save_memory(entries: list[dict]) -> None:
    """Salva entradas de memória."""
    entries = _prune(entries)
    storage.save(STORE_KEY, entries)


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
