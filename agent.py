"""Agente de BI usando OpenRouter (OpenAI SDK) como backend."""

import json
import os
import re
from openai import OpenAI
from prompts import build_system_prompt
from memory import load_memory, save_memory, add_entry
from nekt_client import call_tool

# --- Config ---
_MODEL = os.getenv("BI_AGENT_MODEL", "anthropic/claude-sonnet-4")
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY não configurada. "
                "Defina a variável de ambiente ou crie um arquivo .env"
            )
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client

# --- Tools disponíveis para o modelo ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": (
                "Executa uma query SQL no Nekt Data Lakehouse e retorna os resultados. "
                "Use para consultar tabelas Gold, Silver e Trusted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "Query SQL para executar no lakehouse",
                    }
                },
                "required": ["sql_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relevant_tables_ddl",
            "description": (
                "Busca tabelas relevantes no lakehouse a partir de uma pergunta. "
                "Retorna os DDLs (schemas) das tabelas encontradas. "
                "Use para descobrir tabelas quando não conhece o schema."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Pergunta ou palavras-chave para buscar tabelas relevantes (ex: 'reservas', 'churn imóveis')",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_preview",
            "description": (
                "Retorna uma prévia (primeiras linhas) de uma tabela do lakehouse. "
                "Use para verificar formato dos dados antes de montar a query final."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nome completo da tabela (ex: 'nekt_gold.kpis_diretoria_pivotada_2')",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
]

# Mapeamento tool name → nome real no MCP (caso difira)
_TOOL_MAP = {
    "execute_sql": "execute_sql",
    "get_relevant_tables_ddl": "get_relevant_tables_ddl",
    "get_table_preview": "get_table_preview",
}

MAX_TOOL_ROUNDS = 10


def _extract_memory_facts(text: str) -> list[str]:
    """Extrai fatos do bloco [MEMORY] na resposta."""
    match = re.search(r"\[MEMORY\]\s*(.*?)\s*\[/MEMORY\]", text, re.DOTALL)
    if not match:
        return []
    lines = match.group(1).strip().split("\n")
    return [line.strip().lstrip("- ").strip() for line in lines if line.strip()]


def _remove_memory_block(text: str) -> str:
    """Remove o bloco [MEMORY] do texto visível."""
    return re.sub(r"\[MEMORY\].*?\[/MEMORY\]", "", text, flags=re.DOTALL).strip()


_KPI_TABLE_PATTERN = re.compile(r"(?i)\b\w*kpis?\w*\b")


def _add_kpi_warning(name: str, result: str) -> str:
    """Adiciona aviso se get_relevant_tables_ddl retornou tabelas de KPI."""
    if name != "get_relevant_tables_ddl":
        return result
    kpi_tables = _KPI_TABLE_PATTERN.findall(result)
    if kpi_tables:
        return (
            result
            + "\n\n⚠️ ATENÇÃO: Os resultados acima incluem tabelas de KPI "
            f"({', '.join(set(kpi_tables))}). "
            "NÃO use essas tabelas. Escolha apenas tabelas de domínio específico "
            "(ex: dados_churn, deals_pipedrive, etc). "
            "Se só apareceram tabelas de KPI, refaça a busca com palavras-chave "
            "mais específicas do domínio."
        )
    return result


def _execute_tool_call(name: str, arguments: dict) -> str:
    """Executa uma tool call no Nekt MCP."""
    mcp_name = _TOOL_MAP.get(name, name)
    try:
        result = call_tool(mcp_name, arguments)
        return _add_kpi_warning(name, result)
    except Exception as e:
        return f"Erro ao executar {name}: {e}"


def run_agent(
    user_message: str,
    history: list[dict] | None = None,
    on_status: callable = None,
) -> str:
    """
    Executa uma pergunta via OpenRouter API com tool calling.

    Args:
        user_message: Pergunta do usuário.
        history: Histórico de mensagens anteriores [{"role": ..., "content": ...}].
        on_status: Callback opcional para atualizar status (recebe string).

    Returns:
        Texto da resposta final (limpo, sem bloco MEMORY).
    """
    client = _get_client()

    # Monta mensagens
    system_prompt = build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    # Loop de tool calling
    for round_num in range(MAX_TOOL_ROUNDS):
        if on_status:
            if round_num == 0:
                on_status("Analisando sua pergunta...")
            else:
                on_status(f"Consultando dados (etapa {round_num + 1})...")

        response = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            tools=TOOLS,
            max_tokens=2000,
        )

        choice = response.choices[0]

        # Se não há tool calls, temos a resposta final
        if not choice.message.tool_calls:
            break

        # Adiciona a mensagem do assistente com tool calls
        messages.append(choice.message)

        # Executa cada tool call
        for tc in choice.message.tool_calls:
            if on_status:
                tool_label = {
                    "execute_sql": "Executando SQL...",
                    "get_relevant_tables_ddl": "Buscando tabelas relevantes...",
                    "get_table_preview": "Verificando dados...",
                }.get(tc.function.name, f"Executando {tc.function.name}...")
                on_status(tool_label)

            args = json.loads(tc.function.arguments)
            result = _execute_tool_call(tc.function.name, args)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    # Extrai resposta final
    response_text = choice.message.content or ""

    # Salva fatos de memória
    facts = _extract_memory_facts(response_text)
    if facts:
        entries = load_memory()
        for fact in facts:
            entries = add_entry(entries, fact, source="agent")
        save_memory(entries)

    return _remove_memory_block(response_text)
