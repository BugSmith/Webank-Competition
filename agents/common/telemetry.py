"""Shared OpenTelemetry helpers for Webank agents."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Dict, Iterator, Optional

try:  # pragma: no cover - optional dependency guard
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover - keep runtime lenient
    trace = None  # type: ignore
    Resource = None  # type: ignore
    TracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore
    OTLPSpanExporter = None  # type: ignore
    _OTEL_AVAILABLE = False


LOGGER = logging.getLogger(__name__)
_TRACE_NAMESPACE = "webank.agents"
_DEFAULT_LANGSMITH_ENDPOINT = "https://api.smith.langchain.com/otel/v1/traces"
_ENABLE_FLAG = "WEBANK_ENABLE_OTEL"


def _parse_bool(value: str | None) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _should_enable() -> bool:
    flag = _parse_bool(os.getenv(_ENABLE_FLAG))
    if flag is not None:
        return flag
    if os.getenv("LANGSMITH_API_KEY"):
        return True
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return True
    return False


def _parse_header_string(raw_headers: str | None) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if not raw_headers:
        return headers
    for chunk in raw_headers.split(","):
        if not chunk.strip():
            continue
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        headers[key.strip()] = value.strip()
    return headers


def _build_headers() -> Dict[str, str]:
    headers = _parse_header_string(os.getenv("OTEL_EXPORTER_OTLP_HEADERS"))
    api_key = os.getenv("LANGSMITH_API_KEY")
    if api_key:
        headers.setdefault("x-api-key", api_key.strip())
    project = os.getenv("LANGSMITH_PROJECT")
    if project:
        headers.setdefault("x-langsmith-project", project.strip())
    return headers


@lru_cache(maxsize=1)
def configure_tracing() -> bool:
    """Configure OpenTelemetry once for LangSmith if enabled."""

    if not _OTEL_AVAILABLE:
        LOGGER.debug("OpenTelemetry dependencies missing; tracing disabled.")
        return False

    if not _should_enable():
        return False

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", _DEFAULT_LANGSMITH_ENDPOINT)
    headers = _build_headers()

    if endpoint == _DEFAULT_LANGSMITH_ENDPOINT and "x-api-key" not in headers:
        LOGGER.warning(
            "LangSmith tracing requested but LANGSMITH_API_KEY is not set; skipping exporter setup.",
        )
        return False

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "webank-agents"),
            "service.namespace": os.getenv("OTEL_SERVICE_NAMESPACE", "webank"),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
    tracer_provider.add_span_processor(span_processor)

    try:
        trace.set_tracer_provider(tracer_provider)
    except RuntimeError:
        current_provider = trace.get_tracer_provider()
        if isinstance(current_provider, TracerProvider):  # type: ignore[arg-type]
            current_provider.add_span_processor(span_processor)
        else:
            LOGGER.debug("Tracer provider already configured and not SDK-based; skipping override.")
            return False

    LOGGER.info("OpenTelemetry tracing configured for LangSmith exporter at %s", endpoint)
    return True


def is_tracing_enabled() -> bool:
    """Expose ON/OFF state for callers that want to add metadata conditionally."""

    return configure_tracing()


@contextmanager
def trace_agent_span(
    name: str, attributes: Optional[Dict[str, Any]] = None
) -> Iterator[Any]:
    """Context manager that records a span around an agent action."""

    if trace is None:
        yield None
        return

    # Attempt lazy configuration (safe even if already configured elsewhere).
    configure_tracing()

    tracer = trace.get_tracer(_TRACE_NAMESPACE)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                if value is None:
                    continue
                span.set_attribute(key, value)
        yield span
