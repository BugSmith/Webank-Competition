"""Factory for the Asset agent."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

ASSET_SYSTEM_PROMPT = (
    (PROMPTS_DIR / "asset_system_prompt.md").read_text(encoding="utf-8")
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
