"""Factory helpers for the multi-turn conversation agent."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional

from agno.agent import Agent
from agno.models.base import Model

from agents.models import default_model_factory

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
CONVERSATION_PROMPT_PATH = PROMPTS_DIR / "conversation_system_prompt.md"
CONVERSATION_SYSTEM_PROMPT = CONVERSATION_PROMPT_PATH.read_text(encoding="utf-8")


def build_conversation_agent(model: Model | None = None) -> Agent:
    """Instantiate the conversation agent with default model + instructions."""
    return Agent(
        name="ConversationAgent",
        model=model or default_model_factory(),
        instructions=CONVERSATION_SYSTEM_PROMPT,
        markdown=False,
    )


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
