"""Commerce tools.

Each tool is bounded: it wraps one trusted API operation, declares its
input schema, validates arguments, handles errors, and returns a
structured ToolResult. The LLM can only call what the registry exposes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.caching.cache import CacheService
from app.config.settings import Settings
from app.security.injection import InjectionScanner
from app.tools.base import ToolAuthContext, ToolResult
from app.tools.commerce_client import CommerceClient


class SearchProductsInput(BaseModel):
    query: str = Field(description="Natural language search for product names/specs")
    category: str | None = Field(
        default=None, description="notebooks|smartphones|monitors|accessories"
    )
    brand: str | None = None
    max_price_cents: int | None = Field(default=None, ge=0)
    min_price_cents: int | None = Field(default=None, ge=0)
    limit: int = Field(default=10, ge=1, le=25)


class SearchProductsTool:
    name = "search_products"
    description = "Search the product catalog by name, specs, category, brand or price."
    input_schema = SearchProductsInput
    requires_auth = False

    def __init__(self, client: CommerceClient, cache: CacheService, settings: Settings):
        self.client = client
        self.cache = cache
        self.settings = settings

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = SearchProductsInput.model_validate(arguments)
        params = {
            "q": args.query,
            "limit": args.limit,
        }
        if args.category:
            params["category"] = args.category
        if args.brand:
            params["brand"] = args.brand
        if args.max_price_cents is not None:
            params["maxPriceCents"] = args.max_price_cents
        if args.min_price_cents is not None:
            params["minPriceCents"] = args.min_price_cents

        cache_key = f"tool:search:{sorted(params.items())}"
        cached = await self.cache.get(cache_key, self.settings.cache_search_ttl)
        if cached is not None:
            return ToolResult(ok=True, data=cached, cached=True)

        payload = await self.client.list_products(params)
        summary = [
            {
                "id": p["id"],
                "name": p["name"],
                "brand": p["brand"],
                "price_cents": p["priceCents"],
                "category": p["category"]["slug"],
            }
            for p in payload.get("items", [])
        ]
        await self.cache.set(cache_key, summary, self.settings.cache_search_ttl)
        return ToolResult(ok=True, data=summary)


class ProductDetailsInput(BaseModel):
    product_id: str = Field(description="UUID of the product")


class GetProductDetailsTool:
    name = "get_product_details"
    description = "Get full details and specifications of a product by id."
    input_schema = ProductDetailsInput
    requires_auth = False

    def __init__(self, client: CommerceClient, cache: CacheService, settings: Settings):
        self.client = client
        self.cache = cache
        self.settings = settings

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = ProductDetailsInput.model_validate(arguments)
        cache_key = f"tool:product:{args.product_id}"
        cached = await self.cache.get(cache_key, self.settings.cache_product_ttl)
        if cached is not None:
            return ToolResult(ok=True, data=cached, cached=True)

        product = await self.client.get_product(args.product_id)
        await self.cache.set(cache_key, product, self.settings.cache_product_ttl)
        return ToolResult(ok=True, data=product)


class PriceInput(BaseModel):
    product_id: str


class GetProductPriceTool:
    name = "get_product_price"
    description = "Get the current price of a product. Always prefer this over guessing."
    input_schema = PriceInput
    requires_auth = False

    def __init__(self, client: CommerceClient, cache: CacheService, settings: Settings):
        self.client = client
        self.cache = cache
        self.settings = settings

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = PriceInput.model_validate(arguments)
        cache_key = f"tool:price:{args.product_id}"
        cached = await self.cache.get(cache_key, self.settings.cache_price_ttl)
        if cached is not None:
            return ToolResult(ok=True, data=cached, cached=True)

        product = await self.client.get_product(args.product_id)
        price = {
            "product_id": product["id"],
            "name": product["name"],
            "price_cents": product["priceCents"],
            "currency": product.get("currency", "BRL"),
        }
        await self.cache.set(cache_key, price, self.settings.cache_price_ttl)
        return ToolResult(ok=True, data=price)


class InventoryInput(BaseModel):
    product_id: str


class GetInventoryTool:
    name = "get_inventory"
    description = "Get current stock availability of a product. Never cached."
    input_schema = InventoryInput
    requires_auth = False

    def __init__(self, client: CommerceClient, settings: Settings):
        self.client = client
        self.settings = settings

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = InventoryInput.model_validate(arguments)
        inventory = await self.client.get_inventory(args.product_id)
        return ToolResult(
            ok=True,
            data={
                "product_id": inventory["productId"],
                "available": inventory["available"],
                "quantity": inventory["quantity"],
                "in_stock": inventory["inStock"],
            },
        )


class CompareInput(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=3)


class CompareProductsTool:
    name = "compare_products"
    description = "Fetch full details of 2-3 products for comparison."
    input_schema = CompareInput
    requires_auth = False

    def __init__(self, client: CommerceClient, cache: CacheService, settings: Settings):
        self.client = client
        self.cache = cache
        self.settings = settings

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = CompareInput.model_validate(arguments)
        products = []
        for product_id in args.product_ids:
            cache_key = f"tool:product:{product_id}"
            product = await self.cache.get(cache_key, self.settings.cache_product_ttl)
            if product is None:
                product = await self.client.get_product(product_id)
                await self.cache.set(cache_key, product, self.settings.cache_product_ttl)
            products.append(product)
        return ToolResult(ok=True, data=products)


class OrderStatusInput(BaseModel):
    order_number: str = Field(description='Order number like "ORD-20260101-ABC123"')


class GetOrderStatusTool:
    name = "get_order_status"
    description = "Get the status of the caller's order by order number."
    input_schema = OrderStatusInput
    requires_auth = True

    def __init__(self, client: CommerceClient):
        self.client = client

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = OrderStatusInput.model_validate(arguments)
        if not auth.user_id:
            return ToolResult(ok=False, error="Authentication required to check orders.")
        # In production the AI service receives a scoped service token;
        # the backend still enforces ownership on the caller's user id.
        status = await self.client.get_order_status(args.order_number, auth.user_id)
        return ToolResult(ok=True, data=status)


class UserOrdersInput(BaseModel):
    limit: int = Field(default=5, ge=1, le=20)


class GetUserOrdersTool:
    name = "get_user_orders"
    description = "List the caller's recent orders."
    input_schema = UserOrdersInput
    requires_auth = True

    def __init__(self, client: CommerceClient):
        self.client = client

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = UserOrdersInput.model_validate(arguments)
        if not auth.user_id:
            return ToolResult(ok=False, error="Authentication required.")
        orders = await self.client.list_user_orders(auth.user_id)
        return ToolResult(ok=True, data=orders.get("orders", orders)[: args.limit])


class ShippingInput(BaseModel):
    quantity: int = Field(default=1, ge=1, le=50)
    subtotal_cents: int = Field(default=0, ge=0)


class CalculateShippingTool:
    name = "calculate_shipping"
    description = "Estimate shipping cost based on quantity and subtotal."
    input_schema = ShippingInput
    requires_auth = False

    async def execute(self, arguments: dict, auth: ToolAuthContext) -> ToolResult:
        args = ShippingInput.model_validate(arguments)
        shipping_cents = 0 if args.subtotal_cents >= 30000 else max(1500, args.quantity * 500)
        return ToolResult(
            ok=True,
            data={
                "shipping_cents": shipping_cents,
                "free_shipping": shipping_cents == 0,
                "note": "Free shipping for orders above R$300.00.",
            },
        )


def build_tool_registry(
    client: CommerceClient,
    cache: CacheService,
    settings: Settings,
    scanner: InjectionScanner,
) -> dict[str, object]:
    return {
        "search_products": SearchProductsTool(client, cache, settings),
        "get_product_details": GetProductDetailsTool(client, cache, settings),
        "get_product_price": GetProductPriceTool(client, cache, settings),
        "get_inventory": GetInventoryTool(client, settings),
        "compare_products": CompareProductsTool(client, cache, settings),
        "get_order_status": GetOrderStatusTool(client),
        "get_user_orders": GetUserOrdersTool(client),
        "calculate_shipping": CalculateShippingTool(),
    }
