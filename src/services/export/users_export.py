"""
Pipedrive Users Export Service

API Documentation References:
- Primary API: https://developers.pipedrive.com/docs/api/v1/Users
- Related APIs: https://developers.pipedrive.com/docs/api/v1/UserRoles
Reference Date: 2025-12-02

This module exports users data from Pipedrive API to SQLite database.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_export import BaseExport

logger = logging.getLogger(__name__)


class UsersExport(BaseExport):
    """
    Export users data to SQLite database.

    Exports:
    - Users with roles and permissions
    - User roles
    """

    async def export(
        self,
        include_roles: bool = True,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export users data to SQLite database.

        Args:
            include_roles: Whether to export user roles
            filters: Optional filters for users

        Returns:
            Export statistics and results
        """
        logger.info("Starting users export")

        # Create users table
        await self._create_users_table()

        # Fetch all users
        users_data = await self.fetch_all_paginated("/users", filters)

        if not users_data:
            logger.warning("No users found to export")
            return {"users_exported": 0, "tables_created": []}

        # Transform and insert users
        transformed_users = [self._transform_user(user) for user in users_data]
        users_inserted = await self.bulk_insert("users", transformed_users)

        tables_created = ["users"]
        export_stats = {"users_exported": users_inserted}

        # Export roles if requested
        if include_roles:
            roles_stats = await self._export_user_roles(users_data)
            export_stats.update(roles_stats)
            tables_created.append("user_roles")

        export_stats["tables_created"] = tables_created

        logger.info(f"Users export completed: {export_stats}")
        return export_stats

    async def _create_users_table(self) -> None:
        """Create users table with proper schema."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "email": "TEXT NOT NULL",
            "active_flag": "BOOLEAN DEFAULT TRUE",
            "is_admin": "BOOLEAN DEFAULT FALSE",
            "is_you": "BOOLEAN DEFAULT FALSE",
            "role_id": "INTEGER",
            "role_name": "TEXT",
            "default_currency": "TEXT",
            "locale": "TEXT",
            "timezone": "TEXT",
            "phone": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_users_email ON users(email)",
            "CREATE INDEX idx_users_active_flag ON users(active_flag)",
            "CREATE INDEX idx_users_role_id ON users(role_id)",
            "CREATE INDEX idx_users_is_admin ON users(is_admin)",
        ]

        await self.create_table("users", columns, indexes, drop_if_exists=True)

    def _transform_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user data for database insertion."""
        role = user_data.get("role", {})

        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "active_flag": user_data.get("active_flag", True),
            "is_admin": user_data.get("is_admin", False),
            "is_you": user_data.get("is_you", False),
            "role_id": role.get("id") if role else None,
            "role_name": role.get("name") if role else None,
            "default_currency": user_data.get("default_currency"),
            "locale": user_data.get("locale"),
            "timezone": user_data.get("timezone"),
            "phone": user_data.get("phone"),
        }

    async def _export_user_roles(
        self, users_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Export user roles."""
        await self._create_user_roles_table()

        # Extract unique roles from users
        roles_map = {}
        for user in users_data:
            role = user.get("role")
            if role and role.get("id"):
                roles_map[role["id"]] = role

        if roles_map:
            roles_data = list(roles_map.values())
            transformed_roles = [self._transform_role(role) for role in roles_data]
            roles_inserted = await self.bulk_insert("user_roles", transformed_roles)
            return {"user_roles_exported": roles_inserted}

        return {"user_roles_exported": 0}

    async def _create_user_roles_table(self) -> None:
        """Create user_roles table."""
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "level": "INTEGER",
            "description": "TEXT",
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        }

        indexes = [
            "CREATE INDEX idx_user_roles_name ON user_roles(name)",
            "CREATE INDEX idx_user_roles_level ON user_roles(level)",
        ]

        await self.create_table("user_roles", columns, indexes)

    def _transform_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform role data for database insertion."""
        return {
            "id": role_data.get("id"),
            "name": role_data.get("name"),
            "level": role_data.get("level"),
            "description": role_data.get("description"),
        }
