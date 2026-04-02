"""Autenticação simples com email @seazone.com.br + senha."""

import hashlib
import secrets

import storage

STORE_KEY = "users"
ALLOWED_DOMAIN = "seazone.com.br"


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _load_users() -> dict:
    return storage.load(STORE_KEY, default={})


def _save_users(users: dict) -> None:
    storage.save(STORE_KEY, users)


def validate_email(email: str) -> tuple[bool, str]:
    """Valida se o email é do domínio permitido."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Email inválido."
    domain = email.split("@")[1]
    if domain != ALLOWED_DOMAIN:
        return False, f"Apenas emails @{ALLOWED_DOMAIN} são permitidos."
    return True, ""


def register(email: str, name: str, password: str) -> tuple[bool, str]:
    """Registra um novo usuário."""
    email = email.strip().lower()
    name = name.strip()

    valid, msg = validate_email(email)
    if not valid:
        return False, msg

    if not name:
        return False, "Nome é obrigatório."

    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."

    users = _load_users()
    if email in users:
        return False, "Este email já está cadastrado."

    salt = secrets.token_hex(16)
    users[email] = {
        "name": name,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return True, ""


def login(email: str, password: str) -> tuple[bool, str, str]:
    """Autentica um usuário. Retorna (sucesso, mensagem_erro, nome)."""
    email = email.strip().lower()
    users = _load_users()

    if email not in users:
        return False, "Email ou senha incorretos.", ""

    user = users[email]
    hashed = _hash_password(password, user["salt"])
    if hashed != user["password_hash"]:
        return False, "Email ou senha incorretos.", ""

    return True, "", user["name"]
