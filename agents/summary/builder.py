"""Factory for the Summary agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import build_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

SUMMARY_SYSTEM_PROMPT = (
    (PROMPTS_DIR / "summary_system_prompt.md").read_text(encoding="utf-8")
)
SUMMARY_MODEL_ID = os.getenv("SUMMARY_AGENT_MODEL_ID", "qwen-max")
_SUMMARY_MODEL_FACTORY = build_model_factory(SUMMARY_MODEL_ID)


def build_summary_agent(model: Model | None = None) -> Agent:
    """Create the Summary agent configured for the Webank pipeline."""
    return Agent(
        name="SummaryAgent",
        model=model or _SUMMARY_MODEL_FACTORY(),
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
