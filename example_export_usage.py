"""Example usage of the SQLite export functionality."""

import asyncio
import logging
from pathlib import Path

from src.client.pipedrive_client import PipedriveClient
from src.services.export import ExportManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example of using the export functionality."""

    # Initialize Pipedrive client
    api_token = "your_api_token_here"  # Replace with actual token
    client = PipedriveClient(api_token)

    # Define database path
    db_path = Path("pipedrive_export.sqlite")

    # Initialize export manager
    async with ExportManager(client, db_path) as export_manager:
        # Add progress callback
        def progress_callback(progress_info):
            table = progress_info["table_name"]
            current = progress_info["current"]
            total = progress_info["total"]
            percentage = progress_info["percentage"]
            message = progress_info["message"]

            if total:
                logger.info(
                    f"{table}: {current}/{total} ({percentage:.1f}%) - {message}"
                )
            else:
                logger.info(f"{table}: {current} - {message}")

        export_manager.add_progress_callback(progress_callback)

        # Export all data
        logger.info("Starting comprehensive export...")

        result = await export_manager.export_all(
            include_deals=True,
            include_users=True,
            include_contacts=True,
            include_pipelines=True,
            include_activities=True,
            include_products=True,
            include_organizations=True,
            # Deal-specific options
            deals_options={
                "include_activities": True,
                "include_notes": True,
                "include_products": True,
                "include_files": True,
                "include_followers": True,
                "include_participants": True,
            },
            # User-specific options
            users_options={
                "include_roles": True,
            },
            # Contact-specific options
            contacts_options={
                "include_emails": True,
                "include_phones": True,
                "include_organizations": True,
            },
            # Pipeline-specific options
            pipelines_options={
                "include_stages": True,
            },
            # Activity-specific options
            activities_options={
                "include_participants": True,
            },
            # Product-specific options
            products_options={
                "include_variants": True,
            },
            # Organization-specific options
            organizations_options={
                "include_addresses": True,
                "include_relationships": True,
            },
        )

        # Print results
        logger.info("Export completed!")
        logger.info(f"Database path: {result['database_path']}")
        logger.info(
            f"Total records exported: {result['final_statistics']['total_records_exported']}"
        )
        logger.info(
            f"Database size: {result['final_statistics']['database_size_mb']} MB"
        )

        # Print per-table statistics
        for table, stats in result["final_statistics"]["table_statistics"].items():
            if isinstance(stats, dict) and "record_count" in stats:
                logger.info(f"{table}: {stats['record_count']} records")

        # Print individual export results
        for export_type, export_result in result["export_results"].items():
            if "error" in export_result:
                logger.error(f"{export_type} export failed: {export_result['error']}")
            elif "skipped" in export_result:
                logger.info(f"{export_type} export was skipped")
            else:
                logger.info(f"{export_type} export succeeded")


async def export_specific_data():
    """Example of exporting specific data types."""

    api_token = "your_api_token_here"  # Replace with actual token
    client = PipedriveClient(api_token)
    db_path = Path("pipedrive_deals_only.sqlite")

    async with ExportManager(client, db_path) as export_manager:
        # Export only deals with related data
        result = await export_manager.export_deals(
            include_activities=True,
            include_notes=True,
            include_products=True,
            include_files=False,  # Skip files to save space
            include_followers=True,
            include_participants=True,
            filters={
                "status": "open",  # Only open deals
                "limit": 1000,  # Limit to 1000 deals
            },
        )

        logger.info(f"Deals export result: {result}")


if __name__ == "__main__":
    # Run the comprehensive export example
    asyncio.run(main())

    # Or run specific export example
    # asyncio.run(export_specific_data())
