"""Cliente HTTP para o Nekt MCP Server (Streamable HTTP transport)."""

import json
import httpx

_NEKT_URL = "https://nekt-mcp.seazone.com.br/mcp"
_NEKT_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJuZWt0LW1jcC1zZXJ2ZXIiLCJpc3MiOiJodHRwczovL3d3dy5uZWt0LmNvbSIs"
    "ImlhdCI6MTc3NDg4ODA3OSwiZXhwIjoxODA1OTkyMDc5LCJhdWQiOiJuZWt0LW1jcC1zZXJ2"
    "ZXIiLCJzY29wZSI6InJlYWQgd3JpdGUifQ."
    "S9jYa_56UGioe-aq8H1WK8F1GIG1uD-nbU2kKDmTNZbMgNk_WII5cy9QSnb-TJpsJvDS0tWR"
    "z7c6J6HrnB7sQqnwEVB2KkLXImaz8kkjydhRpxQicd6_MQUD45wB2lBfNGJDBKe1SLCVlcbO"
    "EgioU0kqyhGfx6FG4xsjhVqGfV_yordkp46P-MEjjW2JytsDqkW4jcVMulVstgZYmy8KvgUY"
    "NZ_wZgW-7SKbQ_Q5FjKOTpNAiQzR_qIzk3IlRsSGc9QZ_ZdvRia6PIVPlg49AcveKz2DpYK6"
    "RGq2tJCqyhUPZdmARfbm7KnIuUE464q3j3uUMoV8Ii3svCWU7lDSNQ"
)

_BASE_HEADERS = {
    "Authorization": f"Bearer {_NEKT_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

_client = httpx.Client(timeout=120)
_session_id: str | None = None
_request_id = 0


def _next_id() -> int:
    global _request_id
    _request_id += 1
    return _request_id


def _parse_sse(text: str) -> dict | None:
    """Extrai o JSON-RPC result de uma resposta SSE."""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                if "result" in data:
                    return data["result"]
                if "error" in data:
                    raise RuntimeError(f"MCP error: {data['error']}")
            except json.JSONDecodeError:
                continue
    return None


def _post(payload: dict) -> dict:
    """Envia JSON-RPC ao MCP server, lidando com SSE e session ID."""
    global _session_id

    headers = dict(_BASE_HEADERS)
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id

    resp = _client.post(_NEKT_URL, json=payload, headers=headers)
    resp.raise_for_status()

    # Captura session ID do header
    sid = resp.headers.get("mcp-session-id")
    if sid:
        _session_id = sid

    # Parse: pode ser SSE (text/event-stream) ou JSON direto
    ct = resp.headers.get("content-type", "")
    if "text/event-stream" in ct:
        result = _parse_sse(resp.text)
        if result is not None:
            return result
        raise RuntimeError(f"Sem result na resposta SSE: {resp.text[:300]}")
    else:
        data = resp.json()
        if "result" in data:
            return data["result"]
        raise RuntimeError(f"Resposta inesperada: {resp.text[:300]}")


def _ensure_initialized():
    """Faz o handshake MCP se ainda não foi feito."""
    global _session_id
    if _session_id:
        return

    _post({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "nekt-agent", "version": "1.0"},
        },
        "id": _next_id(),
    })

    # Envia notifications/initialized (obrigatório pelo protocolo)
    headers = dict(_BASE_HEADERS)
    if _session_id:
        headers["Mcp-Session-Id"] = _session_id
    _client.post(_NEKT_URL, json={
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }, headers=headers)


def call_tool(tool_name: str, arguments: dict) -> str:
    """Chama uma tool do Nekt MCP e retorna o resultado como texto."""
    _ensure_initialized()

    result = _post({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
        "id": _next_id(),
    })

    # MCP retorna content como lista de blocos
    content = result.get("content", [])
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block["text"])
        else:
            parts.append(json.dumps(block, ensure_ascii=False))

    return "\n".join(parts) if parts else json.dumps(result, ensure_ascii=False)
