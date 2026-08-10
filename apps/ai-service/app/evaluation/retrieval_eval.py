"""Retrieval evaluation: does the retriever find the right products?

Metrics per question:
- recall@k: fraction of expected products found in the top-k
- category precision: does the top result match the expected category
- feature recall: fraction of expected spec keywords found across
  retrieved chunk contents

No LLM is involved — the dataset answers are checked against the
retrieved documents (product id + content).
"""

from __future__ import annotations

import re

_TOKEN_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])")


def _tokens(text: str) -> set[str]:
    text = _TOKEN_SPLIT.sub(" ", text.lower())
    return set(re.findall(r"[a-z0-9]+", text))


def _expected_products(case: dict) -> list[str]:
    return [name.lower() for name in case.get("expected_products", [])]


def _feature_found(feature: str, doc_tokens: set[str]) -> bool:
    """Feature matches when every normalized token appears in the doc."""
    return all(t in doc_tokens for t in _tokens(feature))


async def evaluate_retrieval(container, dataset: list[dict]) -> dict:
    results: list[dict] = []
    total_recall = 0.0
    total_category = 0.0
    total_feature = 0.0

    for case in dataset:
        documents = await container.rag.retrieve(case["question"], top_k=6)
        doc_text = "\n".join((d.get("content") or "") for d in documents).lower()
        doc_tokens = _tokens(doc_text)

        expected = _expected_products(case)
        if expected:
            found = sum(1 for name in expected if name in doc_text)
            recall = found / len(expected)
        else:
            recall = 1.0  # no specific product expected; don't penalize

        expected_category = case.get("expected_category")
        top_meta = (documents[0].get("metadata") or {}) if documents else {}
        category_hit = (
            1.0
            if expected_category
            and expected_category.lower() in str(top_meta.get("category", "")).lower()
            else 0.0
        )
        if not expected_category:
            category_hit = 1.0

        features = case.get("expected_features", [])
        if features:
            feature_hit = sum(1 for f in features if _feature_found(f, doc_tokens)) / len(features)
        else:
            feature_hit = 1.0

        total_recall += recall
        total_category += category_hit
        total_feature += feature_hit

        results.append(
            {
                "id": case["id"],
                "name": case["question"][:60],
                "recall": recall,
                "category_precision": category_hit,
                "feature_recall": feature_hit,
                "passed": recall >= 0.8 and category_hit >= 0.8 and feature_hit >= 0.6,
            }
        )

    n = len(dataset) or 1
    return {
        "cases": results,
        "avg_recall_at_k": total_recall / n,
        "avg_category_precision": total_category / n,
        "avg_feature_recall": total_feature / n,
        "passed_cases": sum(1 for r in results if r["passed"]),
        "total_cases": n,
    }
