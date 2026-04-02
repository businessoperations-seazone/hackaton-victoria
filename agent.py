"""Agente de BI usando Claude Code CLI como backend."""

import subprocess
import json
import os
import re
from prompts import build_system_prompt
from memory import load_memory, save_memory, add_entry

_MCP_CONFIG_PATH = "/tmp/nekt-mcp-config.json"


def _extract_memory_facts(text: str) -> list[str]:
    """Extrai fatos do bloco [MEMORY] na resposta."""
    match = re.search(r"\[MEMORY\]\s*(.*?)\s*\[/MEMORY\]", text, re.DOTALL)
    if not match:
        return []
    lines = match.group(1).strip().split("\n")
    facts = []
    for line in lines:
        line = line.strip().lstrip("- ").strip()
        if line:
            facts.append(line)
    return facts


def _remove_memory_block(text: str) -> str:
    """Remove o bloco [MEMORY] do texto visível."""
    return re.sub(r"\[MEMORY\].*?\[/MEMORY\]", "", text, flags=re.DOTALL).strip()


def _ensure_mcp_config():
    """Cria o arquivo de config MCP se não existir."""
    if os.path.exists(_MCP_CONFIG_PATH):
        return
    claude_json = os.path.expanduser("~/.claude.json")
    with open(claude_json) as f:
        data = json.load(f)
    nekt = data["projects"]["/home/victoria"]["mcpServers"]["Nekt"]
    config = {"mcpServers": {"Nekt": nekt}}
    with open(_MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f)


def run_agent(user_message: str, session_id: str | None = None) -> tuple[str, str]:
    """
    Executa uma pergunta via Claude Code CLI.

    Na primeira mensagem, cria sessão nova com system prompt + memória.
    Nas seguintes, retoma a sessão com --resume.

    Returns:
        (resposta_texto, session_id)
    """
    _ensure_mcp_config()

    cmd = [
        "claude",
        "-p", user_message,
        "--output-format", "json",
        "--model", "sonnet",
        "--mcp-config", _MCP_CONFIG_PATH,
        "--permission-mode", "bypassPermissions",
        "--allowedTools",
        "mcp__Nekt__execute_sql",
        "mcp__Nekt__get_relevant_tables_ddl",
        "mcp__Nekt__get_table_preview",
    ]

    if session_id:
        cmd.extend(["--resume", session_id])
    else:
        system_prompt = build_system_prompt()
        cmd.extend(["--system-prompt", system_prompt])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or "Erro desconhecido ao executar o agente."
        raise RuntimeError(f"Erro no Claude CLI: {error_msg}")

    try:
        data = json.loads(result.stdout)
        new_session_id = data.get("session_id", session_id)
        response_text = data.get("result", result.stdout)
    except json.JSONDecodeError:
        response_text = result.stdout
        new_session_id = session_id

    # Extrair e salvar fatos de memória
    facts = _extract_memory_facts(response_text)
    if facts:
        entries = load_memory()
        for fact in facts:
            entries = add_entry(entries, fact, source="agent")
        save_memory(entries)

    # Limpar bloco de memória do texto visível
    clean_response = _remove_memory_block(response_text)

    return clean_response, new_session_id
