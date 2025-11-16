"""Model factories for agno agents using DashScope."""

from __future__ import annotations

import os
from typing import Callable

from agno.models.dashscope import DashScope

DefaultModelFactory = Callable[[], DashScope]


def default_model_factory() -> DashScope:
    """Return the default DashScope model configured via env vars."""
    model_id = os.getenv("AGNO_MODEL_ID", "qwen-plus")
    temperature = float(os.getenv("AGNO_TEMPERATURE", "0.3"))
    base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    api_key = os.getenv("DASHSCOPE_API_KEY")
    return DashScope(id=model_id, temperature=temperature, base_url=base_url, api_key=api_key)


def build_model_factory(model_id: str | None = None) -> DefaultModelFactory:
    """Build a factory producing DashScope models with a fixed identifier."""
    fallback_id = os.getenv("AGNO_MODEL_ID", "qwen-plus")
    resolved_model_id = model_id or fallback_id
    temperature = float(os.getenv("AGNO_TEMPERATURE", "0.3"))
    base_url = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    api_key = os.getenv("DASHSCOPE_API_KEY")

    def factory() -> DashScope:
        return DashScope(
            id=resolved_model_id,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
        )

    return factory
