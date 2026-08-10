"""Unit tests for hybrid retrieval fusion and reranking."""

from app.rag.reranking.score_reranker import SimpleScoreReranker
from app.rag.retrieval.fusion import reciprocal_rank_fusion, weighted_score_fusion


def _item(doc_id: str, score: float, category: str = "Notebooks") -> dict:
    return {
        "id": doc_id,
        "product_id": doc_id,
        "content": f"content {doc_id}",
        "metadata": {"category": category, "price_cents": 489900},
        "score": score,
    }


def test_rrf_merges_and_ranks():
    semantic = [_item("a", 0.9), _item("b", 0.8), _item("c", 0.7)]
    keyword = [_item("b", 0.4), _item("a", 0.3)]
    fused = reciprocal_rank_fusion([semantic, keyword])
    ids = [d["id"] for d in fused]
    assert ids[0] in ("a", "b")
    assert set(ids) == {"a", "b", "c"}
    assert fused[0]["sources"]  # provenance retained


def test_weighted_fusion_honors_weights():
    semantic = [_item("a", 1.0), _item("b", 0.9)]
    keyword = [_item("b", 0.2)]
    fused = weighted_score_fusion([semantic, keyword], weights=[1.0, 0.0])
    assert fused[0]["id"] == "a"


def test_reranker_keeps_order_for_equal_signals():
    items = [_item("a", 0.5, category="Acessórios"), _item("b", 0.6)]
    reranker = SimpleScoreReranker()
    import asyncio

    ranked = asyncio.run(reranker.rerank_dicts("query", items))
    assert ranked[0]["id"] == "b"
