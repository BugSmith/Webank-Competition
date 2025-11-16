"""Composable pipeline orchestrating the Webank agents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from agno.agent import Agent

from agents.asset.builder import build_asset_agent, format_asset_prompt
from agents.behavior.builder import build_behavior_agent, format_behavior_prompt
from agents.common.telemetry import trace_agent_span
from agents.models import build_model_factory, default_model_factory
from agents.socio_role.builder import (
    build_socio_role_agent,
    format_socio_role_prompt,
)
from agents.summary.builder import build_summary_agent, format_summary_prompt

_SPAN_TEXT_LIMIT = 2048


def _truncate(text: str, limit: int = _SPAN_TEXT_LIMIT) -> str:
    """Clip long metadata attributes to avoid oversized spans."""

    if limit <= 3:
        return text[:limit]
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _stringify_output(output: Any) -> str:
    """Render various agent outputs to plain text for tracing."""

    if isinstance(output, dict) and "content" in output:
        return str(output["content"]).strip()
    if hasattr(output, "content"):
        return str(output.content).strip()
    return str(output).strip()


def _safe_json_dumps(payload: Any) -> str:
    """Serialize payloads defensively for span attributes."""

    try:
        return json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(payload)


def _annotate_agent_input(
    span: Any,
    prompt: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    if span is None:
        return
    span.set_attribute("agent.input.prompt", _truncate(prompt))
    if payload is not None:
        span.set_attribute("agent.input.payload", _truncate(_safe_json_dumps(payload)))


def _annotate_agent_raw_output(span: Any, output: Any) -> None:
    if span is None:
        return
    rendered = _stringify_output(output)
    if rendered:
        span.set_attribute("agent.output.raw", _truncate(rendered))


def _annotate_agent_structured_output(span: Any, payload: Dict[str, Any]) -> None:
    if span is None:
        return
    span.set_attribute("agent.output.json", _truncate(_safe_json_dumps(payload)))


@dataclass(slots=True)
class WebankAgentPipeline:
    """Sequential pipeline wiring the specialised agno agents."""

    socio_role_agent: Agent
    asset_agent: Agent
    behavior_agent: Agent
    summary_agent: Agent

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full agent pipeline and return merged outputs."""

        with trace_agent_span(
            "pipeline.run",
            {"pipeline.name": "WebankAgentPipeline"},
        ) as pipeline_span:
            if pipeline_span is not None:
                pipeline_span.set_attribute(
                    "pipeline.input.payload",
                    _truncate(_safe_json_dumps(payload)),
                )

            socio_input = payload.get("socio_role", {})
            asset_input = payload.get("asset", {})
            behavior_input = payload.get("behavior", {})

            socio_prompt = format_socio_role_prompt(socio_input)
            with trace_agent_span(
                "agent.socio_role",
                {
                    "agent.name": self.socio_role_agent.name or "SocioRoleAgent",
                    "pipeline.stage": "socio_role",
                },
            ) as span:
                _annotate_agent_input(span, socio_prompt, socio_input)
                socio_raw = self.socio_role_agent.run(socio_prompt)
                _annotate_agent_raw_output(span, socio_raw)
                socio_result = _safe_json_loads(socio_raw)
                _annotate_agent_structured_output(span, socio_result)

            asset_prompt = format_asset_prompt(asset_input)
            with trace_agent_span(
                "agent.asset",
                {
                    "agent.name": self.asset_agent.name or "AssetAgent",
                    "pipeline.stage": "asset",
                },
            ) as span:
                _annotate_agent_input(span, asset_prompt, asset_input)
                asset_raw = self.asset_agent.run(asset_prompt)
                _annotate_agent_raw_output(span, asset_raw)
                asset_result = _safe_json_loads(asset_raw)
                _annotate_agent_structured_output(span, asset_result)

            behavior_prompt = format_behavior_prompt(behavior_input)
            with trace_agent_span(
                "agent.behavior",
                {
                    "agent.name": self.behavior_agent.name or "BehaviorAgent",
                    "pipeline.stage": "behavior",
                },
            ) as span:
                _annotate_agent_input(span, behavior_prompt, behavior_input)
                behavior_raw = self.behavior_agent.run(behavior_prompt)
                _annotate_agent_raw_output(span, behavior_raw)
                behavior_result = _safe_json_loads(behavior_raw)
                _annotate_agent_structured_output(span, behavior_result)

            summary_payload = {
                "socio_role": socio_result,
                "asset": asset_result,
                "behavior": behavior_result,
                "context": payload.get("context", {}),
            }
            summary_prompt = format_summary_prompt(summary_payload)
            with trace_agent_span(
                "agent.summary",
                {
                    "agent.name": self.summary_agent.name or "SummaryAgent",
                    "pipeline.stage": "summary",
                },
            ) as span:
                _annotate_agent_input(span, summary_prompt, summary_payload)
                summary_raw = self.summary_agent.run(summary_prompt)
                _annotate_agent_raw_output(span, summary_raw)
                summary_result = _safe_json_loads(summary_raw)
                _annotate_agent_structured_output(span, summary_result)

            result = {
                "socio_role": socio_result,
                "asset": asset_result,
                "behavior": behavior_result,
                "summary": summary_result,
            }

            if pipeline_span is not None:
                pipeline_span.set_attribute(
                    "pipeline.output.payload",
                    _truncate(_safe_json_dumps(result)),
                )

        return result


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
        normalized = _extract_json_payload(output)
        try:
            return json.loads(normalized)
        except json.JSONDecodeError as exc:
            snippet = normalized[:200]
            raise ValueError(f"Agent returned non-JSON payload: {snippet}") from exc
    msg = f"Unsupported agent output type: {type(output)}"
    raise TypeError(msg)


_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _extract_json_payload(text: str) -> str:
    """Best-effort cleanup for model outputs wrapped在 Markdown 或额外描述中."""

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Agent returned empty response.")

    match = _CODE_BLOCK_RE.search(cleaned)
    if match:
        cleaned = match.group(1).strip()

    # Trim任何前缀描述，定位到第一个 JSON 起始符
    for idx, char in enumerate(cleaned):
        if char in "{[":
            if idx > 0:
                cleaned = cleaned[idx:]
            break

    return cleaned
