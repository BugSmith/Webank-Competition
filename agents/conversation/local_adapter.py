"""Local conversation responder using existing user data samples."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.db import db_cursor

logger = logging.getLogger(__name__)


def _safe_query(sql: str, params: tuple[Any, ...]) -> List[Dict[str, Any]]:
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(sql, params)
            return cursor.fetchall() or []
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Local conversation query failed: %s", exc)
        return []


def _load_positions(user_id: str) -> List[Dict[str, Any]]:
    rows = _safe_query(
        """
        SELECT position_type, product_name, product_code, current_value,
               profit_loss, profit_loss_percent
        FROM UserPositions
        WHERE user_id=%s AND status='active'
        ORDER BY updated_at DESC
        LIMIT 5
        """,
        (user_id,),
    )
    if rows:
        return rows

    # Hard-coded fallback for offline demos
    return [
        {
            "position_type": "fund",
            "product_name": "易方达蓝筹精选混合",
            "product_code": "005827",
            "current_value": 2874.5,
            "profit_loss": 374.5,
            "profit_loss_percent": 14.98,
        },
        {
            "position_type": "fund",
            "product_name": "诺安成长混合",
            "product_code": "320007",
            "current_value": 882.7,
            "profit_loss": -17.3,
            "profit_loss_percent": -1.92,
        },
    ]


def _load_recent_bills(user_id: str) -> List[Dict[str, Any]]:
    rows = _safe_query(
        """
        SELECT merchant, category, amount, transaction_date
        FROM Bills
        WHERE user_id=%s
        ORDER BY transaction_date DESC
        LIMIT 3
        """,
        (user_id,),
    )
    if rows:
        return rows
    today = datetime.utcnow().date().isoformat()
    return [
        {
            "merchant": "星巴克咖啡",
            "category": "餐饮",
            "amount": -45,
            "transaction_date": today,
        },
        {
            "merchant": "沃尔玛超市",
            "category": "购物",
            "amount": -189.5,
            "transaction_date": today,
        },
    ]


def _load_recent_news() -> List[Dict[str, Any]]:
    rows = _safe_query(
        """
        SELECT title, summary, category, publish_time
        FROM News
        ORDER BY publish_time DESC, id DESC
        LIMIT 3
        """,
        (),
    )
    if rows:
        return rows
    today = datetime.utcnow().date().isoformat()
    return [
        {
            "title": "央行维持利率稳定",
            "summary": "央行表示将继续保持流动性合理充裕，支持实体经济发展。",
            "category": "宏观",
            "publish_time": today,
        },
        {
            "title": "科技板块领涨A股",
            "summary": "A股冲高回落，科技和新能源板块走势较强。",
            "category": "市场",
            "publish_time": today,
        },
    ]


def _summarize_positions(positions: List[Dict[str, Any]]) -> str:
    if not positions:
        return "暂未查询到持仓信息，您可以先浏览推荐基金。"
    highlights = []
    for pos in positions:
        value = pos.get("current_value") or 0
        gain = pos.get("profit_loss_percent")
        pct = f"{gain:.2f}%" if isinstance(gain, (int, float)) else "--"
        highlights.append(
            f"{pos.get('product_name')}({pos.get('product_code')}) 当前市值约¥{value:.2f}，收益 {pct}"
        )
    return "；".join(highlights)


def _summarize_bills(bills: List[Dict[str, Any]]) -> str:
    if not bills:
        return "最近暂无账单记录。"
    parts = []
    for bill in bills:
        amount = bill.get("amount", 0)
        parts.append(
            f"{bill.get('transaction_date')} {bill.get('merchant')} {bill.get('category')} 支出¥{abs(amount):.2f}"
        )
    return "；".join(parts)


def _build_answer(message: str, insights: Dict[str, Any], user_id: str) -> str:
    asset = insights.get("asset") or {}
    summary = insights.get("summary") or {}
    behavior = insights.get("behavior") or {}

    news_items = _load_recent_news()

    lines = []
    if asset:
        total = asset.get("overall", {}).get("total_value")
        risk = asset.get("overall", {}).get("risk_level")
        if total:
            lines.append(f"目前为您估算的总资产约¥{total:,.2f}，整体风险等级为{risk or '中等'}。")
    if summary.get("summary_text"):
        lines.append(summary["summary_text"])

    positions = _load_positions(user_id)
    bills = _load_recent_bills(user_id)
    topic = _detect_topic(message)

    if topic == "fund":
        lines.append("【持仓摘要】" + _summarize_positions(positions))
        if behavior.get("intent_labels"):
            intent = behavior["intent_labels"][0] if isinstance(behavior["intent_labels"], list) else behavior["intent_labels"]
            lines.append(f"根据行为意图识别，当前偏好：{intent}。建议分批参与，关注净值波动。")
    elif topic == "bill":
        lines.append("【近期账单】" + _summarize_bills(bills))
        lines.append("建议结合预算对高频消费进行归类管理，设定提醒避免重复支出。")
    elif topic == "bill":
        lines.append("【近期账单】" + _summarize_bills(bills))
        lines.append("建议结合预算对高频消费进行归类管理，设定提醒避免重复支出。")
    elif topic == "news":
        lines.append("【今日财经速递】")
        for item in news_items:
            lines.append(f"- {item.get('title')}：{item.get('summary')}")
        lines.append("如需了解更多详情，可前往资讯页查看。")
    else:
        lines.append("【资产概览】" + _summarize_positions(positions))
        lines.append("【近期账单】" + _summarize_bills(bills))
        if news_items:
            lines.append("【今日资讯】")
            lines.extend(f"- {item.get('title')}：{item.get('summary')}" for item in news_items)
        lines.append("整体保持稳健，若计划增配，可优先考虑与现有风格匹配的稳健基金或分层定投策略。")

    lines.append("如需进一步分析，请告诉我具体关注的基金、账单或转账场景。")
    return "\n".join(lines)


def _detect_topic(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["fund", "基金", "持仓", "收益"]):
        return "fund"
    if any(k in msg for k in ["bill", "账单", "消费", "支出"]):
        return "bill"
    if any(k in msg for k in ["news", "资讯", "新闻", "快讯"]):
        return "news"
    return "general"


def build_local_context(user_id: str, message: str) -> Dict[str, Any]:
    return {
        "localPositions": _load_positions(user_id),
        "localBills": _load_recent_bills(user_id),
        "localNews": _load_recent_news(),
        "detectedTopic": _detect_topic(message),
    }


def build_local_reply(
    user_id: str,
    message: str,
    history: List[Dict[str, Any]],
    insights: Dict[str, Any],
) -> Dict[str, Any]:
    response_text = _build_answer(message, insights or {}, user_id)
    actions: List[Dict[str, Any]] = []
    topic = _detect_topic(message)
    if topic == "fund":
        top = _load_positions(user_id)[:1]
        if top:
            actions.append(
                {
                    "type": "navigate",
                    "label": "查看基金详情",
                    "page": "fund_detail",
                    "payload": {"code": top[0].get("product_code")},
                }
            )

    return {
        "response": response_text,
        "actions": actions,
        "insight_refs": history[-3:] if history else [],
    }
