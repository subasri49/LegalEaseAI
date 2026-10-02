"""Tiny SQLite layer that stores generated documents (history)."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL,
    parties       TEXT NOT NULL,
    terms         TEXT NOT NULL,
    dates         TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL
)
"""


def _connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def init_db():
    with closing(_connect()):
        pass


def save_document(document_type, parties, terms, dates, content) -> int:
    with closing(_connect()) as conn:
        cur = conn.execute(
            "INSERT INTO documents (document_type, parties, terms, dates, content, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (document_type, parties, terms, dates, content,
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        conn.commit()
        return cur.lastrowid


def list_documents(limit=20):
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, document_type, dates, created_at FROM documents ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_document(doc_id: int):
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None


def update_document(doc_id: int, content: str) -> bool:
    with closing(_connect()) as conn:
        cur = conn.execute("UPDATE documents SET content = ? WHERE id = ?", (content, doc_id))
        conn.commit()
        return cur.rowcount > 0


def delete_document(doc_id: int) -> bool:
    with closing(_connect()) as conn:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return cur.rowcount > 0
