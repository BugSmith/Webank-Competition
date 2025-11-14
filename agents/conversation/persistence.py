"""Persist agent insights into MySQL tables."""

from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any, Dict, Optional

from agents.db import db_cursor


def persist_asset_snapshot(user_id: str, payload: Optional[Dict[str, Any]]) -> None:
    if not payload:
        return
    report_date = payload.get("report_date") or payload.get("date") or date.today()
    risk_level = payload.get("risk_level") or payload.get("riskLevel")
    breakdown = payload.get("asset_breakdown") or payload.get("assetBreakdown") or payload
    credit_capacity = payload.get("credit_capacity") or payload.get("creditCapacity")

    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO user_asset_snapshots
            (user_id, report_date, risk_level, asset_breakdown, credit_capacity, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                report_date,
                risk_level,
                json.dumps(breakdown or {}, ensure_ascii=False),
                json.dumps(credit_capacity or {}, ensure_ascii=False),
                json.dumps(payload, ensure_ascii=False),
            ),
        )


def persist_behavior_insight(user_id: str, payload: Optional[Dict[str, Any]]) -> None:
    if not payload:
        return

    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO user_behavior_insights
            (user_id, snapshot_at, intent_labels, operational_signals, source_logs)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                payload.get("snapshot_at") or datetime.utcnow(),
                json.dumps(payload.get("intent_labels") or payload.get("intents") or [], ensure_ascii=False),
                json.dumps(
                    payload.get("operational_signals") or payload.get("signals") or {}, ensure_ascii=False
                ),
                json.dumps(payload.get("source_logs") or payload, ensure_ascii=False),
            ),
        )


def persist_socio_role(user_id: str, payload: Optional[Dict[str, Any]]) -> None:
    if not payload:
        return

    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO user_socio_roles
            (user_id, role_tags, life_stage, raw_payload, update_time)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                json.dumps(payload.get("role_tags") or payload.get("tags") or [], ensure_ascii=False),
                payload.get("life_stage") or payload.get("lifeStage"),
                json.dumps(payload, ensure_ascii=False),
                datetime.utcnow(),
            ),
        )


def persist_summary(user_id: str, payload: Optional[Dict[str, Any]]) -> None:
    if not payload:
        return

    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO user_insight_summary
            (user_id, summary_text, recommendations, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                payload.get("summary") or payload.get("summary_text") or "",
                json.dumps(payload.get("recommendations") or payload, ensure_ascii=False),
                datetime.utcnow(),
            ),
        )
