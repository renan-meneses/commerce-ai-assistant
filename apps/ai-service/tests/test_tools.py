"""Unit tests for the commerce client and the tool registry."""

import httpx
import pytest
import respx

from app.caching.cache import CacheService
from app.config.settings import Settings
from app.security.injection import InjectionScanner
from app.tools.base import ToolAuthContext
from app.tools.commerce_client import CommerceApiError, CommerceClient
from app.tools.registry import build_tool_registry


def _registry() -> dict[str, object]:
    settings = Settings()
    client = CommerceClient(settings)
    cache = CacheService(settings)
    scanner = InjectionScanner()
    return build_tool_registry(client, cache, settings, scanner)


@pytest.mark.asyncio
@respx.mock
async def test_commerce_client_retries_on_429():
    settings = Settings(api_url="http://commerce.test")
    client = CommerceClient(settings)
    respx.get("http://commerce.test/api/v1/products/p1").mock(
        side_effect=[
            httpx.Response(429, json={"statusCode": 429}),
            httpx.Response(200, json={"id": "p1", "name": "Product"}),
        ]
    )
    try:
        payload = await client.get_product("p1")
        assert payload["id"] == "p1"
        assert respx.calls.call_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_commerce_client_surfaces_4xx_errors():
    settings = Settings(api_url="http://commerce.test")
    client = CommerceClient(settings)
    respx.get("http://commerce.test/api/v1/products/p1").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    try:
        with pytest.raises(CommerceApiError) as exc:
            await client.get_product("p1")
        assert exc.value.status == 404
    finally:
        await client.close()


def test_registry_contains_expected_tools():
    registry = _registry()
    names = set(registry.keys())
    assert {
        "search_products",
        "get_product_details",
        "get_product_price",
        "get_inventory",
        "compare_products",
        "get_order_status",
        "get_user_orders",
        "calculate_shipping",
    } == names


def test_private_tools_declare_auth_requirement():
    registry = _registry()
    assert registry["get_order_status"].requires_auth is True
    assert registry["get_user_orders"].requires_auth is True
    assert registry["search_products"].requires_auth is False


def test_tool_auth_context():
    ctx = ToolAuthContext(user_id="u1")
    assert ctx.user_id == "u1"
    assert ctx.roles == []
