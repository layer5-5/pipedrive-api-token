"""Export manager for coordinating all SQLite export operations."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base_export import BaseExport
from .deals_export import DealsExport
from .users_export import UsersExport
from .contacts_export import ContactsExport
from .pipelines_export import PipelinesExport
from .activities_export import ActivitiesExport
from .products_export import ProductsExport
from .organizations_export import OrganizationsExport
from ...client.pipedrive_client import PipedriveClient

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Main export manager for coordinating all SQLite export operations.

    Provides a unified interface for exporting all Pipedrive data types
    to a SQLite database with proper relationships and progress tracking.
    """

    def __init__(self, client: PipedriveClient, db_path: Union[str, Path]):
        """
        Initialize export manager.

        Args:
            client: Pipedrive API client
            db_path: Path to SQLite database file
        """
        self.client = client
        self.db_path = Path(db_path)

        # Initialize export modules
        self.deals_export = DealsExport(client, db_path)
        self.users_export = UsersExport(client, db_path)
        self.contacts_export = ContactsExport(client, db_path)
        self.pipelines_export = PipelinesExport(client, db_path)
        self.activities_export = ActivitiesExport(client, db_path)
        self.products_export = ProductsExport(client, db_path)
        self.organizations_export = OrganizationsExport(client, db_path)

        logger.info(f"ExportManager initialized with database: {db_path}")

    async def export_all(
        self,
        include_deals: bool = True,
        include_users: bool = True,
        include_contacts: bool = True,
        include_pipelines: bool = True,
        include_activities: bool = True,
        include_products: bool = True,
        include_organizations: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Export all data types to SQLite database.

        Args:
            include_deals: Whether to export deals
            include_users: Whether to export users
            include_contacts: Whether to export contacts
            include_pipelines: Whether to export pipelines
            include_activities: Whether to export activities
            include_products: Whether to export products
            include_organizations: Whether to export organizations
            **kwargs: Additional export options for specific modules

        Returns:
            Comprehensive export statistics
        """
        logger.info("Starting comprehensive export of all data types")

        export_results = {}

        # Export in logical order to respect dependencies
        export_order = [
            ("users", self.users_export, include_users),
            ("pipelines", self.pipelines_export, include_pipelines),
            ("organizations", self.organizations_export, include_organizations),
            ("contacts", self.contacts_export, include_contacts),
            ("products", self.products_export, include_products),
            ("activities", self.activities_export, include_activities),
            ("deals", self.deals_export, include_deals),
        ]

        for export_name, export_module, should_export in export_order:
            if should_export:
                try:
                    logger.info(f"Exporting {export_name}...")
                    result = await export_module.export(
                        **kwargs.get(f"{export_name}_options", {})
                    )
                    export_results[export_name] = result
                    logger.info(f"Successfully exported {export_name}: {result}")
                except Exception as e:
                    logger.error(f"Failed to export {export_name}: {e}")
                    export_results[export_name] = {"error": str(e), "exported": 0}
            else:
                logger.info(f"Skipping {export_name} export")
                export_results[export_name] = {"skipped": True}

        # Get final statistics
        final_stats = await self.get_export_statistics()

        comprehensive_result = {
            "export_results": export_results,
            "final_statistics": final_stats,
            "database_path": str(self.db_path),
            "export_completed": True,
        }

        logger.info(f"Comprehensive export completed: {comprehensive_result}")
        return comprehensive_result

    async def export_deals(self, **kwargs) -> Dict[str, Any]:
        """Export deals data."""
        return await self.deals_export.export(**kwargs)

    async def export_users(self, **kwargs) -> Dict[str, Any]:
        """Export users data."""
        return await self.users_export.export(**kwargs)

    async def export_contacts(self, **kwargs) -> Dict[str, Any]:
        """Export contacts data."""
        return await self.contacts_export.export(**kwargs)

    async def export_pipelines(self, **kwargs) -> Dict[str, Any]:
        """Export pipelines data."""
        return await self.pipelines_export.export(**kwargs)

    async def export_activities(self, **kwargs) -> Dict[str, Any]:
        """Export activities data."""
        return await self.activities_export.export(**kwargs)

    async def export_products(self, **kwargs) -> Dict[str, Any]:
        """Export products data."""
        return await self.products_export.export(**kwargs)

    async def export_organizations(self, **kwargs) -> Dict[str, Any]:
        """Export organizations data."""
        return await self.organizations_export.export(**kwargs)

    async def get_export_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about exported data.

        Returns:
            Dictionary with table statistics and summary
        """
        all_stats = {}
        total_records = 0

        # Get stats from all export modules
        export_modules = [
            self.deals_export,
            self.users_export,
            self.contacts_export,
            self.pipelines_export,
            self.activities_export,
            self.products_export,
            self.organizations_export,
        ]

        for module in export_modules:
            try:
                stats = await module.get_export_stats()
                all_stats.update(stats)

                # Count total records
                for table_info in stats.values():
                    if isinstance(table_info, dict) and "record_count" in table_info:
                        total_records += table_info["record_count"]
            except Exception as e:
                logger.warning(
                    f"Failed to get statistics from {module.__class__.__name__}: {e}"
                )

        return {
            "table_statistics": all_stats,
            "total_records_exported": total_records,
            "database_path": str(self.db_path),
            "database_size_mb": self._get_database_size_mb(),
        }

    def _get_database_size_mb(self) -> float:
        """Get database file size in MB."""
        try:
            if self.db_path.exists():
                size_bytes = self.db_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.warning(f"Failed to get database size: {e}")
        return 0.0

    def add_progress_callback(self, callback) -> None:
        """
        Add progress callback to all export modules.

        Args:
            callback: Progress callback function
        """
        export_modules = [
            self.deals_export,
            self.users_export,
            self.contacts_export,
            self.pipelines_export,
            self.activities_export,
            self.products_export,
            self.organizations_export,
        ]

        for module in export_modules:
            module.add_progress_callback(callback)

    async def close_all_connections(self) -> None:
        """Close all database connections."""
        export_modules = [
            self.deals_export,
            self.users_export,
            self.contacts_export,
            self.pipelines_export,
            self.activities_export,
            self.products_export,
            self.organizations_export,
        ]

        for module in export_modules:
            try:
                await module.close()
            except Exception as e:
                logger.warning(
                    f"Failed to close connection for {module.__class__.__name__}: {e}"
                )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all_connections()
