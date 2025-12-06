"""Activity tracking service."""

import logging
from typing import List, Optional, Dict, Any

from ..client.pipedrive_client import PipedriveClient
from ..models.activity import (
    Activity,
    ActivityFilter,
    ActivityCreateRequest,
    ActivityUpdateRequest,
)
from ..models.common import PaginatedResponse, PaginationInfo
from ..utils.errors import PipedriveNotFoundError

logger = logging.getLogger(__name__)


class ActivityService:
    """Activity tracking and management service."""

    def __init__(self, client: PipedriveClient):
        self.client = client

    async def get_activities(self, filters: Optional[ActivityFilter] = None) -> PaginatedResponse[Activity]:
        """Get list of activities with optional filtering."""
        if filters is None:
            filters = ActivityFilter()
        
        params: Dict[str, Any] = {
            "start": filters.start,
            "limit": filters.limit,
        }
        
        if filters.deal_id:
            params["deal_id"] = filters.deal_id
        if filters.person_id:
            params["person_id"] = filters.person_id
        if filters.org_id:
            params["org_id"] = filters.org_id
        if filters.user_id:
            params["user_id"] = filters.user_id
        if filters.type:
            params["type"] = filters.type
        if filters.done is not None:
            params["done"] = 1 if filters.done else 0
        if filters.start_date:
            params["start_date"] = filters.start_date.isoformat()
        if filters.end_date:
            params["end_date"] = filters.end_date.isoformat()
        
        response = await self.client.get("/v1/activities", params=params)
        activities = [Activity(**a) for a in response.get("data", [])]
        
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None
        
        return PaginatedResponse(data=activities, pagination=pagination)

    async def get_activity(self, activity_id: int) -> Activity:
        """Get single activity by ID."""
        response = await self.client.get(f"/v1/activities/{activity_id}")
        activity_data = response.get("data")
        
        if not activity_data:
            raise PipedriveNotFoundError(f"Activity {activity_id} not found", "activity", activity_id)
        
        return Activity(**activity_data)

    async def create_activity(self, request: ActivityCreateRequest) -> Activity:
        """Create a new activity."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.post("/v1/activities", data=data)
        return Activity(**response.get("data"))

    async def update_activity(self, activity_id: int, request: ActivityUpdateRequest) -> Activity:
        """Update an existing activity."""
        data = request.model_dump(exclude_none=True)
        response = await self.client.put(f"/v1/activities/{activity_id}", data=data)
        return Activity(**response.get("data"))

    async def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity."""
        response = await self.client.delete(f"/v1/activities/{activity_id}")
        return response.get("success", False)

    async def mark_activity_done(self, activity_id: int) -> Activity:
        """Mark activity as done."""
        request = ActivityUpdateRequest(done=True)
        return await self.update_activity(activity_id, request)
