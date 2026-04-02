"""Persistência de histórico de conversas."""

import json
import os
import uuid
from datetime import datetime

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "chat_history.json")
MAX_CONVERSATIONS = 30


def _load_all() -> list[dict]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []


def _save_all(conversations: list[dict]) -> None:
    # Manter apenas as mais recentes
    conversations = conversations[-MAX_CONVERSATIONS:]
    with open(HISTORY_PATH, "w") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)


def save_conversation(conv_id: str, messages: list[dict]) -> None:
    """Salva ou atualiza uma conversa no histórico."""
    if not messages:
        return

    conversations = _load_all()

    # Título = primeira pergunta do usuário, truncada
    first_question = next(
        (m["content"] for m in messages if m["role"] == "user"), "Conversa"
    )
    title = first_question[:60] + ("..." if len(first_question) > 60 else "")

    # Procura conversa existente pelo ID
    for conv in conversations:
        if conv["id"] == conv_id:
            conv["title"] = title
            conv["messages"] = messages
            conv["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save_all(conversations)
            return

    # Nova conversa
    conversations.append({
        "id": conv_id,
        "title": title,
        "messages": messages,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save_all(conversations)


def load_conversation(conv_id: str) -> list[dict]:
    """Carrega mensagens de uma conversa pelo ID."""
    for conv in _load_all():
        if conv["id"] == conv_id:
            return conv["messages"]
    return []


def list_conversations() -> list[dict]:
    """Lista conversas (mais recente primeiro), retorna id, title, updated_at."""
    conversations = _load_all()
    return [
        {"id": c["id"], "title": c["title"], "updated_at": c["updated_at"]}
        for c in reversed(conversations)
    ]


def delete_conversation(conv_id: str) -> None:
    """Remove uma conversa do histórico."""
    conversations = _load_all()
    conversations = [c for c in conversations if c["id"] != conv_id]
    _save_all(conversations)


def new_conversation_id() -> str:
    return uuid.uuid4().hex[:12]
