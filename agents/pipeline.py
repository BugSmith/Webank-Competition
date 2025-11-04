"""Composable pipeline orchestrating the Webank agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from agno.agent import Agent

from agents.asset.builder import build_asset_agent, format_asset_prompt
from agents.behavior.builder import build_behavior_agent, format_behavior_prompt
from agents.models import build_model_factory, default_model_factory
from agents.socio_role.builder import (
    build_socio_role_agent,
    format_socio_role_prompt,
)
from agents.summary.builder import build_summary_agent, format_summary_prompt


@dataclass(slots=True)
class WebankAgentPipeline:
    """Sequential pipeline wiring the specialised agno agents."""

    socio_role_agent: Agent
    asset_agent: Agent
    behavior_agent: Agent
    summary_agent: Agent

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full agent pipeline and return merged outputs."""
        socio_input = payload.get("socio_role", {})
        asset_input = payload.get("asset", {})
        behavior_input = payload.get("behavior", {})

        socio_raw = self.socio_role_agent.run(
            format_socio_role_prompt(socio_input)
        )
        socio_result = _safe_json_loads(socio_raw)

        asset_raw = self.asset_agent.run(format_asset_prompt(asset_input))
        asset_result = _safe_json_loads(asset_raw)

        behavior_raw = self.behavior_agent.run(
            format_behavior_prompt(behavior_input)
        )
        behavior_result = _safe_json_loads(behavior_raw)

        summary_payload = {
            "socio_role": socio_result,
            "asset": asset_result,
            "behavior": behavior_result,
            "context": payload.get("context", {}),
        }
        summary_raw = self.summary_agent.run(
            format_summary_prompt(summary_payload)
        )
        summary_result = _safe_json_loads(summary_raw)

        return {
            "socio_role": socio_result,
            "asset": asset_result,
            "behavior": behavior_result,
            "summary": summary_result,
        }


def build_default_pipeline(model_id: str | None = None) -> WebankAgentPipeline:
    """Construct the pipeline with DashScope models."""
    factory = build_model_factory(model_id) if model_id else default_model_factory

    socio_agent = build_socio_role_agent(model=factory())
    asset_agent = build_asset_agent(model=factory())
    behavior_agent = build_behavior_agent(model=factory())
    summary_agent = build_summary_agent(model=factory())

    return WebankAgentPipeline(
        socio_role_agent=socio_agent,
        asset_agent=asset_agent,
        behavior_agent=behavior_agent,
        summary_agent=summary_agent,
    )


def _safe_json_loads(output: Any) -> Dict[str, Any]:
    """Convert agent output into a dictionary, tolerant of Agent returns."""
    if isinstance(output, dict):
        return output
    if hasattr(output, "model_dump"):
        return output.model_dump()
    if hasattr(output, "content"):
        return _safe_json_loads(output.content)
    if isinstance(output, str):
        return json.loads(output)
    msg = f"Unsupported agent output type: {type(output)}"
    raise TypeError(msg)
