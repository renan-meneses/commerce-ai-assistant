"""FastAPI application for the AI service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.config.settings import get_settings
from app.observability.tracing import init_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.tracing_enabled:
        init_tracing(settings)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="commerce-ai-assistant AI Service",
        version="0.1.0",
        description=(
            "RAG + LangGraph agent backend for the commerce assistant. "
            "Knowledge questions go through hybrid retrieval (pgvector + FTS); "
            "real-time questions (price, stock, orders) call bounded commerce tools."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
