"""Conversation memory helpers backed by MySQL tables."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from agents.db import db_cursor


def ensure_session(
    user_id: str,
    session_id: Optional[str] = None,
    page_context: Optional[Dict] = None,
    channel: str = "app",
) -> str:
    """Fetch or create a conversation session."""
    resolved_session = session_id or f"sess-{uuid.uuid4().hex}"

    with db_cursor() as (_, cursor):
        cursor.execute(
            "SELECT session_id FROM ai_sessions WHERE session_id=%s",
            (resolved_session,),
        )
        row = cursor.fetchone()
        if row:
            return resolved_session

        cursor.execute(
            """
            INSERT INTO ai_sessions (session_id, user_id, channel, page_context, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                resolved_session,
                user_id,
                channel,
                json.dumps(page_context or {}, ensure_ascii=False),
                datetime.utcnow(),
            ),
        )
    return resolved_session


def fetch_messages(session_id: str, limit: int = 10) -> List[Dict]:
    """Return the latest N messages ordered from old to new."""
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT sender, message, actions, insight_refs, created_at
            FROM ai_session_messages
            WHERE session_id=%s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (session_id, limit),
        )
        rows = cursor.fetchall() or []

    formatted = []
    for row in reversed(rows):
        formatted.append(
            {
                "sender": row.get("sender", "assistant"),
                "message": row.get("message", ""),
                "actions": row.get("actions"),
                "insight_refs": row.get("insight_refs"),
                "created_at": row.get("created_at"),
            }
        )
    return formatted


def append_message(
    session_id: str,
    sender: str,
    message: str,
    actions: Optional[List[Dict]] = None,
    insight_refs: Optional[List[str]] = None,
) -> None:
    """Persist a conversation message."""
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO ai_session_messages
            (session_id, sender, message, actions, insight_refs, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session_id,
                sender,
                message,
                json.dumps(actions or [], ensure_ascii=False),
                json.dumps(insight_refs or [], ensure_ascii=False),
                datetime.utcnow(),
            ),
        )
