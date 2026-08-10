"""Bounded tool framework.

Tools are the ONLY way the LLM interacts with the commerce system.
- Each tool has a Pydantic input schema (validated before execution).
- Tools call trusted application APIs (the NestJS backend) via HTTP.
- No tool receives SQL access or raw database connections.
- Every tool declares required authorization; the executor enforces it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    cached: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "cached": self.cached,
            "meta": self.meta,
        }


class ToolAuthContext(BaseModel):
    """Auth context handed to a tool execution.

    `user_id` identifies the caller (used for ownership checks inside the
    AI service). `user_token` is the short-lived scoped service token that
    the API minted for this request; tools forward it to the commerce API
    so the backend can enforce authorization itself.
    """

    user_id: str | None = None
    user_token: str | None = None
    roles: list[str] = field(default_factory=list)


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    input_schema: type[BaseModel]
    requires_auth: bool = False

    async def execute(
        self,
        arguments: dict[str, Any],
        auth: ToolAuthContext,
    ) -> ToolResult: ...


class ToolExecutionError(Exception):
    """Raised when a tool cannot complete; message is safe for the LLM."""
