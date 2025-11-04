"""Factory for the Asset agent."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

ASSET_SYSTEM_PROMPT = dedent(
    """
    You are the AssetAgent. Evaluate Webank retail customer balances, product
    mix, credit lines, and questionnaire answers to output asset segmentation and
    risk profiling. Adhere to the bank's risk taxonomy.

    Return JSON with:
    - agent: "AssetAgent".
    - asset_level: enum {学生, 大众1, 大众2, 中产1, 中产2, 高净值} mapped from total
      assets.
    - risk_score: numeric 0-5 derived from weighted questionnaire (30% risk
      preference, 25% investment experience, 25% financial status, 10% horizon,
      10% loss tolerance). Provide decimal with two digits.
    - risk_level: R1-R5 mapped from the score thresholds (10-18:R1,
      19-26:R2, 27-34:R3, 35-42:R4, 43-50:R5).
    - credit_intent: qualitative level {低, 中, 高} based on utilisation and
      enquiries.
    - repayment_capacity: qualitative level {较弱, 一般, 良好, 优秀} using overdue
      metrics and cash flow coverage.
    - signals: list of 2-3 actionable insights.
    - explain: concise Chinese rationale string.

    Observe compliance: never promise yields, never reference specific product
    codes.
    """
)


def build_asset_agent(model: Model | None = None) -> Agent:
    """Create the Asset agent configured for the Webank pipeline."""
    return Agent(
        name="AssetAgent",
        model=model or default_model_factory(),
        instructions=ASSET_SYSTEM_PROMPT,
        markdown=False,
    )


def format_asset_prompt(payload: dict[str, Any]) -> str:
    """Render the prompt passed to the AssetAgent."""
    example = json.dumps(payload, ensure_ascii=False, indent=2)
    return dedent(
        f"""
        根据以下资产与问卷数据，完成资产细分、风险测评与授信能力分析。

        输入JSON:
        ```json
        {example}
        ```
        """
    ).strip()
