# src/edututor/persistence/db.py
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

DEFAULT_DB_PATH = Path.home() / ".edututor" / "edututor.db"


def ensure_db_path(path: Optional[str]) -> Path:
    if path:
        p = Path(path)
    else:
        p = DEFAULT_DB_PATH
    # create parent directory if missing
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def connect(path: Optional[str] = None) -> Iterator[sqlite3.Connection]:
    """Context manager that yields a sqlite3.Connection with row access by name."""
    db_path = ensure_db_path(path)
    conn = sqlite3.connect(str(db_path), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def initialize_db(path: Optional[str] = None) -> None:
    """Create the conversations table if it doesn't exist."""
    # avoid using DESC in index definition for maximum compatibility
    ddl = """
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        user_text TEXT NOT NULL,
        intent TEXT,
        provider TEXT,
        llm_raw TEXT,
        sanitized_text TEXT,
        metadata TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
    """
    with connect(path) as conn:
        conn.executescript(ddl)
