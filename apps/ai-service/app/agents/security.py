"""Agent security policy: the hard boundary between LLM and system."""

from __future__ import annotations

import logging

from app.security.injection import InjectionScanner

logger = logging.getLogger(__name__)

# Tools that a refused/injected request may NEVER trigger.
WRITE_TOOLS: set[str] = set()  # registry contains only read-only tools today

AUTH_REQUIRED_TOOLS: set[str] = {"get_order_status", "get_user_orders"}


class AgentSecurityPolicy:
    """Evaluates whether the agent may proceed with a request/action."""

    def __init__(self, scanner: InjectionScanner):
        self.scanner = scanner

    def evaluate_user_query(self, query: str) -> tuple[bool, list[str]]:
        """Refuse the whole turn when the user input looks like an attack."""
        flags = self.scanner.scan(query)
        if flags:
            logger.warning(
                "security: refusing request flagged as %s",
                ",".join(flags),
            )
        return not flags, flags

    def evaluate_tool_call(
        self, tool_name: str, auth_user_id: str | None
    ) -> tuple[bool, str | None]:
        """Enforce tool permissions regardless of what the LLM says."""
        if tool_name in AUTH_REQUIRED_TOOLS and not auth_user_id:
            return False, "tool requires an authenticated user"
        return True, None

    def evaluate_retrieved_content(self, documents: list[dict]) -> list[str]:
        """Flag injection attempts embedded in retrieved documents."""
        flags: list[str] = []
        for doc in documents:
            text = doc.get("content", "")
            hits = self.scanner.scan(text)
            flags.extend(f"doc:{doc.get('id', '?')}:{hit}" for hit in hits)
        return flags
