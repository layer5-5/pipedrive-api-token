"""
Pipedrive Organizations Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Organizations
Reference Date: 2025-12-02

This module exports organizations data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class OrganizationsExport(BaseExport):
    """
    Export organizations data to SQLite database.

    Exports:
    - Organizations with company details
    - Organization addresses
    - Organization relationships
    """

    async def export(
        self,
        include_addresses: bool = True,
        include_relationships: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export organizations data to SQLite database.

        Args:
            include_addresses: Whether to export organization addresses
            include_relationships: Whether to export organization relationships
            filters: Optional filters for organizations

        Returns:
            Export statistics and results
        """
        logger.info("Starting organizations export")

        # Create organizations table
        await self._create_organizations_table()

        # Fetch all organizations
        organizations_data = await self.fetch_all_paginated("/organizations", filters)

        if not organizations_data:
            logger.warning("No organizations found to export")
            return {"organizations_exported": 0, "tables_created": []}

        # Transform and insert organizations
        transformed_organizations = [
            self._transform_organization(org) for org in organizations_data
        ]
        organizations_inserted = await self.bulk_insert(
            "organizations", transformed_organizations
        )

        tables_created = ["organizations"]
        export_stats = {"organizations_exported": organizations_inserted}

        # Export related data
        if include_addresses:
            addresses_stats = await self._export_organization_addresses(
                organizations_data
            )
            export_stats.update(addresses_stats)
            tables_created.append("organization_addresses")

        if include_relationships:
            relationships_stats = await self._export_organization_relationships(
                organizations_data
            )
            export_stats.update(relationships_stats)
            tables_created.append("organization_relationships")

        export_stats["tables_created"] = tables_created

        logger.info(f"Organizations export completed: {export_stats}")
        return export_stats

    async def _create_organizations_table(self) -> None:
        """Create organizations table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "owner_id": "INTEGER",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "visible_to": "TEXT",
            "address": "TEXT",
            "address_subpremise": "TEXT",
            "address_street_number": "TEXT",
            "address_route": "TEXT",
            "address_sublocality": "TEXT",
            "address_locality": "TEXT",
            "address_admin_area_level_1": "TEXT",
            "address_admin_area_level_2": "TEXT",
            "address_country": "TEXT",
            "address_postal_code": "TEXT",
            "address_formatted_address": "TEXT",
            "cc_email": "TEXT",
            "people_count": "INTEGER DEFAULT 0",
            "activities_count": "INTEGER DEFAULT 0",
            "done_activities_count": "INTEGER DEFAULT 0",
            "undone_activities_count": "INTEGER DEFAULT 0",
            "files_count": "INTEGER DEFAULT 0",
            "notes_count": "INTEGER DEFAULT 0",
            "followers_count": "INTEGER DEFAULT 0",
            "email_messages_count": "INTEGER DEFAULT 0",
            "deals_count": "INTEGER DEFAULT 0",
            "won_deals_count": "INTEGER DEFAULT 0",
            "lost_deals_count": "INTEGER DEFAULT 0",
            "open_deals_count": "INTEGER DEFAULT 0",
            "related_open_deals_count": "INTEGER DEFAULT 0",
            "related_won_deals_count": "INTEGER DEFAULT 0",
            "related_lost_deals_count": "INTEGER DEFAULT 0",
            "first_char": "TEXT",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "custom_fields": "TEXT",  # JSON string
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_organizations_name ON organizations(name)",
            "CREATE INDEX idx_organizations_owner_id ON organizations(owner_id)",
            "CREATE INDEX idx_organizations_active_flag ON organizations(active_flag)",
            "CREATE INDEX idx_organizations_address_country ON organizations(address_country)",
            "CREATE INDEX idx_organizations_address_locality ON organizations(address_locality)",
            "CREATE INDEX idx_organizations_add_time ON organizations(add_time)",
        ]

        await self.create_table("organizations", columns, indexes, drop_if_exists=True)

    def _transform_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform organization data for database insertion."""
        import json

        return {
            "id": org_data.get("id"),
            "name": org_data.get("name"),
            "owner_id": org_data.get("owner_id"),
            "active_flag": org_data.get("active_flag", True),
            "visible_to": org_data.get("visible_to"),
            "address": org_data.get("address"),
            "address_subpremise": org_data.get("address_subpremise"),
            "address_street_number": org_data.get("address_street_number"),
            "address_route": org_data.get("address_route"),
            "address_sublocality": org_data.get("address_sublocality"),
            "address_locality": org_data.get("address_locality"),
            "address_admin_area_level_1": org_data.get("address_admin_area_level_1"),
            "address_admin_area_level_2": org_data.get("address_admin_area_level_2"),
            "address_country": org_data.get("address_country"),
            "address_postal_code": org_data.get("address_postal_code"),
            "address_formatted_address": org_data.get("address_formatted_address"),
            "cc_email": org_data.get("cc_email"),
            "people_count": org_data.get("people_count", 0),
            "activities_count": org_data.get("activities_count", 0),
            "done_activities_count": org_data.get("done_activities_count", 0),
            "undone_activities_count": org_data.get("undone_activities_count", 0),
            "files_count": org_data.get("files_count", 0),
            "notes_count": org_data.get("notes_count", 0),
            "followers_count": org_data.get("followers_count", 0),
            "email_messages_count": org_data.get("email_messages_count", 0),
            "deals_count": org_data.get("deals_count", 0),
            "won_deals_count": org_data.get("won_deals_count", 0),
            "lost_deals_count": org_data.get("lost_deals_count", 0),
            "open_deals_count": org_data.get("open_deals_count", 0),
            "related_open_deals_count": org_data.get("related_open_deals_count", 0),
            "related_won_deals_count": org_data.get("related_won_deals_count", 0),
            "related_lost_deals_count": org_data.get("related_lost_deals_count", 0),
            "first_char": org_data.get("first_char"),
            "add_time": org_data.get("add_time"),
            "update_time": org_data.get("update_time"),
            "custom_fields": json.dumps(org_data.get("custom_fields", {})),
        }

    async def _export_organization_addresses(
        self, organizations_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export addresses for all organizations."""
        await self._create_organization_addresses_table()

        all_addresses = []
        for org in organizations_data:
            org_id = org.get("id")

            # Extract address components
            address_data = {
                "org_id": org_id,
                "address": org.get("address"),
                "address_subpremise": org.get("address_subpremise"),
                "address_street_number": org.get("address_street_number"),
                "address_route": org.get("address_route"),
                "address_sublocality": org.get("address_sublocality"),
                "address_locality": org.get("address_locality"),
                "address_admin_area_level_1": org.get("address_admin_area_level_1"),
                "address_admin_area_level_2": org.get("address_admin_area_level_2"),
                "address_country": org.get("address_country"),
                "address_postal_code": org.get("address_postal_code"),
                "address_formatted_address": org.get("address_formatted_address"),
                "address_type": "primary",  # Default address type
            }

            # Only add if there's some address information
            if any(
                address_data[key]
                for key in address_data
                if key != "org_id" and key != "address_type"
            ):
                all_addresses.append(address_data)

        if all_addresses:
            addresses_inserted = await self.bulk_insert(
                "organization_addresses", all_addresses
            )
            return {"organization_addresses_exported": addresses_inserted}

        return {"organization_addresses_exported": 0}

    async def _create_organization_addresses_table(self) -> None:
        """Create organization_addresses table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "org_id": "INTEGER NOT NULL",
            "address": "TEXT",
            "address_subpremise": "TEXT",
            "address_street_number": "TEXT",
            "address_route": "TEXT",
            "address_sublocality": "TEXT",
            "address_locality": "TEXT",
            "address_admin_area_level_1": "TEXT",
            "address_admin_area_level_2": "TEXT",
            "address_country": "TEXT",
            "address_postal_code": "TEXT",
            "address_formatted_address": "TEXT",
            "address_type": "TEXT DEFAULT 'primary'",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_organization_addresses_org_id ON organization_addresses(org_id)",
            "CREATE INDEX idx_organization_addresses_country ON organization_addresses(address_country)",
            "CREATE INDEX idx_organization_addresses_locality ON organization_addresses(address_locality)",
        ]

        await self.create_table("organization_addresses", columns, indexes)

    async def _export_organization_relationships(
        self, organizations_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export relationships between organizations."""
        await self._create_organization_relationships_table()

        # Note: Pipedrive doesn't have direct organization relationships in the API
        # This table is prepared for future use or custom relationship tracking
        all_relationships = []

        # For now, we'll create placeholder relationships based on shared deals
        # This would require additional API calls to get deal relationships
        # For now, return empty

        if all_relationships:
            relationships_inserted = await self.bulk_insert(
                "organization_relationships", all_relationships
            )
            return {"organization_relationships_exported": relationships_inserted}

        return {"organization_relationships_exported": 0}

    async def _create_organization_relationships_table(self) -> None:
        """Create organization_relationships table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "org_id": "INTEGER NOT NULL",
            "related_org_id": "INTEGER NOT NULL",
            "relationship_type": "TEXT",
            "description": "TEXT",
            "active": "BOOLEAN DEFAULT TRUE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_organization_relationships_org_id ON organization_relationships(org_id)",
            "CREATE INDEX idx_organization_relationships_related_org_id ON organization_relationships(related_org_id)",
            "CREATE UNIQUE INDEX idx_organization_relationships_unique ON organization_relationships(org_id, related_org_id)",
        ]

        await self.create_table("organization_relationships", columns, indexes)
