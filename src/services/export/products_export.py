"""
Pipedrive Products Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Products
Reference Date: 2025-12-02

This module exports products data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class ProductsExport(BaseExport):
    """
    Export products data to SQLite database.

    Exports:
    - Products with pricing and details
    - Product variants
    """

    async def export(
        self,
        include_variants: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export products data to SQLite database.

        Args:
            include_variants: Whether to export product variants
            filters: Optional filters for products

        Returns:
            Export statistics and results
        """
        logger.info("Starting products export")

        # Create products table
        await self._create_products_table()

        # Fetch all products
        products_data = await self.fetch_all_paginated("/products", filters)

        if not products_data:
            logger.warning("No products found to export")
            return {"products_exported": 0, "tables_created": []}

        # Transform and insert products
        transformed_products = [
            self._transform_product(product) for product in products_data
        ]
        products_inserted = await self.bulk_insert("products", transformed_products)

        tables_created = ["products"]
        export_stats = {"products_exported": products_inserted}

        # Export variants if requested
        if include_variants:
            variants_stats = await self._export_product_variants(products_data)
            export_stats.update(variants_stats)
            tables_created.append("product_variants")

        export_stats["tables_created"] = tables_created

        logger.info(f"Products export completed: {export_stats}")
        return export_stats

    async def _create_products_table(self) -> None:
        """Create products table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "code": "TEXT",
            "unit": "TEXT",
            "tax": "REAL",
            "tax_name": "TEXT",
            "description": "TEXT",
            "visible_to": "TEXT",
            "owner_id": "INTEGER",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "selectable": "BOOLEAN DEFAULT TRUE",
            "first_char": "TEXT",
            "custom_fields": "TEXT",  # JSON string
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_products_name ON products(name)",
            "CREATE INDEX idx_products_code ON products(code)",
            "CREATE INDEX idx_products_owner_id ON products(owner_id)",
            "CREATE INDEX idx_products_active_flag ON products(active_flag)",
            "CREATE INDEX idx_products_add_time ON products(add_time)",
        ]

        await self.create_table("products", columns, indexes, drop_if_exists=True)

    def _transform_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform product data for database insertion."""
        import json

        # Extract prices from the product data
        prices = product_data.get("prices", [])
        price = prices[0] if prices else {}

        return {
            "id": product_data.get("id"),
            "name": product_data.get("name"),
            "code": product_data.get("code"),
            "unit": product_data.get("unit"),
            "tax": float(product_data.get("tax", 0))
            if product_data.get("tax")
            else None,
            "tax_name": product_data.get("tax_name"),
            "description": product_data.get("description"),
            "visible_to": product_data.get("visible_to"),
            "owner_id": product_data.get("owner_id"),
            "add_time": product_data.get("add_time"),
            "update_time": product_data.get("update_time"),
            "active_flag": product_data.get("active_flag", True),
            "selectable": product_data.get("selectable", True),
            "first_char": product_data.get("first_char"),
            "custom_fields": json.dumps(product_data.get("custom_fields", {})),
        }

    async def _export_product_variants(
        self, products_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export variants for all products."""
        await self._create_product_variants_table()

        all_variants = []
        for product in products_data:
            product_id = product.get("id")
            prices = product.get("prices", [])

            if isinstance(prices, list):
                for price in prices:
                    variant_data = {
                        "product_id": product_id,
                        "price": float(price.get("price", 0))
                        if price.get("price")
                        else None,
                        "currency": price.get("currency"),
                        "cost": float(price.get("cost", 0))
                        if price.get("cost")
                        else None,
                        "overhead_cost": float(price.get("overhead_cost", 0))
                        if price.get("overhead_cost")
                        else None,
                    }
                    all_variants.append(variant_data)

        if all_variants:
            variants_inserted = await self.bulk_insert("product_variants", all_variants)
            return {"product_variants_exported": variants_inserted}

        return {"product_variants_exported": 0}

    async def _create_product_variants_table(self) -> None:
        """Create product_variants table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "product_id": "INTEGER NOT NULL",
            "price": "REAL",
            "currency": "TEXT",
            "cost": "REAL",
            "overhead_cost": "REAL",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_product_variants_product_id ON product_variants(product_id)",
            "CREATE INDEX idx_product_variants_currency ON product_variants(currency)",
        ]

        await self.create_table("product_variants", columns, indexes)
