"""Factory for the FundAdvice agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict

from agno.agent import Agent
from agno.models.base import Model

from agents.models import build_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
FUND_PROMPT_PATH = PROMPTS_DIR / "fund_advice_system_prompt.md"

FUND_ADVICE_SYSTEM_PROMPT = FUND_PROMPT_PATH.read_text(encoding="utf-8")
FUND_AGENT_MODEL_ID = os.getenv("FUND_AGENT_MODEL_ID", "qwen-plus")
_FUND_MODEL_FACTORY = build_model_factory(FUND_AGENT_MODEL_ID)


def build_fund_advice_agent(model: Model | None = None) -> Agent:
    """Create the FundAdvice agent configured for Webank."""
    return Agent(
        name="FundAdviceAgent",
        model=model or _FUND_MODEL_FACTORY(),
        instructions=FUND_ADVICE_SYSTEM_PROMPT,
        markdown=False,
    )


def format_fund_prompt(fund_payload: Dict[str, Any]) -> str:
    """Render the prompt fed to the FundAdvice agent."""
    sample = json.dumps(fund_payload, ensure_ascii=False, indent=2)
    return dedent(
        f"""
        请根据以下基金信息，输出一句专业、合规的投资提示（不超过120字）。
        - 避免承诺收益或过度营销
        - 可给出风险提示或配置建议

        输入:
        ```json
        {sample}
        ```
        """
    ).strip()
