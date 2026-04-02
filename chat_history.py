"""Persistência de histórico de conversas por usuário."""

import json
import os
import uuid
from datetime import datetime

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "chat_history.json")
MAX_CONVERSATIONS_PER_USER = 30


def _load_all() -> list[dict]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []


def _save_all(conversations: list[dict]) -> None:
    with open(HISTORY_PATH, "w") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)


def save_conversation(conv_id: str, messages: list[dict], user_email: str = "") -> None:
    """Salva ou atualiza uma conversa no histórico."""
    if not messages:
        return

    conversations = _load_all()

    first_question = next(
        (m["content"] for m in messages if m["role"] == "user"), "Conversa"
    )
    title = first_question[:60] + ("..." if len(first_question) > 60 else "")

    for conv in conversations:
        if conv["id"] == conv_id:
            conv["title"] = title
            conv["messages"] = messages
            conv["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if user_email:
                conv["user_email"] = user_email
            _save_all(conversations)
            return

    conversations.append({
        "id": conv_id,
        "title": title,
        "messages": messages,
        "user_email": user_email,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

    # Limitar por usuário
    if user_email:
        user_convs = [c for c in conversations if c.get("user_email") == user_email]
        if len(user_convs) > MAX_CONVERSATIONS_PER_USER:
            oldest_ids = {c["id"] for c in user_convs[:-MAX_CONVERSATIONS_PER_USER]}
            conversations = [c for c in conversations if c["id"] not in oldest_ids]

    _save_all(conversations)


def load_conversation(conv_id: str, user_email: str = "") -> list[dict]:
    """Carrega mensagens de uma conversa pelo ID (verifica dono)."""
    for conv in _load_all():
        if conv["id"] == conv_id:
            if user_email and conv.get("user_email", "") != user_email:
                return []
            return conv["messages"]
    return []


def list_conversations(user_email: str = "") -> list[dict]:
    """Lista conversas do usuário (mais recente primeiro)."""
    conversations = _load_all()
    if user_email:
        conversations = [c for c in conversations if c.get("user_email") == user_email]
    return [
        {"id": c["id"], "title": c["title"], "updated_at": c["updated_at"]}
        for c in reversed(conversations)
    ]


def delete_conversation(conv_id: str, user_email: str = "") -> None:
    """Remove uma conversa (verifica dono)."""
    conversations = _load_all()
    conversations = [
        c for c in conversations
        if not (c["id"] == conv_id and (not user_email or c.get("user_email") == user_email))
    ]
    _save_all(conversations)


def new_conversation_id() -> str:
    return uuid.uuid4().hex[:12]
