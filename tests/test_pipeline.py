from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from agents.pipeline import WebankAgentPipeline


@dataclass
class _DummyAgent:
    output: Any

    def run(self, prompt: str) -> Any:  # pragma: no cover - simple stub
        self.last_prompt = prompt
        return self.output


def test_pipeline_merges_agent_outputs(pipeline_payload: Dict[str, Any]) -> None:
    pipeline = WebankAgentPipeline(
        socio_role_agent=_DummyAgent({"role_tags": ["白领"]}),
        asset_agent=_DummyAgent('{"risk_level":"中等"}'),
        behavior_agent=_DummyAgent({"intent_labels": ["follow_up"]}),
        summary_agent=_DummyAgent({"summary": "保持定投", "recommendations": ["控制仓位"]}),
    )

    result = pipeline.run(pipeline_payload)

    assert result["socio_role"]["role_tags"] == ["白领"]
    assert result["asset"]["risk_level"] == "中等"
    assert result["behavior"]["intent_labels"] == ["follow_up"]
    assert result["summary"]["summary"] == "保持定投"
