"""Data retriever utilities for conversation agent."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from agents.db import db_cursor


def fetch_latest_asset(user_id: str) -> Optional[Dict[str, Any]]:
    return _fetch_latest(
        user_id,
        table="user_asset_snapshots",
        order_field="report_date",
        fields=["risk_level", "asset_breakdown", "credit_capacity", "raw_payload"],
    )


def fetch_latest_behavior(user_id: str) -> Optional[Dict[str, Any]]:
    return _fetch_latest(
        user_id,
        table="user_behavior_insights",
        order_field="snapshot_at",
        fields=["intent_labels", "operational_signals", "source_logs"],
    )


def fetch_latest_socio_role(user_id: str) -> Optional[Dict[str, Any]]:
    return _fetch_latest(
        user_id,
        table="user_socio_roles",
        order_field="update_time",
        fields=["role_tags", "life_stage", "raw_payload"],
    )


def fetch_latest_summary(user_id: str) -> Optional[Dict[str, Any]]:
    return _fetch_latest(
        user_id,
        table="user_insight_summary",
        order_field="created_at",
        fields=["summary_text", "recommendations"],
    )


def fetch_user_insights(user_id: str) -> Dict[str, Any]:
    """Aggregate all latest insight records for the given user."""
    return {
        "asset": fetch_latest_asset(user_id),
        "behavior": fetch_latest_behavior(user_id),
        "socio_role": fetch_latest_socio_role(user_id),
        "summary": fetch_latest_summary(user_id),
    }


def _fetch_latest(
    user_id: str,
    table: str,
    order_field: str,
    fields: list[str],
) -> Optional[Dict[str, Any]]:
    columns = ", ".join(fields + ["created_at"] if "created_at" not in fields else fields)
    query = f"""
        SELECT {columns}
        FROM {table}
        WHERE user_id=%s
        ORDER BY {order_field} DESC, id DESC
        LIMIT 1
    """

    with db_cursor() as (_, cursor):
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()

    if not row:
        return None

    normalized = {}
    for key, value in row.items():
        if isinstance(value, str) and value:
            try:
                normalized[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        if isinstance(value, datetime):
            normalized[key] = value.isoformat()
        else:
            normalized[key] = value
    return normalized
