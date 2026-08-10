"""Result fusion for hybrid retrieval.

Two strategies:
- Reciprocal Rank Fusion (RRF): rank-based, robust across score scales.
- Weighted score fusion: normalized score sum with tunable weights.

RRF is the default because semantic (cosine) and lexical (ts_rank)
scores are not directly comparable.
"""

from __future__ import annotations

from typing import Any


def reciprocal_rank_fusion(
    result_sets: list[list[dict[str, Any]]],
    *,
    k: int = 60,
) -> list[dict[str, Any]]:
    """Fuse ranked lists by reciprocal rank.

    score(d) = sum over lists of 1/(k + rank(d))
    """
    fused: dict[str, dict[str, Any]] = {}
    for result_set in result_sets:
        for rank, item in enumerate(result_set, start=1):
            doc_id = item["id"]
            if doc_id not in fused:
                fused[doc_id] = {
                    **item,
                    "fusion_score": 0.0,
                    "sources": [],
                }
            fused[doc_id]["fusion_score"] += 1.0 / (k + rank)
            fused[doc_id]["sources"].append(item)
    ranked = sorted(
        fused.values(),
        key=lambda d: d["fusion_score"],
        reverse=True,
    )
    return ranked


def weighted_score_fusion(
    result_sets: list[list[dict[str, Any]]],
    *,
    weights: list[float] | None = None,
    top_k: int = 6,
) -> list[dict[str, Any]]:
    """Normalize each list's scores to [0,1] and fuse with weights."""
    if weights is None:
        weights = [1.0 / len(result_sets)] * len(result_sets)
    fused: dict[str, dict[str, Any]] = {}
    for weight, result_set in zip(weights, result_sets, strict=True):
        scores = [float(r.get("score", 0.0)) for r in result_set]
        max_score = max(scores, default=1.0)
        if max_score <= 0:
            max_score = 1.0
        for item, raw_score in zip(result_set, scores, strict=True):
            doc_id = item["id"]
            if doc_id not in fused:
                fused[doc_id] = {**item, "fusion_score": 0.0, "sources": []}
            fused[doc_id]["fusion_score"] += weight * (raw_score / max_score)
            fused[doc_id]["sources"].append(item)
    ranked = sorted(fused.values(), key=lambda d: d["fusion_score"], reverse=True)
    return ranked[:top_k]
