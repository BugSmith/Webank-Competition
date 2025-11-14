from __future__ import annotations

from typing import Any, Dict

from agents.fund_advice.service import FundAdviceService


class _StaticAgent:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_prompt = ""

    def run(self, prompt: str) -> Any:
        self.last_prompt = prompt
        return self.response


def test_fund_advice_service_returns_normalized_content(sample_fund_payload: Dict[str, Any]) -> None:
    service = FundAdviceService.__new__(FundAdviceService)
    service.agent = _StaticAgent({"content": "保持分散配置，关注净值波动。"})

    result = service.generate_advice(sample_fund_payload)

    assert "分散" in result
    assert "净值" in result
