"""Simplified Deal management service."""

import logging
from typing import List, Optional, Dict, Any

from ..client.pipedrive_client import PipedriveClient
from ..models.deal import Deal, DealCreateRequest, DealUpdateRequest
from ..models.common import PaginatedResponse
from ..utils.errors import PipedriveNotFoundError, PipedriveValidationError

logger = logging.getLogger(__name__)


class DealService:
    """Simplified deal management service."""

    def __init__(self, client: PipedriveClient):
        """Initialize deal service."""
        self.client = client

    async def search_deals(self, term: str, limit: int = 10) -> List[Deal]:
        """
        Search for deals by term.

        Args:
            term: Search term
            limit: Maximum number of results

        Returns:
            List of matching deals
        """
        params = {"term": term, "limit": limit}
        response = await self.client.get("/v1/deals/search", params=params)

        deals_data = response.get("data", [])
        return [Deal(**deal_data) for deal_data in deals_data]

    async def get_deal(self, deal_id: int) -> Deal:
        """
        Get single deal by ID.

        Args:
            deal_id: Deal ID

        Returns:
            Deal object

        Raises:
            PipedriveNotFoundError: Deal not found
        """
        response = await self.client.get(f"/v1/deals/{deal_id}")
        deal_data = response.get("data")

        if not deal_data:
            raise PipedriveNotFoundError(
                f"Deal {deal_id} not found",
                resource_type="deal",
                resource_id=deal_id,
            )

        return Deal(**deal_data)

    async def create_deal(
        self,
        title: str,
        value: Optional[str] = None,
        currency: str = "USD",
        person_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        stage_id: Optional[int] = None,
    ) -> Deal:
        """
        Create a new deal.

        Args:
            title: Deal title
            value: Deal value
            currency: Currency code
            person_id: Person ID
            organization_id: Organization ID
            stage_id: Stage ID

        Returns:
            Created deal
        """
        data = {"title": title}

        if value is not None:
            data["value"] = str(value)
        if currency:
            data["currency"] = currency
        if person_id:
            data["person_id"] = str(person_id)
        if organization_id:
            data["org_id"] = str(organization_id)
        if stage_id:
            data["stage_id"] = str(stage_id)

        response = await self.client.post("/v1/deals", data=data)
        deal_data = response.get("data")

        if not deal_data:
            raise PipedriveValidationError("Failed to create deal")

        return Deal(**deal_data)

    async def update_deal(
        self,
        deal_id: int,
        title: Optional[str] = None,
        value: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Deal:
        """
        Update an existing deal.

        Args:
            deal_id: Deal ID
            title: New title
            value: New value
            status: New status

        Returns:
            Updated deal
        """
        data = {}

        if title is not None:
            data["title"] = title
        if value is not None:
            data["value"] = value
        if status is not None:
            data["status"] = status

        response = await self.client.put(f"/v1/deals/{deal_id}", data=data)
        deal_data = response.get("data")

        if not deal_data:
            raise PipedriveNotFoundError(
                f"Deal {deal_id} not found or update failed",
                resource_type="deal",
                resource_id=deal_id,
            )

        return Deal(**deal_data)
