"""Factory for the SocioRole agent."""

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

SOCIO_ROLE_SYSTEM_PROMPT = (
    (PROMPTS_DIR / "socio_role_system_prompt.md").read_text(encoding="utf-8")
)
SOCIO_ROLE_MODEL_ID = os.getenv("SOCIO_ROLE_AGENT_MODEL_ID", "qwen-max")
_SOCIO_MODEL_FACTORY = build_model_factory(SOCIO_ROLE_MODEL_ID)


def build_socio_role_agent(model: Model | None = None) -> Agent:
    """Create the SocioRole agent configured for the Webank pipeline."""
    return Agent(
        name="SocioRoleAgent",
        model=model or _SOCIO_MODEL_FACTORY(),
        instructions=SOCIO_ROLE_SYSTEM_PROMPT,
        markdown=False,
    )


def format_socio_role_prompt(payload: dict[str, Any]) -> str:
    """Render the prompt that feeds the SocioRoleAgent."""
    example = json.dumps(payload, ensure_ascii=False, indent=2)
    return dedent(
        f"""
        请基于以下输入生成用户社会角色标签。严格遵循系统提示中的字段定义。

        输入JSON:
        ```json
        {example}
        ```
        """
    ).strip()
