from __future__ import annotations

from typing import Dict, List

from agents.conversation.builder import format_conversation_prompt


def test_conversation_prompt_includes_sections(
    conversation_history: List[Dict[str, str]],
) -> None:
    insights = {
        "asset": {"risk_level": "中等"},
        "behavior": {"intent_labels": ["follow_up"]},
        "summary": {"summary_text": "保持稳健"},
        "socio_role": {"life_stage": "家庭新锐"},
    }

    prompt = format_conversation_prompt(
        user_message="请帮我看看基金",
        insights=insights,
        history=conversation_history,
        context={"pageType": "financing"},
    )

    assert "## 历史对话" in prompt
    assert "## 用户洞察" in prompt
    assert "请帮我看看基金" in prompt
