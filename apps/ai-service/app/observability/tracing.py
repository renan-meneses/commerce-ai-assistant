"""OpenTelemetry tracing setup."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def init_tracing(settings: Settings) -> None:
    """Initialize the global TracerProvider with an OTLP exporter."""
    try:
        resource = Resource.create(
            {"service.name": settings.app_name, "deployment.environment": settings.environment}
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
        )
        trace.set_tracer_provider(provider)
        logger.info(
            "OpenTelemetry tracing initialized (OTLP %s)", settings.otel_exporter_otlp_endpoint
        )
    except Exception as exc:  # pragma: no cover - depends on infra state
        logger.warning("failed to init tracing: %s", exc)
