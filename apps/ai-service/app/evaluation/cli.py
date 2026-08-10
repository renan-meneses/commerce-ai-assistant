"""Evaluation CLI: `python -m app.evaluation.cli [--suite rag|agent]`.

Generates a markdown report under evaluation/reports/.
Requires indexed data (vectors) for retrieval eval and mocks-free
behavioral assertions for the agent (no external LLM calls).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[4]
# parents: cli.py -> evaluation -> app -> ai-service -> repo root
DATASETS_DIR = REPO_ROOT / "evaluation" / "datasets"
REPORTS_DIR = REPO_ROOT / "evaluation" / "reports"


def load_dataset(name: str) -> list[dict]:
    path = DATASETS_DIR / name
    with path.open() as fh:
        return json.load(fh)


async def run_rag_eval(container) -> dict:
    """Retrieval-only evaluation: precision/recall against expected products/features."""
    from app.evaluation.retrieval_eval import evaluate_retrieval

    dataset = load_dataset("rag_questions.json")
    return await evaluate_retrieval(container, dataset)


async def run_behavioral_eval(container) -> dict:
    """Behavioral evaluation without LLM calls: intent + tool + security checks."""
    from app.evaluation.behavioral_eval import evaluate_behavioral

    dataset = load_dataset("behavioral_cases.json")
    return await evaluate_behavioral(container, dataset)


async def main(suite: str | None) -> None:
    from app.api.dependencies import AgentContainer

    container = AgentContainer()
    results: dict = {"generated_at": datetime.now(UTC).isoformat(), "suites": {}}

    try:
        if suite in (None, "rag"):
            results["suites"]["rag"] = await run_rag_eval(container)
        if suite in (None, "agent"):
            results["suites"]["agent"] = await run_behavioral_eval(container)
    finally:
        await container.aclose()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"evaluation-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    report = render_report(results)
    report_path.write_text(report)
    print(report)
    print(f"\nReport written to {report_path}")


def render_report(results: dict) -> str:
    lines = ["# AI Evaluation Report", "", f"Generated: {results['generated_at']}", ""]
    for suite_name, suite in results.get("suites", {}).items():
        lines.append(f"## {suite_name}")
        lines.append("")
        for key, value in suite.items():
            if key in ("cases",):
                continue
            if isinstance(value, float):
                value = f"{value:.3f}"
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    lines.append("## Case details")
    lines.append("")
    for suite_name, suite in results.get("suites", {}).items():
        for case in suite.get("cases", []):
            status = "PASS" if case.get("passed") else "FAIL"
            lines.append(f"- [{status}] {suite_name} / {case.get('id')}: {case.get('name', '')}")
            if not case.get("passed"):
                lines.append(f"  - details: {case.get('details', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI evaluation suites")
    parser.add_argument("--suite", choices=["rag", "agent"], default=None)
    args = parser.parse_args()
    asyncio.run(main(args.suite))
