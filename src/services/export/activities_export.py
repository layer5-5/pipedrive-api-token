"""
Pipedrive Activities Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Activities
Reference Date: 2025-12-02

This module exports activities data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class ActivitiesExport(BaseExport):
    """
    Export activities data to SQLite database.

    Exports:
    - Activities with all types and details
    - Activity participants
    """

    async def export(
        self,
        include_participants: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export activities data to SQLite database.

        Args:
            include_participants: Whether to export activity participants
            filters: Optional filters for activities

        Returns:
            Export statistics and results
        """
        logger.info("Starting activities export")

        # Create activities table
        await self._create_activities_table()

        # Fetch all activities
        activities_data = await self.fetch_all_paginated("/activities", filters)

        if not activities_data:
            logger.warning("No activities found to export")
            return {"activities_exported": 0, "tables_created": []}

        # Transform and insert activities
        transformed_activities = [
            self._transform_activity(activity) for activity in activities_data
        ]
        activities_inserted = await self.bulk_insert(
            "activities", transformed_activities
        )

        tables_created = ["activities"]
        export_stats = {"activities_exported": activities_inserted}

        # Export participants if requested
        if include_participants:
            participants_stats = await self._export_activity_participants(
                activities_data
            )
            export_stats.update(participants_stats)
            tables_created.append("activity_participants")

        export_stats["tables_created"] = tables_created

        logger.info(f"Activities export completed: {export_stats}")
        return export_stats

    async def _create_activities_table(self) -> None:
        """Create activities table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "subject": "TEXT",
            "type": "TEXT NOT NULL",
            "description": "TEXT",
            "due_date": "DATE",
            "due_time": "TIME",
            "duration": "TEXT",
            "user_id": "INTEGER",
            "deal_id": "INTEGER",
            "person_id": "INTEGER",
            "org_id": "INTEGER",
            "note": "TEXT",
            "location": "TEXT",
            "public": "BOOLEAN DEFAULT FALSE",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "done": "BOOLEAN DEFAULT FALSE",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_activities_type ON activities(type)",
            "CREATE INDEX idx_activities_user_id ON activities(user_id)",
            "CREATE INDEX idx_activities_deal_id ON activities(deal_id)",
            "CREATE INDEX idx_activities_person_id ON activities(person_id)",
            "CREATE INDEX idx_activities_org_id ON activities(org_id)",
            "CREATE INDEX idx_activities_due_date ON activities(due_date)",
            "CREATE INDEX idx_activities_done ON activities(done)",
            "CREATE INDEX idx_activities_active_flag ON activities(active_flag)",
        ]

        await self.create_table("activities", columns, indexes, drop_if_exists=True)

    def _transform_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform activity data for database insertion."""
        return {
            "id": activity_data.get("id"),
            "subject": activity_data.get("subject"),
            "type": activity_data.get("type"),
            "description": activity_data.get("description"),
            "due_date": activity_data.get("due_date"),
            "due_time": activity_data.get("due_time"),
            "duration": activity_data.get("duration"),
            "user_id": activity_data.get("user_id"),
            "deal_id": activity_data.get("deal_id"),
            "person_id": activity_data.get("person_id"),
            "org_id": activity_data.get("org_id"),
            "note": activity_data.get("note"),
            "location": activity_data.get("location"),
            "public": activity_data.get("public", False),
            "active_flag": activity_data.get("active_flag", True),
            "done": activity_data.get("done", False),
            "add_time": activity_data.get("add_time"),
            "update_time": activity_data.get("update_time"),
        }

    async def _export_activity_participants(
        self, activities_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export participants for all activities."""
        await self._create_activity_participants_table()

        all_participants = []
        for activity in activities_data:
            activity_id = activity.get("id")
            participants = activity.get("participants", [])

            if isinstance(participants, list):
                for participant in participants:
                    participant_data = {
                        "activity_id": activity_id,
                        "person_id": participant.get("person_id"),
                        "primary_flag": participant.get("primary_flag", False),
                    }
                    all_participants.append(participant_data)

        if all_participants:
            participants_inserted = await self.bulk_insert(
                "activity_participants", all_participants
            )
            return {"activity_participants_exported": participants_inserted}

        return {"activity_participants_exported": 0}

    async def _create_activity_participants_table(self) -> None:
        """Create activity_participants table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "activity_id": "INTEGER NOT NULL",
            "person_id": "INTEGER NOT NULL",
            "primary_flag": "BOOLEAN DEFAULT FALSE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_activity_participants_activity_id ON activity_participants(activity_id)",
            "CREATE INDEX idx_activity_participants_person_id ON activity_participants(person_id)",
            "CREATE UNIQUE INDEX idx_activity_participants_unique ON activity_participants(activity_id, person_id)",
        ]

        await self.create_table("activity_participants", columns, indexes)
