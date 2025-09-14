# src/edututor/persistence/store.py
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

from .db import connect, initialize_db


class ConversationRecord:
    def __init__(
        self,
        id: int,
        created_at: str,
        user_text: str,
        intent: Optional[str],
        provider: Optional[str],
        llm_raw: Optional[Dict[str, Any]],
        sanitized_text: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        self.id = id
        self.created_at = created_at
        self.user_text = user_text
        self.intent = intent
        self.provider = provider
        self.llm_raw = llm_raw or {}
        self.sanitized_text = sanitized_text
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "user_text": self.user_text,
            "intent": self.intent,
            "provider": self.provider,
            "llm_raw": self.llm_raw,
            "sanitized_text": self.sanitized_text,
            "metadata": self.metadata,
        }


class ConversationStore:
    """Simple DAO for conversation logs."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path
        initialize_db(self.db_path)

    def save_conversation(
        self,
        user_text: str,
        intent: Optional[str],
        provider: Optional[str],
        llm_raw: Optional[Dict[str, Any]],
        sanitized_text: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Insert a conversation row. Returns the inserted row id."""
        created_at = datetime.utcnow().isoformat() + "Z"
        llm_raw_txt = json.dumps(llm_raw or {})
        metadata_txt = json.dumps(metadata or {})
        with connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO conversations
                (created_at, user_text, intent, provider, llm_raw, sanitized_text, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    user_text,
                    intent,
                    provider,
                    llm_raw_txt,
                    sanitized_text,
                    metadata_txt,
                ),
            )
            return cast_int(cur.lastrowid)

    def fetch_recent(self, limit: int = 100) -> List[ConversationRecord]:
        with connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, created_at, user_text, intent, provider, "
                "llm_raw, sanitized_text, metadata "
                "FROM conversations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [self._row_to_record(r) for r in rows]

    def fetch_by_id(self, row_id: int) -> Optional[ConversationRecord]:
        with connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, created_at, user_text, intent, provider, "
                "llm_raw, sanitized_text, metadata "
                "FROM conversations WHERE id = ?",
                (row_id,),
            )
            row = cur.fetchone()
            return self._row_to_record(row) if row else None

    def export_json(self, limit: int = 100) -> str:
        """Return a JSON string of recent conversations."""
        recs = self.fetch_recent(limit)
        return json.dumps([r.to_dict() for r in recs], indent=2)

    def _row_to_record(self, row: Mapping[str, Any]) -> ConversationRecord:
        # sqlite Row supports mapping lookups by column name
        try:
            llm_raw = json.loads(row["llm_raw"]) if row["llm_raw"] else {}
        except Exception:
            llm_raw = {}
        try:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        except Exception:
            metadata = {}
        return ConversationRecord(
            id=row["id"],
            created_at=row["created_at"],
            user_text=row["user_text"],
            intent=row["intent"],
            provider=row["provider"],
            llm_raw=llm_raw,
            sanitized_text=row["sanitized_text"],
            metadata=metadata,
        )


def cast_int(x: Any) -> int:
    # sqlite Cursor.lastrowid may already be int; fallback safe-casting
    try:
        return int(x)
    except Exception:
        return 0
