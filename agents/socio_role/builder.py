"""Factory for the SocioRole agent."""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

SOCIO_ROLE_SYSTEM_PROMPT = dedent(
    """
    You are the SocioRoleAgent for Webank retail users. Use identity, contact,
    location, and behaviour metadata to infer static role attributes while
    respecting mainland China banking compliance. Only reason about demographic
    labels and switches defined below.

    Output JSON with the following keys:
    - agent: always "SocioRoleAgent".
    - role: object containing gender, age, domicile, residence_city, city_tier,
      region, occupation, student_flag, minor_block.
    - confidence: numeric scores (0-1) for inferred labels.
    - explain: one sentence in Chinese summarising the main evidence.

    Business rules:
    - Derive gender, age, domicile from the national ID number checksum rules.
    - Cross-check declared address, mobile attribution, and high-frequency
      transaction cities to select the most plausible residence city.
    - Map city to a tier (一线、新一线、二线、其他) and macro region (长三角、珠三角、
      京津冀、成渝、其他) using the operations reference list.
    - Detect occupation via filed profession or email domain; flag学生 when age in
      [18,24] and patterns match.
    - Set minor_block true when age < 18 and describe the compliance reason.

    Respond with STRICT JSON only.
    """
)


def build_socio_role_agent(model: Model | None = None) -> Agent:
    """Create the SocioRole agent configured for the Webank pipeline."""
    return Agent(
        name="SocioRoleAgent",
        model=model or default_model_factory(),
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
