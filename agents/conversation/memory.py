"""Conversation memory helpers backed by MySQL tables."""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from agents.db import db_cursor

logger = logging.getLogger(__name__)

_USE_MEMORY = os.getenv("AI_MEMORY_BACKEND", "").lower() == "memory"
_MEM_SESSIONS: Dict[str, Dict] = {}
_MEM_MESSAGES: Dict[str, List[Dict]] = defaultdict(list)


def _enable_memory_mode(reason: Exception) -> None:
    global _USE_MEMORY
    if not _USE_MEMORY:
        _USE_MEMORY = True
        logger.warning(
            "Conversation DB 不可用，切换为内存模式：%s。会话记录仅在进程内有效。", reason
        )


def ensure_session(
    user_id: str,
    session_id: Optional[str] = None,
    page_context: Optional[Dict] = None,
    channel: str = "app",
) -> str:
    """Fetch or create a conversation session."""
    resolved_session = session_id or f"sess-{uuid.uuid4().hex}"

    if _USE_MEMORY:
        _MEM_SESSIONS.setdefault(
            resolved_session,
            {
                "user_id": user_id,
                "channel": channel,
                "page_context": page_context or {},
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        return resolved_session

    try:
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
    except Exception as exc:  # pragma: no cover - fallback path
        _enable_memory_mode(exc)
        return ensure_session(user_id, session_id=resolved_session, page_context=page_context, channel=channel)


def fetch_messages(session_id: str, limit: int = 10) -> List[Dict]:
    """Return the latest N messages ordered from old to new."""
    if _USE_MEMORY:
        rows = _MEM_MESSAGES.get(session_id, [])[-limit:]
        return list(rows)

    try:
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
    except Exception as exc:  # pragma: no cover
        _enable_memory_mode(exc)
        return fetch_messages(session_id, limit)

    formatted: List[Dict] = []
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
    payload = {
        "sender": sender,
        "message": message,
        "actions": actions or [],
        "insight_refs": insight_refs or [],
        "created_at": datetime.utcnow().isoformat(),
    }

    if _USE_MEMORY:
        _MEM_MESSAGES[session_id].append(payload)
        return

    try:
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
    except Exception as exc:  # pragma: no cover
        _enable_memory_mode(exc)
        append_message(session_id, sender, message, actions, insight_refs)
