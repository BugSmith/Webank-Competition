"""Service wrapper for the FundAdvice agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import json

from agents.common.telemetry import trace_agent_span

from agents.fund_advice.builder import (
    build_fund_advice_agent,
    format_fund_prompt,
)

_SPAN_TEXT_LIMIT = 2048


def _truncate(text: str) -> str:
    if len(text) <= _SPAN_TEXT_LIMIT:
        return text
    return f"{text[:_SPAN_TEXT_LIMIT-3]}..."


def _stringify_output(output: Any) -> str:
    if isinstance(output, dict) and "content" in output:
        return str(output["content"]).strip()
    if hasattr(output, "content"):
        return str(output.content).strip()
    return str(output).strip()


@dataclass
class FundAdviceService:
    """Thin service that keeps the fund agent warm."""

    def __post_init__(self) -> None:
        self.agent = build_fund_advice_agent()

    def generate_advice(self, fund_payload: Dict[str, Any]) -> str:
        prompt = format_fund_prompt(fund_payload)
        with trace_agent_span(
            "agent.fund_advice",
            {
                "agent.name": self.agent.name or "FundAdviceAgent",
            },
        ) as span:
            if span:
                span.set_attribute("agent.input.prompt", _truncate(prompt))
                span.set_attribute(
                    "agent.input.payload",
                    _truncate(json.dumps(fund_payload, ensure_ascii=False)),
                )
            output = self.agent.run(prompt)
            response_text = _stringify_output(output)
            if span:
                span.set_attribute("agent.output.text", _truncate(response_text))
        return response_text
