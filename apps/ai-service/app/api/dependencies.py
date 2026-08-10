"""Dependency container: wires the whole agent graph once per process."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.agents.security import AgentSecurityPolicy
from app.caching.cache import CacheService
from app.config.settings import get_settings
from app.graph.workflow import GraphDeps, build_graph
from app.llms.embeddings import build_embedding_provider
from app.llms.router import ModelRouter
from app.rag.rag import RagPipeline
from app.rag.reranking.score_reranker import SimpleScoreReranker
from app.rag.retrieval.hybrid import HybridRetriever
from app.rag.retrieval.keyword import KeywordRetriever
from app.rag.retrieval.semantic import SemanticRetriever
from app.rag.store.pgvector_store import PgVectorStore
from app.security.injection import InjectionScanner
from app.tools.commerce_client import CommerceClient
from app.tools.registry import build_tool_registry

logger = logging.getLogger(__name__)


class AgentContainer:
    """Holds long-lived dependencies and the compiled agent graph."""

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings

        self.cache = CacheService(settings)
        self.commerce = CommerceClient(settings)

        self.store = PgVectorStore(settings)
        self.embeddings = build_embedding_provider(settings)

        semantic = SemanticRetriever(self.store, self.embeddings, settings)
        keyword = KeywordRetriever(self.store)
        reranker = SimpleScoreReranker()
        self.retriever = HybridRetriever(semantic, keyword, reranker, settings)
        self.rag = RagPipeline(self.retriever, settings)

        self.scanner = InjectionScanner()
        self.security = AgentSecurityPolicy(self.scanner)
        self.router = ModelRouter(settings)

        self.tools = build_tool_registry(self.commerce, self.cache, settings, self.scanner)

        deps = GraphDeps(
            settings=settings,
            router=self.router,
            retriever=self.retriever,
            tools=self.tools,
            security=self.security,
            embeddings=self.embeddings,
        )
        self.graph = build_graph(deps)

    async def aclose(self) -> None:
        await self.cache.close()
        await self.commerce.close()
        await self.store.close()


@lru_cache
def get_container() -> AgentContainer:
    return AgentContainer()
