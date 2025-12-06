"""
Pipedrive Pipelines Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Pipelines
- Related APIs: https://developers.pipedrive.com/docs/api/v1/Stages
Reference Date: 2025-12-02

This module exports pipelines data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class PipelinesExport(BaseExport):
    """
    Export pipelines data to SQLite database.

    Exports:
    - Pipelines with stages
    - Pipeline stages
    """

    async def export(
        self,
        include_stages: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export pipelines data to SQLite database.

        Args:
            include_stages: Whether to export pipeline stages
            filters: Optional filters for pipelines

        Returns:
            Export statistics and results
        """
        logger.info("Starting pipelines export")

        # Create pipelines table
        await self._create_pipelines_table()

        # Fetch all pipelines
        pipelines_data = await self.fetch_all_paginated("/pipelines", filters)

        if not pipelines_data:
            logger.warning("No pipelines found to export")
            return {"pipelines_exported": 0, "tables_created": []}

        # Transform and insert pipelines
        transformed_pipelines = [
            self._transform_pipeline(pipeline) for pipeline in pipelines_data
        ]
        pipelines_inserted = await self.bulk_insert("pipelines", transformed_pipelines)

        tables_created = ["pipelines"]
        export_stats = {"pipelines_exported": pipelines_inserted}

        # Export stages if requested
        if include_stages:
            stages_stats = await self._export_pipeline_stages(pipelines_data)
            export_stats.update(stages_stats)
            tables_created.append("pipeline_stages")

        export_stats["tables_created"] = tables_created

        logger.info(f"Pipelines export completed: {export_stats}")
        return export_stats

    async def _create_pipelines_table(self) -> None:
        """Create pipelines table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "url_title": "TEXT",
            "active": "BOOLEAN DEFAULT TRUE",
            "deal_probability": "BOOLEAN DEFAULT FALSE",
            "order_nr": "INTEGER",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_pipelines_name ON pipelines(name)",
            "CREATE INDEX idx_pipelines_active ON pipelines(active)",
            "CREATE INDEX idx_pipelines_order_nr ON pipelines(order_nr)",
        ]

        await self.create_table("pipelines", columns, indexes, drop_if_exists=True)

    def _transform_pipeline(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pipeline data for database insertion."""
        return {
            "id": pipeline_data.get("id"),
            "name": pipeline_data.get("name"),
            "url_title": pipeline_data.get("url_title"),
            "active": pipeline_data.get("active", True),
            "deal_probability": pipeline_data.get("deal_probability", False),
            "order_nr": pipeline_data.get("order_nr"),
            "add_time": pipeline_data.get("add_time"),
            "update_time": pipeline_data.get("update_time"),
        }

    async def _export_pipeline_stages(
        self, pipelines_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export stages for all pipelines."""
        await self._create_pipeline_stages_table()

        all_stages = []
        for pipeline in pipelines_data:
            pipeline_id = pipeline.get("id")
            try:
                response = await self.client.get(f"/pipelines/{pipeline_id}/stages")
                stages = response.get("data", [])

                for stage in stages:
                    stage["pipeline_id"] = pipeline_id
                    all_stages.append(stage)

            except Exception as e:
                logger.warning(
                    f"Failed to fetch stages for pipeline {pipeline_id}: {e}"
                )

        if all_stages:
            transformed_stages = [self._transform_stage(stage) for stage in all_stages]
            stages_inserted = await self.bulk_insert(
                "pipeline_stages", transformed_stages
            )
            return {"pipeline_stages_exported": stages_inserted}

        return {"pipeline_stages_exported": 0}

    async def _create_pipeline_stages_table(self) -> None:
        """Create pipeline_stages table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "pipeline_id": "INTEGER NOT NULL",
            "name": "TEXT NOT NULL",
            "order_nr": "INTEGER",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "deal_probability": "INTEGER",
            "rotten_flag": "BOOLEAN DEFAULT FALSE",
            "rotten_days": "INTEGER",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_pipeline_stages_pipeline_id ON pipeline_stages(pipeline_id)",
            "CREATE INDEX idx_pipeline_stages_name ON pipeline_stages(name)",
            "CREATE INDEX idx_pipeline_stages_order_nr ON pipeline_stages(order_nr)",
            "CREATE INDEX idx_pipeline_stages_active_flag ON pipeline_stages(active_flag)",
        ]

        await self.create_table("pipeline_stages", columns, indexes)

    def _transform_stage(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform stage data for database insertion."""
        return {
            "id": stage_data.get("id"),
            "pipeline_id": stage_data.get("pipeline_id"),
            "name": stage_data.get("name"),
            "order_nr": stage_data.get("order_nr"),
            "active_flag": stage_data.get("active_flag", True),
            "deal_probability": stage_data.get("deal_probability"),
            "rotten_flag": stage_data.get("rotten_flag", False),
            "rotten_days": stage_data.get("rotten_days"),
            "add_time": stage_data.get("add_time"),
            "update_time": stage_data.get("update_time"),
        }
