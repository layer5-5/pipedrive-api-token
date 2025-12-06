"""
Pipedrive Deals Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Deals
- Related APIs: https://developers.pipedrive.com/docs/api/v1/Activities, https://developers.pipedrive.com/docs/api/v1/Notes, https://developers.pipedrive.com/docs/api/v1/Products, https://developers.pipedrive.com/docs/api/v1/Files
Reference Date: 2025-12-02

This module exports deals data from Pipedrive API to SQLite database.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_export import BaseExport
from ...models.deal import Deal, DealStatus
from ...models.activity import Activity
from ...models.contact import Person
from ...models.user import User
from ...models.common import Note, File

logger = logging.getLogger(__name__)


class DealsExport(BaseExport):
    """
    Export deals data to SQLite database.

    Exports:
    - Deals with all stages and related data
    - Deal activities
    - Deal notes
    - Deal products
    - Deal files
    - Deal followers
    - Deal participants
    """

    async def export(
        self,
        include_activities: bool = True,
        include_notes: bool = True,
        include_products: bool = True,
        include_files: bool = True,
        include_followers: bool = True,
        include_participants: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export deals data to SQLite database.

        Args:
            include_activities: Whether to export deal activities
            include_notes: Whether to export deal notes
            include_products: Whether to export deal products
            include_files: Whether to export deal files
            include_followers: Whether to export deal followers
            include_participants: Whether to export deal participants
            filters: Optional filters for deals

        Returns:
            Export statistics and results
        """
        logger.info("Starting deals export")

        # Create deals table
        await self._create_deals_table()

        # Fetch all deals
        deals_data = await self.fetch_all_paginated("/deals", filters)

        if not deals_data:
            logger.warning("No deals found to export")
            return {"deals_exported": 0, "tables_created": []}

        # Transform and insert deals
        transformed_deals = [self._transform_deal(deal) for deal in deals_data]
        deals_inserted = await self.bulk_insert("deals", transformed_deals)

        tables_created = ["deals"]
        export_stats = {"deals_exported": deals_inserted}

        # Export related data
        if include_activities:
            activities_stats = await self._export_deal_activities(deals_data)
            export_stats.update(activities_stats)
            tables_created.append("deal_activities")

        if include_notes:
            notes_stats = await self._export_deal_notes(deals_data)
            export_stats.update(notes_stats)
            tables_created.append("deal_notes")

        if include_products:
            products_stats = await self._export_deal_products(deals_data)
            export_stats.update(products_stats)
            tables_created.append("deal_products")

        if include_files:
            files_stats = await self._export_deal_files(deals_data)
            export_stats.update(files_stats)
            tables_created.append("deal_files")

        if include_followers:
            followers_stats = await self._export_deal_followers(deals_data)
            export_stats.update(followers_stats)
            tables_created.append("deal_followers")

        if include_participants:
            participants_stats = await self._export_deal_participants(deals_data)
            export_stats.update(participants_stats)
            tables_created.append("deal_participants")

        export_stats["tables_created"] = tables_created

        logger.info(f"Deals export completed: {export_stats}")
        return export_stats

    async def _create_deals_table(self) -> None:
        """Create deals table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "title": "TEXT NOT NULL",
            "value": "REAL",
            "currency": "TEXT",
            "status": "TEXT",
            "stage_id": "INTEGER",
            "pipeline_id": "INTEGER",
            "owner_id": "INTEGER",
            "creator_user_id": "INTEGER",
            "person_id": "INTEGER",
            "org_id": "INTEGER",
            "person_name": "TEXT",
            "org_name": "TEXT",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "stage_change_time": "DATETIME",
            "expected_close_date": "DATE",
            "close_time": "DATETIME",
            "won_time": "DATETIME",
            "lost_time": "DATETIME",
            "first_won_time": "DATETIME",
            "lost_reason": "TEXT",
            "probability": "INTEGER",
            "products_count": "INTEGER DEFAULT 0",
            "activities_count": "INTEGER DEFAULT 0",
            "done_activities_count": "INTEGER DEFAULT 0",
            "undone_activities_count": "INTEGER DEFAULT 0",
            "files_count": "INTEGER DEFAULT 0",
            "notes_count": "INTEGER DEFAULT 0",
            "followers_count": "INTEGER DEFAULT 0",
            "email_messages_count": "INTEGER DEFAULT 0",
            "participants_count": "INTEGER DEFAULT 0",
            "next_activity_date": "DATE",
            "next_activity_time": "TIME",
            "next_activity_id": "INTEGER",
            "last_activity_date": "DATE",
            "last_activity_id": "INTEGER",
            "last_incoming_mail_time": "DATETIME",
            "last_outgoing_mail_time": "DATETIME",
            "visible_to": "TEXT",
            "active": "BOOLEAN DEFAULT TRUE",
            "deleted": "BOOLEAN DEFAULT FALSE",
            "custom_fields": "TEXT",  # JSON string
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deals_status ON deals(status)",
            "CREATE INDEX idx_deals_stage_id ON deals(stage_id)",
            "CREATE INDEX idx_deals_pipeline_id ON deals(pipeline_id)",
            "CREATE INDEX idx_deals_owner_id ON deals(owner_id)",
            "CREATE INDEX idx_deals_person_id ON deals(person_id)",
            "CREATE INDEX idx_deals_org_id ON deals(org_id)",
            "CREATE INDEX idx_deals_add_time ON deals(add_time)",
            "CREATE INDEX idx_deals_value ON deals(value)",
        ]

        await self.create_table("deals", columns, indexes, drop_if_exists=True)

    def _transform_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform deal data for database insertion."""
        import json

        return {
            "id": deal_data.get("id"),
            "title": deal_data.get("title"),
            "value": float(deal_data.get("value", 0))
            if deal_data.get("value")
            else None,
            "currency": deal_data.get("currency"),
            "status": deal_data.get("status"),
            "stage_id": deal_data.get("stage_id"),
            "pipeline_id": deal_data.get("pipeline_id"),
            "owner_id": deal_data.get("owner_id"),
            "creator_user_id": deal_data.get("creator_user_id"),
            "person_id": deal_data.get("person_id"),
            "org_id": deal_data.get("org_id"),
            "person_name": deal_data.get("person_name"),
            "org_name": deal_data.get("org_name"),
            "add_time": deal_data.get("add_time"),
            "update_time": deal_data.get("update_time"),
            "stage_change_time": deal_data.get("stage_change_time"),
            "expected_close_date": deal_data.get("expected_close_date"),
            "close_time": deal_data.get("close_time"),
            "won_time": deal_data.get("won_time"),
            "lost_time": deal_data.get("lost_time"),
            "first_won_time": deal_data.get("first_won_time"),
            "lost_reason": deal_data.get("lost_reason"),
            "probability": deal_data.get("probability"),
            "products_count": deal_data.get("products_count", 0),
            "activities_count": deal_data.get("activities_count", 0),
            "done_activities_count": deal_data.get("done_activities_count", 0),
            "undone_activities_count": deal_data.get("undone_activities_count", 0),
            "files_count": deal_data.get("files_count", 0),
            "notes_count": deal_data.get("notes_count", 0),
            "followers_count": deal_data.get("followers_count", 0),
            "email_messages_count": deal_data.get("email_messages_count", 0),
            "participants_count": deal_data.get("participants_count", 0),
            "next_activity_date": deal_data.get("next_activity_date"),
            "next_activity_time": deal_data.get("next_activity_time"),
            "next_activity_id": deal_data.get("next_activity_id"),
            "last_activity_date": deal_data.get("last_activity_date"),
            "last_activity_id": deal_data.get("last_activity_id"),
            "last_incoming_mail_time": deal_data.get("last_incoming_mail_time"),
            "last_outgoing_mail_time": deal_data.get("last_outgoing_mail_time"),
            "visible_to": deal_data.get("visible_to"),
            "active": deal_data.get("active", True),
            "deleted": deal_data.get("deleted", False),
            "custom_fields": json.dumps(deal_data.get("custom_fields", {})),
        }

    async def _export_deal_activities(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export activities for all deals."""
        await self._create_deal_activities_table()

        all_activities = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get(f"/deals/{deal_id}/activities")
                activities = response.get("data", [])

                for activity in activities:
                    activity["deal_id"] = deal_id
                    all_activities.append(activity)

            except Exception as e:
                logger.warning(f"Failed to fetch activities for deal {deal_id}: {e}")

        if all_activities:
            transformed_activities = [
                self._transform_activity(activity) for activity in all_activities
            ]
            activities_inserted = await self.bulk_insert(
                "deal_activities", transformed_activities
            )
            return {"activities_exported": activities_inserted}

        return {"activities_exported": 0}

    async def _create_deal_activities_table(self) -> None:
        """Create deal_activities table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "subject": "TEXT",
            "type": "TEXT",
            "description": "TEXT",
            "due_date": "DATE",
            "due_time": "TIME",
            "duration": "TEXT",
            "user_id": "INTEGER",
            "done": "BOOLEAN DEFAULT FALSE",
            "note": "TEXT",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "update_time": "DATETIME",
            "add_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_activities_deal_id ON deal_activities(deal_id)",
            "CREATE INDEX idx_deal_activities_type ON deal_activities(type)",
            "CREATE INDEX idx_deal_activities_due_date ON deal_activities(due_date)",
        ]

        await self.create_table("deal_activities", columns, indexes)

    def _transform_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform activity data for database insertion."""
        return {
            "id": activity_data.get("id"),
            "deal_id": activity_data.get("deal_id"),
            "subject": activity_data.get("subject"),
            "type": activity_data.get("type"),
            "description": activity_data.get("description"),
            "due_date": activity_data.get("due_date"),
            "due_time": activity_data.get("due_time"),
            "duration": activity_data.get("duration"),
            "user_id": activity_data.get("user_id"),
            "done": activity_data.get("done", False),
            "note": activity_data.get("note"),
            "active_flag": activity_data.get("active_flag", True),
            "update_time": activity_data.get("update_time"),
            "add_time": activity_data.get("add_time"),
        }

    async def _export_deal_notes(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export notes for all deals."""
        await self._create_deal_notes_table()

        all_notes = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get("/notes", params={"deal_id": deal_id})
                notes = response.get("data", [])

                for note in notes:
                    note["deal_id"] = deal_id
                    all_notes.append(note)

            except Exception as e:
                logger.warning(f"Failed to fetch notes for deal {deal_id}: {e}")

        if all_notes:
            transformed_notes = [self._transform_note(note) for note in all_notes]
            notes_inserted = await self.bulk_insert("deal_notes", transformed_notes)
            return {"notes_exported": notes_inserted}

        return {"notes_exported": 0}

    async def _create_deal_notes_table(self) -> None:
        """Create deal_notes table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "content": "TEXT NOT NULL",
            "user_id": "INTEGER",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_notes_deal_id ON deal_notes(deal_id)",
            "CREATE INDEX idx_deal_notes_user_id ON deal_notes(user_id)",
        ]

        await self.create_table("deal_notes", columns, indexes)

    def _transform_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform note data for database insertion."""
        return {
            "id": note_data.get("id"),
            "deal_id": note_data.get("deal_id"),
            "content": note_data.get("content"),
            "user_id": note_data.get("user_id"),
            "add_time": note_data.get("add_time"),
            "update_time": note_data.get("update_time"),
        }

    async def _export_deal_products(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export products for all deals."""
        await self._create_deal_products_table()

        all_products = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get(f"/deals/{deal_id}/products")
                products = response.get("data", [])

                for product in products:
                    product["deal_id"] = deal_id
                    all_products.append(product)

            except Exception as e:
                logger.warning(f"Failed to fetch products for deal {deal_id}: {e}")

        if all_products:
            transformed_products = [
                self._transform_deal_product(product) for product in all_products
            ]
            products_inserted = await self.bulk_insert(
                "deal_products", transformed_products
            )
            return {"deal_products_exported": products_inserted}

        return {"deal_products_exported": 0}

    async def _create_deal_products_table(self) -> None:
        """Create deal_products table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "product_id": "INTEGER",
            "name": "TEXT",
            "item_price": "REAL",
            "quantity": "INTEGER",
            "discount": "REAL",
            "discount_type": "TEXT",
            "tax": "REAL",
            "sum": "REAL",
            "currency": "TEXT",
            "enabled_flag": "BOOLEAN DEFAULT TRUE",
            "add_time": "DATETIME",
            "comments": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_products_deal_id ON deal_products(deal_id)",
            "CREATE INDEX idx_deal_products_product_id ON deal_products(product_id)",
        ]

        await self.create_table("deal_products", columns, indexes)

    def _transform_deal_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform deal product data for database insertion."""
        return {
            "id": product_data.get("id"),
            "deal_id": product_data.get("deal_id"),
            "product_id": product_data.get("product_id"),
            "name": product_data.get("name"),
            "item_price": float(product_data.get("item_price", 0))
            if product_data.get("item_price")
            else None,
            "quantity": product_data.get("quantity"),
            "discount": float(product_data.get("discount", 0))
            if product_data.get("discount")
            else None,
            "discount_type": product_data.get("discount_type"),
            "tax": float(product_data.get("tax", 0))
            if product_data.get("tax")
            else None,
            "sum": float(product_data.get("sum", 0))
            if product_data.get("sum")
            else None,
            "currency": product_data.get("currency"),
            "enabled_flag": product_data.get("enabled_flag", True),
            "add_time": product_data.get("add_time"),
            "comments": product_data.get("comments"),
        }

    async def _export_deal_files(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export files for all deals."""
        await self._create_deal_files_table()

        all_files = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get(f"/deals/{deal_id}/files")
                files = response.get("data", [])

                for file in files:
                    file["deal_id"] = deal_id
                    all_files.append(file)

            except Exception as e:
                logger.warning(f"Failed to fetch files for deal {deal_id}: {e}")

        if all_files:
            transformed_files = [self._transform_file(file) for file in all_files]
            files_inserted = await self.bulk_insert("deal_files", transformed_files)
            return {"deal_files_exported": files_inserted}

        return {"deal_files_exported": 0}

    async def _create_deal_files_table(self) -> None:
        """Create deal_files table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "name": "TEXT",
            "file_type": "TEXT",
            "file_size": "INTEGER",
            "url": "TEXT",
            "remote_location": "TEXT",
            "upload_time": "DATETIME",
            "add_time": "DATETIME",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_files_deal_id ON deal_files(deal_id)",
            "CREATE INDEX idx_deal_files_file_type ON deal_files(file_type)",
        ]

        await self.create_table("deal_files", columns, indexes)

    def _transform_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform file data for database insertion."""
        return {
            "id": file_data.get("id"),
            "deal_id": file_data.get("deal_id"),
            "name": file_data.get("name"),
            "file_type": file_data.get("file_type"),
            "file_size": file_data.get("file_size"),
            "url": file_data.get("url"),
            "remote_location": file_data.get("remote_location"),
            "upload_time": file_data.get("upload_time"),
            "add_time": file_data.get("add_time"),
        }

    async def _export_deal_followers(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export followers for all deals."""
        await self._create_deal_followers_table()

        all_followers = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get(f"/deals/{deal_id}/followers")
                followers = response.get("data", [])

                for follower in followers:
                    follower["deal_id"] = deal_id
                    all_followers.append(follower)

            except Exception as e:
                logger.warning(f"Failed to fetch followers for deal {deal_id}: {e}")

        if all_followers:
            transformed_followers = [
                self._transform_follower(follower) for follower in all_followers
            ]
            followers_inserted = await self.bulk_insert(
                "deal_followers", transformed_followers
            )
            return {"deal_followers_exported": followers_inserted}

        return {"deal_followers_exported": 0}

    async def _create_deal_followers_table(self) -> None:
        """Create deal_followers table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "user_id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_followers_deal_id ON deal_followers(deal_id)",
            "CREATE INDEX idx_deal_followers_user_id ON deal_followers(user_id)",
        ]

        await self.create_table("deal_followers", columns, indexes)

    def _transform_follower(self, follower_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform follower data for database insertion."""
        return {
            "id": follower_data.get("id"),
            "deal_id": follower_data.get("deal_id"),
            "user_id": follower_data.get("id"),  # Follower ID is the user ID
            "name": follower_data.get("name"),
            "email": follower_data.get("email"),
        }

    async def _export_deal_participants(
        self, deals_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export participants for all deals."""
        await self._create_deal_participants_table()

        all_participants = []
        for deal in deals_data:
            deal_id = deal.get("id")
            try:
                response = await self.client.get(f"/deals/{deal_id}/participants")
                participants = response.get("data", [])

                for participant in participants:
                    participant["deal_id"] = deal_id
                    all_participants.append(participant)

            except Exception as e:
                logger.warning(f"Failed to fetch participants for deal {deal_id}: {e}")

        if all_participants:
            transformed_participants = [
                self._transform_participant(participant)
                for participant in all_participants
            ]
            participants_inserted = await self.bulk_insert(
                "deal_participants", transformed_participants
            )
            return {"deal_participants_exported": participants_inserted}

        return {"deal_participants_exported": 0}

    async def _create_deal_participants_table(self) -> None:
        """Create deal_participants table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "deal_id": "INTEGER NOT NULL",
            "person_id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_deal_participants_deal_id ON deal_participants(deal_id)",
            "CREATE INDEX idx_deal_participants_person_id ON deal_participants(person_id)",
        ]

        await self.create_table("deal_participants", columns, indexes)

    def _transform_participant(
        self, participant_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform participant data for database insertion."""
        return {
            "id": participant_data.get("id"),
            "deal_id": participant_data.get("deal_id"),
            "person_id": participant_data.get("person_id"),
            "name": participant_data.get("name"),
            "email": participant_data.get("email"),
            "phone": participant_data.get("phone"),
        }
