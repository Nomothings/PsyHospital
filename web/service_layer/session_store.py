"""SQLite-backed chat session persistence."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteChatSessionStore:
    """Small SQLite store for web chat sessions."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    messages_json TEXT NOT NULL,
                    llm_history_json TEXT NOT NULL,
                    last_active REAL NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_active "
                "ON chat_sessions(last_active)"
            )

    def create_session(
        self,
        session_id: str,
        case_id: str,
        record_id: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        llm_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        session = {
            "session_id": session_id,
            "case_id": case_id,
            "record_id": record_id,
            "messages": messages or [],
            "llm_history": llm_history or [],
            "last_active": now,
            "created_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chat_sessions (
                    session_id, case_id, record_id, messages_json,
                    llm_history_json, last_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    case_id,
                    record_id,
                    json.dumps(session["messages"], ensure_ascii=False),
                    json.dumps(session["llm_history"], ensure_ascii=False),
                    now,
                    now,
                ),
            )
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    def update_session_messages(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        llm_history: List[Dict[str, Any]],
    ) -> None:
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE chat_sessions
                SET messages_json = ?, llm_history_json = ?, last_active = ?
                WHERE session_id = ?
                """,
                (
                    json.dumps(messages, ensure_ascii=False),
                    json.dumps(llm_history, ensure_ascii=False),
                    now,
                    session_id,
                ),
            )

    def touch_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE chat_sessions SET last_active = ? WHERE session_id = ?",
                (time.time(), session_id),
            )

    def delete_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))

    def delete_expired_sessions(self, ttl_seconds: int) -> int:
        cutoff = time.time() - ttl_seconds
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM chat_sessions WHERE last_active < ?",
                (cutoff,),
            )
            return cursor.rowcount

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_sessions ORDER BY last_active DESC"
            ).fetchall()
        return [self._row_to_session(row) for row in rows]

    @staticmethod
    def _loads_json(value: str, default: Any) -> Any:
        try:
            return json.loads(value or "")
        except json.JSONDecodeError:
            return default

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "session_id": row["session_id"],
            "case_id": row["case_id"],
            "record_id": row["record_id"],
            "messages": self._loads_json(row["messages_json"], []),
            "llm_history": self._loads_json(row["llm_history_json"], []),
            "last_active": row["last_active"],
            "created_at": row["created_at"],
        }
