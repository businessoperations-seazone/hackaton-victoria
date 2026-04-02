"""Persistência de dados JSON via PostgreSQL (DATABASE_URL) ou arquivos locais.

Se DATABASE_URL estiver definida, usa PostgreSQL. Caso contrário, fallback
para arquivos JSON no disco (útil para desenvolvimento local).
"""

import json
import os


def _db_url() -> str:
    return os.environ.get("DATABASE_URL", "")


# ---------------------------------------------------------------------------
# PostgreSQL backend
# ---------------------------------------------------------------------------
_initialized = False


def _connect():
    import psycopg
    return psycopg.connect(_db_url())


def _ensure_table():
    global _initialized
    if _initialized:
        return
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS json_store (
                key TEXT PRIMARY KEY,
                data JSONB NOT NULL DEFAULT '[]'::jsonb
            )
        """)
        conn.commit()
    _initialized = True


def _pg_load(key: str, default=None):
    _ensure_table()
    with _connect() as conn:
        row = conn.execute(
            "SELECT data FROM json_store WHERE key = %s", (key,)
        ).fetchone()
    if row is None:
        return default if default is not None else []
    return row[0]


def _pg_save(key: str, data) -> None:
    _ensure_table()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO json_store (key, data) VALUES (%s, %s::jsonb)
               ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data""",
            (key, json.dumps(data, ensure_ascii=False)),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Arquivo local (fallback)
# ---------------------------------------------------------------------------
def _file_load(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return default if default is not None else []


def _file_save(path: str, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------
def use_db() -> bool:
    return bool(_db_url())


def load(key: str, file_path: str = "", default=None):
    """Carrega dados por chave (PG) ou caminho de arquivo (local)."""
    if use_db():
        return _pg_load(key, default)
    return _file_load(file_path or key, default)


def save(key: str, data, file_path: str = "") -> None:
    """Salva dados por chave (PG) ou caminho de arquivo (local)."""
    if use_db():
        _pg_save(key, data)
    else:
        _file_save(file_path or key, data)
