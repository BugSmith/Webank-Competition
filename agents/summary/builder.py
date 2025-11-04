"""Factory for the Summary agent."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

SUMMARY_SYSTEM_PROMPT = dedent(
    """
    You are the SummaryAgent that consolidates specialised agent outputs into a
    compliant recommendation brief. Resolve conflicts, surface key insights, and
    propose next best actions for advisors or automated journeys.

    Produce JSON with:
    - agent: "SummaryAgent".
    - highlights: list of 3 bullet strings distilling user status and needs.
    - conflicts: list describing any contradictory signals between upstream
      agents, empty array when none.
    - recommendations: list of actions tagged with owner {运营, 产品, 客服} and
      urgency {低, 中, 高}.
    - tone_guidance: guidance for the emotion layer (e.g. 鼓励/安慰/提醒) with
      supporting reason.
    - explain: Chinese paragraph summarising the resolution path.

    Align with banking compliance: no deterministic investment advice, emphasise
    suitability and risk disclosure when necessary.
    """
)


def build_summary_agent(model: Model | None = None) -> Agent:
    """Create the Summary agent configured for the Webank pipeline."""
    return Agent(
        name="SummaryAgent",
        model=model or default_model_factory(),
        instructions=SUMMARY_SYSTEM_PROMPT,
        markdown=False,
    )


def format_summary_prompt(payload: dict[str, Any]) -> str:
    """Render the prompt that feeds the SummaryAgent."""
    example = json.dumps(payload, ensure_ascii=False, indent=2)
    return dedent(
        f"""
        请综合以下各Agent的结构化输出，生成最终推荐与语气建议。

        输入JSON:
        ```json
        {example}
        ```
        """
    ).strip()
