# TODO: Avoid silent failures in exception handling.
# The `get_person_deals` and `get_person_activities` methods use a broad `except Exception`
# that logs a warning and returns an empty list. This is a silent failure that can hide underlying issues.
# It's better to let exceptions propagate to a centralized error handler in the web layer,
# or to catch specific, expected exceptions and re-raise them as a custom service-level exception.
# This will make the application more robust and easier to debug.

# TODO: Improve exception handling in `get_comprehensive_person`.
# When using `asyncio.gather` with `return_exceptions=True`, the code checks for exceptions
# but then discards them. At a minimum, the exceptions should be logged with their full traceback
# so that errors are not silently ignored. For example:
# `if isinstance(deals, Exception): logger.error("Failed to fetch deals", exc_info=deals)`
"""Contact/Person management service."""

import logging
from typing import List, Optional, Dict, Any

from ..client.pipedrive_client import PipedriveClient
from ..models.contact import (
    Person,
    ComprehensivePerson,
    PersonFilter,
    PersonCreateRequest,
    PersonUpdateRequest,
)
from ..models.common import PaginatedResponse, PaginationInfo, Note, File
from ..models.deal import Deal
from ..models.activity import Activity
from ..utils.errors import PipedriveNotFoundError, PipedriveAPIError

logger = logging.getLogger(__name__)


class ContactService:
    """Contact/Person management service."""

    def __init__(self, client: PipedriveClient):
        self.client = client

    async def get_persons(
        self, filters: Optional[PersonFilter] = None
    ) -> PaginatedResponse[Person]:
        """Get list of persons with optional filtering."""
        if filters is None:
            filters = PersonFilter()

        params: Dict[str, Any] = {
            "start": filters.start,
            "limit": filters.limit,
        }

        if filters.org_id:
            params["org_id"] = filters.org_id
        if filters.owner_id:
            params["owner_id"] = filters.owner_id
        if filters.first_char:
            params["first_char"] = filters.first_char
        if filters.sort:
            params["sort"] = filters.sort

        response = await self.client.get("/v1/persons", params=params)
        persons = [Person(**p) for p in response.get("data", [])]

        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None

        return PaginatedResponse(data=persons, pagination=pagination)

    async def get_person(self, person_id: int) -> Person:
        """Get single person by ID."""
        response = await self.client.get(f"/v1/persons/{person_id}")
        person_data = response.get("data")

        if not person_data:
            raise PipedriveNotFoundError(
                f"Person {person_id} not found", "person", person_id
            )

        return Person(**person_data)

    async def get_comprehensive_person(self, person_id: int) -> ComprehensivePerson:
        """Get comprehensive person data with all relationships."""
        person = await self.get_person(person_id)

        import asyncio

        deals_task = self.get_person_deals(person_id)
        activities_task = self.get_person_activities(person_id)

        deals, activities = await asyncio.gather(
            deals_task, activities_task, return_exceptions=True
        )

        deals = deals if not isinstance(deals, Exception) else []
        activities = activities if not isinstance(activities, Exception) else []

        return ComprehensivePerson(
            **person.model_dump(), deals=deals, activities=activities
        )

    async def get_person_deals(self, person_id: int) -> List[Deal]:
        """Get all deals for a person."""
        response = await self.client.get(f"/v1/persons/{person_id}/deals")
        return [Deal(**d) for d in response.get("data", [])]

    async def get_person_activities(self, person_id: int) -> List[Activity]:
        """Get all activities for a person."""
        response = await self.client.get(f"/v1/persons/{person_id}/activities")
        return [Activity(**a) for a in response.get("data", [])]

    async def create_person(self, request: PersonCreateRequest) -> Person:
        """Create a new person."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.post("/v1/persons", data=data)
        return Person(**response.get("data"))

    async def update_person(
        self, person_id: int, request: PersonUpdateRequest
    ) -> Person:
        """Update an existing person."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.put(f"/v1/persons/{person_id}", data=data)
        return Person(**response.get("data"))

    async def delete_person(self, person_id: int) -> bool:
        """Delete a person."""
        response = await self.client.delete(f"/v1/persons/{person_id}")
        return response.get("success", False)

    async def search_persons(self, query: str, limit: int = 10) -> List[Person]:
        """
        Search for persons by name, email, or other fields.

        Args:
            query: Search term to look for
            limit: Maximum number of results to return

        Returns:
            List of matching persons
        """
        params: Dict[str, Any] = {
            "term": query,
            "item_type": "person",
            "limit": limit,
        }

        response = await self.client.get("/v2/itemSearch", params=params)

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to search persons: {error_message}")

        # Item search returns different structure - extract person data
        search_results = response.get("data", [])
        persons = []

        for result in search_results:
            if result.get("type") == "person":
                person_data = result.get("data", {})
                if person_data:
                    persons.append(Person(**person_data))

        return persons
