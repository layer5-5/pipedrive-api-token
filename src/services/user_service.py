"""User management service for Pipedrive MCP Server."""

import logging
from typing import List, Optional

from ..client.pipedrive_client import PipedriveClient
from ..models.user import User
from ..models.common import PaginatedResponse, PaginationInfo
from ..utils.errors import PipedriveError, PipedriveNotFoundError

logger = logging.getLogger(__name__)


class UserService:
    """
    User management service providing:
    - User retrieval operations
    - Team member listing
    - User details fetching
    """

    def __init__(self, client: PipedriveClient):
        """Initialize user service with Pipedrive client."""
        self.client = client

    async def get_users(self, limit: int = 10) -> PaginatedResponse:
        """
        Get list of users/team members.

        Args:
            limit: Maximum number of users to return

        Returns:
            Paginated response with users

        Raises:
            PipedriveError: If API call fails
        """
        try:
            response = await self.client.get("/v1/users", params={"limit": limit})

            users_data = response.get("data", [])
            users = [User(**user) for user in users_data]

            # Create pagination info
            pagination = PaginationInfo(
                start=0, limit=limit, more_items_in_collection=False, next_start=None
            )

            return PaginatedResponse(
                data=users, pagination=pagination, success=response.get("success", True)
            )

        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            raise PipedriveError(f"Failed to fetch users: {str(e)}")

    async def get_user(self, user_id: int) -> User:
        """
        Get specific user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            PipedriveNotFoundError: If user not found
            PipedriveError: If API call fails
        """
        try:
            response = await self.client.get(f"/v1/users/{user_id}")

            if not response.get("success", False):
                raise PipedriveNotFoundError(f"User {user_id} not found")

            user_data = response.get("data")
            if not user_data:
                raise PipedriveNotFoundError(f"User {user_id} not found")

            return User(**user_data)

        except PipedriveNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise PipedriveError(f"Failed to fetch user: {str(e)}")

    async def find_user_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.

        Args:
            email: Email address to search for

        Returns:
            User object if found, None otherwise
        """
        try:
            # Get all users and search for matching email
            users_response = await self.get_users(
                limit=100
            )  # Get more users for search
            users = users_response.data

            for user in users:
                if (
                    hasattr(user, "email")
                    and user.email
                    and user.email.lower() == email.lower()
                ):
                    return user

            return None

        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None

    async def get_current_user(self) -> User:
        """
        Get the current authenticated user.

        Returns:
            Current user object

        Raises:
            PipedriveError: If API call fails
        """
        try:
            response = await self.client.get("/v1/users/me")

            if not response.get("success", False):
                raise PipedriveError("Failed to get current user")

            user_data = response.get("data")
            if not user_data:
                raise PipedriveError("No current user data available")

            return User(**user_data)

        except Exception as e:
            logger.error(f"Error fetching current user: {e}")
            raise PipedriveError(f"Failed to get current user: {str(e)}")
