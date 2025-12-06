"""
Pipedrive Contacts Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Persons
- Related APIs: https://developers.pipedrive.com/docs/api/v1/Organizations
Reference Date: 2025-12-02

This module exports contacts (persons) data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class ContactsExport(BaseExport):
    """
    Export contacts (persons) data to SQLite database.

    Exports:
    - Persons with contact information
    - Person emails
    - Person phones
    - Person organizations
    """

    async def export(
        self,
        include_emails: bool = True,
        include_phones: bool = True,
        include_organizations: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export contacts data to SQLite database.

        Args:
            include_emails: Whether to export person emails
            include_phones: Whether to export person phones
            include_organizations: Whether to export person organizations
            filters: Optional filters for contacts

        Returns:
            Export statistics and results
        """
        logger.info("Starting contacts export")

        # Create persons table
        await self._create_persons_table()

        # Fetch all persons
        persons_data = await self.fetch_all_paginated("/persons", filters)

        if not persons_data:
            logger.warning("No contacts found to export")
            return {"contacts_exported": 0, "tables_created": []}

        # Transform and insert persons
        transformed_persons = [
            self._transform_person(person) for person in persons_data
        ]
        persons_inserted = await self.bulk_insert("persons", transformed_persons)

        tables_created = ["persons"]
        export_stats = {"contacts_exported": persons_inserted}

        # Export related data
        if include_emails:
            emails_stats = await self._export_person_emails(persons_data)
            export_stats.update(emails_stats)
            tables_created.append("person_emails")

        if include_phones:
            phones_stats = await self._export_person_phones(persons_data)
            export_stats.update(phones_stats)
            tables_created.append("person_phones")

        if include_organizations:
            orgs_stats = await self._export_person_organizations(persons_data)
            export_stats.update(orgs_stats)
            tables_created.append("person_organizations")

        export_stats["tables_created"] = tables_created

        logger.info(f"Contacts export completed: {export_stats}")
        return export_stats

    async def _create_persons_table(self) -> None:
        """Create persons table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "first_name": "TEXT",
            "last_name": "TEXT",
            "owner_id": "INTEGER",
            "org_id": "INTEGER",
            "org_name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "visible_to": "TEXT",
            "add_time": "DATETIME",
            "update_time": "DATETIME",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "label": "TEXT",
            "cc_email": "TEXT",
            "first_char": "TEXT",
            "custom_fields": "TEXT",  # JSON string
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_persons_name ON persons(name)",
            "CREATE INDEX idx_persons_owner_id ON persons(owner_id)",
            "CREATE INDEX idx_persons_org_id ON persons(org_id)",
            "CREATE INDEX idx_persons_email ON persons(email)",
            "CREATE INDEX idx_persons_active_flag ON persons(active_flag)",
            "CREATE INDEX idx_persons_add_time ON persons(add_time)",
        ]

        await self.create_table("persons", columns, indexes, drop_if_exists=True)

    def _transform_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform person data for database insertion."""
        import json

        return {
            "id": person_data.get("id"),
            "name": person_data.get("name"),
            "first_name": person_data.get("first_name"),
            "last_name": person_data.get("last_name"),
            "owner_id": person_data.get("owner_id"),
            "org_id": person_data.get("org_id"),
            "org_name": person_data.get("org_name"),
            "email": person_data.get("email"),
            "phone": person_data.get("phone"),
            "visible_to": person_data.get("visible_to"),
            "add_time": person_data.get("add_time"),
            "update_time": person_data.get("update_time"),
            "active_flag": person_data.get("active_flag", True),
            "label": person_data.get("label"),
            "cc_email": person_data.get("cc_email"),
            "first_char": person_data.get("first_char"),
            "custom_fields": json.dumps(person_data.get("custom_fields", {})),
        }

    async def _export_person_emails(
        self, persons_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export emails for all persons."""
        await self._create_person_emails_table()

        all_emails = []
        for person in persons_data:
            person_id = person.get("id")
            emails = person.get("email", [])

            if isinstance(emails, list):
                for email in emails:
                    email_data = {
                        "person_id": person_id,
                        "label": email.get("label", "other"),
                        "value": email.get("value"),
                        "primary": email.get("primary", False),
                    }
                    all_emails.append(email_data)
            elif isinstance(emails, dict):
                # Handle single email case
                email_data = {
                    "person_id": person_id,
                    "label": emails.get("label", "other"),
                    "value": emails.get("value"),
                    "primary": emails.get("primary", False),
                }
                all_emails.append(email_data)

        if all_emails:
            emails_inserted = await self.bulk_insert("person_emails", all_emails)
            return {"person_emails_exported": emails_inserted}

        return {"person_emails_exported": 0}

    async def _create_person_emails_table(self) -> None:
        """Create person_emails table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "person_id": "INTEGER NOT NULL",
            "label": "TEXT",
            "value": "TEXT NOT NULL",
            "primary": "BOOLEAN DEFAULT FALSE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_person_emails_person_id ON person_emails(person_id)",
            "CREATE INDEX idx_person_emails_value ON person_emails(value)",
            "CREATE INDEX idx_person_emails_primary ON person_emails(primary)",
        ]

        await self.create_table("person_emails", columns, indexes)

    async def _export_person_phones(
        self, persons_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export phones for all persons."""
        await self._create_person_phones_table()

        all_phones = []
        for person in persons_data:
            person_id = person.get("id")
            phones = person.get("phone", [])

            if isinstance(phones, list):
                for phone in phones:
                    phone_data = {
                        "person_id": person_id,
                        "label": phone.get("label", "other"),
                        "value": phone.get("value"),
                        "primary": phone.get("primary", False),
                    }
                    all_phones.append(phone_data)
            elif isinstance(phones, dict):
                # Handle single phone case
                phone_data = {
                    "person_id": person_id,
                    "label": phones.get("label", "other"),
                    "value": phones.get("value"),
                    "primary": phones.get("primary", False),
                }
                all_phones.append(phone_data)

        if all_phones:
            phones_inserted = await self.bulk_insert("person_phones", all_phones)
            return {"person_phones_exported": phones_inserted}

        return {"person_phones_exported": 0}

    async def _create_person_phones_table(self) -> None:
        """Create person_phones table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "person_id": "INTEGER NOT NULL",
            "label": "TEXT",
            "value": "TEXT NOT NULL",
            "primary": "BOOLEAN DEFAULT FALSE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_person_phones_person_id ON person_phones(person_id)",
            "CREATE INDEX idx_person_phones_value ON person_phones(value)",
            "CREATE INDEX idx_person_phones_primary ON person_phones(primary)",
        ]

        await self.create_table("person_phones", columns, indexes)

    async def _export_person_organizations(
        self, persons_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export organization relationships for all persons."""
        await self._create_person_organizations_table()

        all_orgs = []
        for person in persons_data:
            person_id = person.get("id")
            org_id = person.get("org_id")
            org_name = person.get("org_name")

            if org_id:
                org_data = {
                    "person_id": person_id,
                    "org_id": org_id,
                    "org_name": org_name,
                    "active": True,
                }
                all_orgs.append(org_data)

        if all_orgs:
            orgs_inserted = await self.bulk_insert("person_organizations", all_orgs)
            return {"person_organizations_exported": orgs_inserted}

        return {"person_organizations_exported": 0}

    async def _create_person_organizations_table(self) -> None:
        """Create person_organizations table."""
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "person_id": "INTEGER NOT NULL",
            "org_id": "INTEGER NOT NULL",
            "org_name": "TEXT",
            "active": "BOOLEAN DEFAULT TRUE",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_person_organizations_person_id ON person_organizations(person_id)",
            "CREATE INDEX idx_person_organizations_org_id ON person_organizations(org_id)",
            "CREATE UNIQUE INDEX idx_person_organizations_unique ON person_organizations(person_id, org_id)",
        ]

        await self.create_table("person_organizations", columns, indexes)
