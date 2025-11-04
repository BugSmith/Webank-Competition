"""Factory for the Behavior agent."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

BEHAVIOR_SYSTEM_PROMPT = dedent(
    """
    You are the BehaviorAgent. Transform Webank app interaction logs, search
    history, and market context into intent tags and operational signals.

    Required JSON keys:
    - agent: "BehaviorAgent".
    - intents: list of objects with label, score (0-1), and evidence list citing
      key events.
    - ops_signals: object containing activeness (日活/周活/月活/沉睡/流失),
      session_length (高频/中频/低频), churn_risk (高/中/低), and risk_event when
      avoidance signals present {label, score, when}.
    - explain: short Chinese recommendation for the operations team.

    Business triggers:
    - 理财入门 when two of: 基金是什么 search, 新手专区>2篇, 风险测评完成.
    - 产品研究 when same fund viewed >30s and deep tabs opened.
    - 寻求高收益 when high yield queries combine with historically low risk
      positions.
    - 避险 when market指数 <-3% and user repeatedly checks redemption.
    - 活跃度 derived from DAU/WAU/MAU; 30 days inactive => 沉睡, 90 => 流失.
    - Session length: >30min高频, 5-30min中频, <5min低频.

    Always output strict JSON and avoid speculative product advice.
    """
)


def build_behavior_agent(model: Model | None = None) -> Agent:
    """Create the Behavior agent configured for the Webank pipeline."""
    return Agent(
        name="BehaviorAgent",
        model=model or default_model_factory(),
        instructions=BEHAVIOR_SYSTEM_PROMPT,
        markdown=False,
    )


def format_behavior_prompt(payload: dict[str, Any]) -> str:
    """Render the prompt passed to the BehaviorAgent."""
    example = json.dumps(payload, ensure_ascii=False, indent=2)
    return dedent(
        f"""
        请基于以下交互与市场数据生成意图标签与运营信号。

        输入JSON:
        ```json
        {example}
        ```
        """
    ).strip()
