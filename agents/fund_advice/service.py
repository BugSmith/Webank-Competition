"""Service wrapper for the FundAdvice agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from agents.fund_advice.builder import (
    build_fund_advice_agent,
    format_fund_prompt,
)


@dataclass
class FundAdviceService:
    """Thin service that keeps the fund agent warm."""

    def __post_init__(self) -> None:
        self.agent = build_fund_advice_agent()

    def generate_advice(self, fund_payload: Dict[str, Any]) -> str:
        prompt = format_fund_prompt(fund_payload)
        output = self.agent.run(prompt)
        if isinstance(output, dict) and "content" in output:
            return str(output["content"]).strip()
        if hasattr(output, "content"):
            return str(output.content).strip()
        return str(output).strip()
