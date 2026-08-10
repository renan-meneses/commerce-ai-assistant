"""HTTP client for the trusted commerce API (NestJS backend).

Tools never talk to the database directly; they call these endpoints.
The backend enforces authorization, business rules and data integrity.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class CommerceApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"commerce API error {status}: {message}")


class CommerceClient:
    """Thin async client over the commerce API."""

    def __init__(self, settings: Settings):
        self._client = httpx.AsyncClient(
            base_url=settings.api_url,
            timeout=10.0,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        user_token: str | None = None,
        retries: int = 3,
    ) -> dict:
        headers = {}
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        last_error: CommerceApiError | None = None
        for attempt in range(retries + 1):
            try:
                response = await self._client.request(
                    method, path, params=params, json=json, headers=headers
                )
            except httpx.HTTPError as exc:
                last_error = CommerceApiError(0, f"commerce API unreachable: {exc}")
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise last_error from exc
            if response.status_code >= 400:
                last_error = CommerceApiError(response.status_code, response.text[:300])
                if response.status_code in (429, 502, 503, 504) and attempt < retries:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise last_error
            return response.json()
        assert last_error is not None
        raise last_error

    async def list_products(self, params: dict) -> dict:
        return await self._request("GET", "/api/v1/products", params=params)

    async def get_product(self, product_id: str) -> dict:
        return await self._request("GET", f"/api/v1/products/{product_id}")

    async def get_inventory(self, product_id: str) -> dict:
        return await self._request("GET", f"/api/v1/products/{product_id}/inventory")

    async def get_order_status(self, number: str, user_token: str) -> dict:
        return await self._request(
            "GET",
            f"/api/v1/orders/by-number/{number}",
            user_token=user_token,
        )

    async def list_user_orders(self, user_token: str) -> dict:
        return await self._request("GET", "/api/v1/orders", user_token=user_token)

    async def close(self) -> None:
        await self._client.aclose()
