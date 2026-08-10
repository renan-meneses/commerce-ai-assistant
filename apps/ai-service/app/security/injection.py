"""Prompt injection defenses.

User input and retrieved documents are untrusted data. We defend in
depth:

1. Heuristic scanning of inbound user messages for known injection
   patterns (system prompt extraction, instruction override, admin
   actions, price manipulation).
2. Prompt-level policy: the system prompt declares retrieved content is
   untrusted and must not override instructions (see prompts/templates).
3. Tool permission model: the tool registry contains only read-only
   commerce tools; even a successful injection cannot reach a write path.
4. Output validation: structured outputs are Pydantic-validated before
   use, and the response generation node re-checks for leaked prompts.
"""

from __future__ import annotations

import re

INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "ignore_instructions",
        re.compile(
            r"ignore\s+(?:all|any|previous|your)\s+(?:previous|prior|other|above|earlier)?\s*(?:instructions|rules|prompt)",
            re.I,
        ),
    ),
    (
        "reveal_prompt",
        re.compile(
            r"(reveal|show|print|disclose|give me|tell me).{0,30}(system|developer)?\s*prompt|instructions",
            re.I,
        ),
    ),
    ("ignore_system_prompt", re.compile(r"ignore.{0,20}system", re.I)),
    (
        "role_override",
        re.compile(r"you\s+are\s+now|act\s+as\s+(an?\s+)?admin|new\s+instructions", re.I),
    ),
    (
        "admin_action",
        re.compile(
            r"(change|update|set|modify|grant|remove).{0,40}(price|discount|stock|admin|permission|role)",
            re.I,
        ),
    ),
    (
        "discount_override",
        re.compile(r"\d{1,3}\s*%?\s*discount|lower\s+the\s+price|free\s+product", re.I),
    ),
    (
        "sql_injection",
        re.compile(
            r"(union\s+select|drop\s+table|insert\s+into|delete\s+from|--\s|;\s*drop)", re.I
        ),
    ),
    ("tool_abuse", re.compile(r"call.{0,20}(admin|internal|execute|run|shell)", re.I)),
]

REFUSAL_CATEGORY = "REFUSED"


class InjectionScanner:
    """Detects injection attempts in untrusted text."""

    def __init__(self, patterns: list[tuple[str, re.Pattern]] | None = None):
        self.patterns = patterns or INJECTION_PATTERNS

    def scan(self, text: str) -> list[str]:
        """Return the list of matched threat categories (empty if clean)."""
        matches: list[str] = []
        for name, pattern in self.patterns:
            if pattern.search(text):
                matches.append(name)
        return matches

    def is_suspicious(self, text: str) -> bool:
        return bool(self.scan(text))

    def sanitize_for_logging(self, text: str) -> str:
        """Keep logs safe: truncate and strip tokens."""
        from app.security.masking import mask_sensitive

        return mask_sensitive(text)[:200]
