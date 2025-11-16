"""Factory helpers for Webank agent suite built with agno."""

from agents.common.telemetry import configure_tracing

from .pipeline import WebankAgentPipeline, build_default_pipeline
from .socio_role.builder import build_socio_role_agent
from .asset.builder import build_asset_agent
from .behavior.builder import build_behavior_agent
from .summary.builder import build_summary_agent
from .conversation import ConversationService
from .fund_advice import FundAdviceService

configure_tracing()

__all__ = [
    "WebankAgentPipeline",
    "build_default_pipeline",
    "build_socio_role_agent",
    "build_asset_agent",
    "build_behavior_agent",
    "build_summary_agent",
    "ConversationService",
    "FundAdviceService",
]
