"""Factory for the Behavior agent."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

BEHAVIOR_SYSTEM_PROMPT = (
    (PROMPTS_DIR / "behavior_system_prompt.md").read_text(encoding="utf-8")
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
