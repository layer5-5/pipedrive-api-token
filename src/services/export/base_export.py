"""
Pipedrive Base Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/
Reference Date: 2025-12-02

This module provides base functionality for exporting Pipedrive API data to SQLite database.
"""

import logging
import sqlite3
import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Callable
import aiosqlite

from ...client.pipedrive_client import PipedriveClient
from ...utils.errors import PipedriveAPIError

logger = logging.getLogger(__name__)


class BaseExport(ABC):
    """
    Base class for all SQLite export operations.

    Provides common functionality for:
    - Database connection management
    - Table creation utilities
    - Data insertion methods
    - Error handling
    - Progress tracking
    - Transaction management
    """

    def __init__(self, client: PipedriveClient, db_path: Union[str, Path]):
        """
        Initialize base export class.

        Args:
            client: Pipedrive API client
            db_path: Path to SQLite database file
        """
        self.client = client
        self.db_path = Path(db_path)
        self._connection: Optional[aiosqlite.Connection] = None
        self._progress_callbacks: List[Callable] = []

        logger.info(
            f"Initialized {self.__class__.__name__} with database: {self.db_path}"
        )

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Get database connection with proper cleanup.

        Yields:
            Database connection
        """
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create connection
            self._connection = await aiosqlite.connect(self.db_path)

            # Enable foreign keys
            await self._connection.execute("PRAGMA foreign_keys = ON")

            # Set row factory for dict-like access
            self._connection.row_factory = aiosqlite.Row

            logger.debug(f"Database connection established: {self.db_path}")
            yield self._connection

        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if self._connection:
                await self._connection.close()
                self._connection = None
                logger.debug("Database connection closed")

    async def create_table(
        self,
        table_name: str,
        columns: Dict[str, str],
        indexes: Optional[List[str]] = None,
        drop_if_exists: bool = False,
    ) -> None:
        """
        Create a table with specified columns and indexes.

        Args:
            table_name: Name of the table
            columns: Dictionary of column names and their SQL definitions
            indexes: List of index definitions
            drop_if_exists: Whether to drop table if it exists
        """
        async with self.get_connection() as conn:
            # Drop table if requested
            if drop_if_exists:
                await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(f"Dropped existing table: {table_name}")

            # Build CREATE TABLE statement
            column_defs = [
                f"{name} {definition}" for name, definition in columns.items()
            ]
            create_sql = (
                f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            )

            await conn.execute(create_sql)
            logger.info(f"Created table: {table_name}")

            # Create indexes
            if indexes:
                for index_sql in indexes:
                    await conn.execute(index_sql)
                    logger.debug(f"Created index for table: {table_name}")

            await conn.commit()

    async def bulk_insert(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000,
        on_conflict: Optional[str] = None,
    ) -> int:
        """
        Bulk insert data into table with batching.

        Args:
            table_name: Name of the table
            data: List of data dictionaries
            batch_size: Number of records per batch
            on_conflict: Conflict resolution strategy (e.g., "REPLACE", "IGNORE")

        Returns:
            Total number of records inserted
        """
        if not data:
            return 0

        async with self.get_connection() as conn:
            total_inserted = 0

            # Get column names from first record
            columns = list(data[0].keys())
            placeholders = ", ".join(["?" for _ in columns])

            # Build INSERT statement
            conflict_clause = f" OR {on_conflict}" if on_conflict else ""
            insert_sql = f"INSERT{conflict_clause} INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                values = [[record.get(col) for col in columns] for record in batch]

                await conn.executemany(insert_sql, values)
                await conn.commit()

                batch_inserted = len(batch)
                total_inserted += batch_inserted

                # Report progress
                await self._report_progress(
                    table_name,
                    total_inserted,
                    len(data),
                    f"Inserted {batch_inserted} records",
                )

                logger.debug(
                    f"Inserted batch of {batch_inserted} records into {table_name}"
                )

            logger.info(
                f"Bulk insert completed: {total_inserted} records into {table_name}"
            )
            return total_inserted

    async def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[aiosqlite.Row]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result rows
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params or ())
            return list(await cursor.fetchall())

    async def get_record_count(self, table_name: str) -> int:
        """
        Get total record count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Record count
        """
        result = await self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]["count"] if result else 0

    def add_progress_callback(self, callback: Callable) -> None:
        """
        Add a progress callback function.

        Args:
            callback: Function that receives (table_name, current, total, message)
        """
        self._progress_callbacks.append(callback)

    async def _report_progress(
        self, table_name: str, current: int, total: Optional[int], message: str = ""
    ) -> None:
        """
        Report progress to all registered callbacks.

        Args:
            table_name: Name of the table being processed
            current: Current progress count
            total: Total count
            message: Progress message
        """
        progress_info = {
            "table_name": table_name,
            "current": current,
            "total": total,
            "percentage": (current / total * 100) if total and total > 0 else 0,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress_info)
                else:
                    callback(progress_info)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def fetch_all_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 500,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all data from a paginated endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch

        Returns:
            List of all items
        """
        all_data = []
        start = 0
        page_count = 0

        if params is None:
            params = {}

        params["limit"] = page_size

        while True:
            if max_pages and page_count >= max_pages:
                break

            params["start"] = start

            try:
                response = await self.client.get(endpoint, params=params)
                data = response.get("data", [])

                if not data:
                    break

                all_data.extend(data)

                # Report progress
                await self._report_progress(
                    endpoint,
                    len(all_data),
                    None,
                    f"Fetched page {page_count + 1} ({len(data)} items)",
                )

                # Check if there are more items
                additional_data = response.get("additional_data", {})
                pagination = additional_data.get("pagination", {})

                if not pagination.get("more_items_in_collection", False):
                    break

                start = pagination.get("next_start", start + page_size)
                page_count += 1

            except PipedriveAPIError as e:
                logger.error(f"Error fetching page {page_count} from {endpoint}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching from {endpoint}: {e}")
                break

        logger.info(f"Fetched {len(all_data)} total items from {endpoint}")
        return all_data

    @abstractmethod
    async def export(self, **kwargs) -> Dict[str, Any]:
        """
        Export data to SQLite database.

        Args:
            **kwargs: Export-specific parameters

        Returns:
            Export statistics and results
        """
        pass

    async def get_export_stats(self) -> Dict[str, Any]:
        """
        Get statistics about exported data.

        Returns:
            Dictionary with table statistics
        """
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]

            stats = {}
            for table in tables:
                count = await self.get_record_count(table)
                stats[table] = {"record_count": count}

            return stats

    async def close(self) -> None:
        """Close any open connections."""
        if self._connection:
            await self._connection.close()
            self._connection = None
