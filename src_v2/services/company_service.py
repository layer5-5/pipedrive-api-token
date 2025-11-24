"""Company/Organization management service."""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..client.pipedrive_client import PipedriveClient
from ..models.company import (
    Organization,
    ComprehensiveOrganization,
    OrganizationFilter,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
)
from ..models.common import PaginatedResponse, PaginationInfo
from ..models.deal import Deal
from ..models.contact import Person
from ..utils.errors import PipedriveNotFoundError

logger = logging.getLogger(__name__)


class CompanyService:
    """Company/Organization management service."""

    def __init__(self, client: PipedriveClient):
        self.client = client

    async def get_organizations(self, filters: Optional[OrganizationFilter] = None) -> PaginatedResponse[Organization]:
        """Get list of organizations."""
        if filters is None:
            filters = OrganizationFilter()
        
        params: Dict[str, Any] = {
            "start": filters.start,
            "limit": filters.limit,
        }
        
        if filters.owner_id:
            params["owner_id"] = filters.owner_id
        if filters.first_char:
            params["first_char"] = filters.first_char
        if filters.sort:
            params["sort"] = filters.sort
        
        response = await self.client.get("/v1/organizations", params=params)
        orgs = [Organization(**o) for o in response.get("data", [])]
        
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None
        
        return PaginatedResponse(data=orgs, pagination=pagination)

    async def get_organization(self, org_id: int) -> Organization:
        """Get single organization by ID."""
        response = await self.client.get(f"/v1/organizations/{org_id}")
        org_data = response.get("data")
        
        if not org_data:
            raise PipedriveNotFoundError(f"Organization {org_id} not found", "organization", org_id)
        
        return Organization(**org_data)

    async def get_comprehensive_organization(self, org_id: int) -> ComprehensiveOrganization:
        """Get comprehensive organization data."""
        org = await self.get_organization(org_id)
        
        import asyncio
        deals_task = self.get_organization_deals(org_id)
        persons_task = self.get_organization_persons(org_id)
        
        deals, persons = await asyncio.gather(deals_task, persons_task, return_exceptions=True)
        
        deals = deals if not isinstance(deals, Exception) else []
        persons = persons if not isinstance(persons, Exception) else []
        
        # Calculate total revenue from won deals
        total_revenue = sum(d.value for d in deals if d.status == "won" and d.value) if deals else Decimal(0)
        
        return ComprehensiveOrganization(
            **org.model_dump(),
            deals=deals,
            persons=persons,
            total_revenue=total_revenue,
        )

    async def get_organization_deals(self, org_id: int) -> List[Deal]:
        """Get all deals for an organization."""
        try:
            response = await self.client.get(f"/v1/organizations/{org_id}/deals")
            return [Deal(**d) for d in response.get("data", [])]
        except Exception as e:
            logger.warning(f"Error fetching deals for org {org_id}: {e}")
            return []

    async def get_organization_persons(self, org_id: int) -> List[Person]:
        """Get all persons for an organization."""
        try:
            response = await self.client.get(f"/v1/organizations/{org_id}/persons")
            return [Person(**p) for p in response.get("data", [])]
        except Exception as e:
            logger.warning(f"Error fetching persons for org {org_id}: {e}")
            return []

    async def create_organization(self, request: OrganizationCreateRequest) -> Organization:
        """Create a new organization."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.post("/v1/organizations", data=data)
        return Organization(**response.get("data"))

    async def update_organization(self, org_id: int, request: OrganizationUpdateRequest) -> Organization:
        """Update an existing organization."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.put(f"/v1/organizations/{org_id}", data=data)
        return Organization(**response.get("data"))

    async def delete_organization(self, org_id: int) -> bool:
        """Delete an organization."""
        response = await self.client.delete(f"/v1/organizations/{org_id}")
        return response.get("success", False)
