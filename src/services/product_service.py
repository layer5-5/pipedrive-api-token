"""Product management service."""

import logging
from typing import List, Optional, Dict, Any

from ..client.pipedrive_client import PipedriveClient
from ..models.product import Product, ProductPrice
from ..models.common import PaginatedResponse, PaginationInfo
from ..utils.errors import PipedriveNotFoundError, PipedriveAPIError

logger = logging.getLogger(__name__)


class ProductService:
    """Product management service."""

    def __init__(self, client: PipedriveClient):
        self.client = client

    async def get_products(
        self, limit: Optional[int] = None, start: int = 0, status: Optional[str] = None
    ) -> PaginatedResponse[Product]:
        """
        Get products with optional filtering.

        Args:
            limit: Number of results to return
            start: Pagination start
            status: Filter by status (active, deleted)
        """
        params: Dict[str, Any] = {
            "start": start,
        }

        if limit:
            params["limit"] = limit
        if status:
            params["status"] = status

        response = await self.client.get("/v2/products", params=params)

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get products: {error_message}")

        products_data = response.get("data", [])
        products = [Product(**product_data) for product_data in products_data]

        # Handle pagination
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None

        return PaginatedResponse(data=products, pagination=pagination)

    async def get_product(self, product_id: int) -> Product:
        """Get single product by ID."""
        response = await self.client.get(f"/v2/products/{product_id}")

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get product: {error_message}")

        product_data = response.get("data")

        if not product_data:
            raise PipedriveNotFoundError(
                f"Product {product_id} not found", "product", product_id
            )

        return Product(**product_data)

    async def get_product_deals(
        self, product_id: int, start: int = 0, limit: int = 100
    ) -> PaginatedResponse:
        """
        Get deals that include a specific product.

        Args:
            product_id: Product ID
            start: Pagination start
            limit: Number of results to return
        """
        params: Dict[str, Any] = {
            "start": start,
            "limit": limit,
        }

        response = await self.client.get(
            f"/v2/products/{product_id}/deals", params=params
        )

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get product deals: {error_message}")

        deals_data = response.get("data", [])
        # Import here to avoid circular imports
        from ..models.deal import Deal

        deals = [Deal(**deal_data) for deal_data in deals_data]

        # Handle pagination
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None

        return PaginatedResponse(data=deals, pagination=pagination)

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """
        Search for products by name or code.

        Args:
            query: Search term to look for
            limit: Maximum number of results to return

        Returns:
            List of matching products
        """
        params: Dict[str, Any] = {
            "term": query,
            "item_type": "product",
            "limit": limit,
        }

        response = await self.client.get("/v2/itemSearch", params=params)

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to search products: {error_message}")

        # Item search returns different structure - extract product data
        search_results = response.get("data", [])
        products = []

        for result in search_results:
            if result.get("type") == "product":
                product_data = result.get("data", {})
                if product_data:
                    products.append(Product(**product_data))

        return products
