"""Factory helpers for the multi-turn conversation agent."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
CONVERSATION_PROMPT_PATH = PROMPTS_DIR / "conversation_system_prompt.md"
CONVERSATION_SYSTEM_PROMPT = CONVERSATION_PROMPT_PATH.read_text(encoding="utf-8")
logger = logging.getLogger(__name__)


def _has_dashscope_key() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY"))


class FallbackConversationAgent:
    """本地兜底模型，确保在无 DashScope/OpenAI Key 时仍可返回响应。"""

    name = "ConversationFallbackAgent"

    section_pattern = re.compile(r"^## (.+?)\n(.*?)(?=^## |\Z)", re.M | re.S)

    @classmethod
    def _parse_sections(cls, prompt: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        for match in cls.section_pattern.finditer(prompt):
            sections[match.group(1).strip()] = match.group(2).strip()
        return sections

    def run(self, prompt: str) -> str:

        sections = self._parse_sections(prompt)
        question = sections.get("当前用户提问", "").strip()
        insights_section = sections.get("用户洞察", "").strip()

        insight_summary = ""
        if insights_section:
            candidate = insights_section
            try:
                candidate_dict = json.loads(insights_section)
            except json.JSONDecodeError:
                candidate_dict = None
            if isinstance(candidate_dict, dict):
                candidate = json.dumps(candidate_dict, ensure_ascii=False)
            insight_summary = candidate[:200]

        response_parts = [
            "当前处于离线演练模式，我已记录您的需求并会在服务恢复后第一时间跟进。",
        ]
        if question:
            response_parts.append(f"您刚才的提问是：「{question.strip()}」。")
        if insight_summary:
            response_parts.append(f"已有洞察参考：{insight_summary}")
        response_parts.append("如需立即处理，可联系人工客服或稍后再试。")
        return "\n\n".join(response_parts)


def build_conversation_agent(model: Model | None = None) -> Agent:
    """Instantiate the conversation agent with default model + instructions."""
    if _has_dashscope_key():
        return Agent(
            name="ConversationAgent",
            model=model or default_model_factory(),
            instructions=CONVERSATION_SYSTEM_PROMPT,
            markdown=False,
        )

    logger.warning(
        "未检测到 DASHSCOPE_API_KEY，ConversationAgent 将使用 FallbackConversationAgent 以离线模式运行。"
    )
    return FallbackConversationAgent()


def format_conversation_prompt(
    user_message: str,
    insights: Dict[str, Any],
    history: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Render the single prompt passed to agno Agent."""
    history_lines = []
    for item in history:
        speaker = "用户" if item["sender"] == "user" else "AI"
        history_lines.append(f"{speaker}: {item['message']}")
    history_block = "\n".join(history_lines) if history_lines else "（无历史对话）"

    return dedent(
        f"""
        ## 历史对话
        {history_block}

        ## 上下文
        {context or {}}

        ## 用户洞察
        {insights}

        ## 当前用户提问
        {user_message}
        """
    ).strip()
