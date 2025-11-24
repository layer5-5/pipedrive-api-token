"""Deal management service with comprehensive lifecycle tracking."""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..client.pipedrive_client import PipedriveClient
from ..models.deal import (
    Deal,
    DealStatus,
    ComprehensiveDeal,
    DealProduct,
    StageChange,
    DealFilter,
    DealCreateRequest,
    DealUpdateRequest,
)
from ..models.common import Note, File, PaginatedResponse
from ..models.activity import Activity
from ..models.contact import Person
from ..models.user import User
from ..utils.errors import PipedriveNotFoundError, PipedriveValidationError
from ..config import settings

logger = logging.getLogger(__name__)


class DealService:
    """
    Deal management service providing:
    - Full CRUD operations
    - Comprehensive deal data retrieval
    - Lifecycle tracking
    - Activity associations
    - Product management
    - Stage history
    - Analytics
    """

    def __init__(self, client: PipedriveClient):
        """
        Initialize deal service.

        Args:
            client: Pipedrive API client
        """
        self.client = client

    async def get_deals(
        self,
        filters: Optional[DealFilter] = None,
    ) -> PaginatedResponse[Deal]:
        """
        Get list of deals with optional filtering.

        Args:
            filters: Filter parameters

        Returns:
            Paginated list of deals
        """
        if filters is None:
            filters = DealFilter()

        # Build query parameters
        params: Dict[str, Any] = {
            "start": filters.start,
            "limit": filters.limit,
        }

        if filters.status:
            params["status"] = filters.status.value
        if filters.pipeline_id:
            params["pipeline_id"] = filters.pipeline_id
        if filters.stage_id:
            params["stage_id"] = filters.stage_id
        if filters.owner_id:
            params["owner_id"] = filters.owner_id
        if filters.person_id:
            params["person_id"] = filters.person_id
        if filters.org_id:
            params["org_id"] = filters.org_id
        if filters.sort:
            params["sort"] = filters.sort

        logger.info(f"Getting deals with filters: {params}")

        response = await self.client.get("/v1/deals", params=params)

        deals = [Deal(**deal_data) for deal_data in response.get("data", [])]

        # Extract pagination info
        additional_data = response.get("additional_data", {})
        pagination_data = additional_data.get("pagination", {})

        from ..models.common import PaginationInfo

        pagination = (
            PaginationInfo(
                start=pagination_data.get("start", 0),
                limit=pagination_data.get("limit", filters.limit),
                more_items_in_collection=pagination_data.get(
                    "more_items_in_collection", False
                ),
                next_start=pagination_data.get("next_start"),
            )
            if pagination_data
            else None
        )

        return PaginatedResponse(data=deals, pagination=pagination)

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
        logger.info(f"Getting deal: {deal_id}")

        try:
            response = await self.client.get(f"/v1/deals/{deal_id}")
            deal_data = response.get("data")

            if not deal_data:
                raise PipedriveNotFoundError(
                    f"Deal {deal_id} not found",
                    resource_type="deal",
                    resource_id=deal_id,
                )

            return Deal(**deal_data)
        except PipedriveNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            raise

    async def get_comprehensive_deal(self, deal_id: int) -> ComprehensiveDeal:
        """
        Get comprehensive deal data including:
        - Basic deal info
        - All activities
        - All notes
        - All products
        - Stage history
        - All files
        - All participants
        - Computed metrics

        Args:
            deal_id: Deal ID

        Returns:
            Comprehensive deal object with all related data
        """
        logger.info(f"Getting comprehensive deal data for: {deal_id}")

        # Get basic deal info
        deal = await self.get_deal(deal_id)

        # Get all related data in parallel (for performance)
        import asyncio

        activities_task = self.get_deal_activities(deal_id)
        notes_task = self.get_deal_notes(deal_id)
        products_task = self.get_deal_products(deal_id)
        files_task = self.get_deal_files(deal_id)
        followers_task = self.get_deal_followers(deal_id)
        participants_task = self.get_deal_participants(deal_id)

        # Wait for all tasks to complete
        (
            activities,
            notes,
            products,
            files,
            followers,
            participants,
        ) = await asyncio.gather(
            activities_task,
            notes_task,
            products_task,
            files_task,
            followers_task,
            participants_task,
            return_exceptions=True,
        )

        # Handle exceptions (use empty list if fetch failed)
        activities = activities if not isinstance(activities, Exception) else []
        notes = notes if not isinstance(notes, Exception) else []
        products = products if not isinstance(products, Exception) else []
        files = files if not isinstance(files, Exception) else []
        followers = followers if not isinstance(followers, Exception) else []
        participants = participants if not isinstance(participants, Exception) else []

        # Compute metrics
        time_in_current_stage_days = None
        if deal.stage_change_time:
            time_in_current_stage_days = (datetime.now() - deal.stage_change_time).days

        total_product_value = sum(p.sum for p in products) if products else None

        # Create comprehensive deal object
        comprehensive_deal = ComprehensiveDeal(
            **deal.model_dump(),
            activities=activities,
            notes=notes,
            products=products,
            files=files,
            followers=followers,
            participants=participants,
            stage_history=[],  # TODO: Implement stage history
            time_in_current_stage_days=time_in_current_stage_days,
            total_stage_changes=0,  # TODO: Implement from stage history
            average_time_per_stage=None,  # TODO: Compute from stage history
            total_product_value=total_product_value,
        )

        return comprehensive_deal

    async def get_deal_activities(self, deal_id: int) -> List[Activity]:
        """Get all activities for a deal."""
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/activities")
            activities_data = response.get("data", [])
            return [Activity(**activity) for activity in activities_data]
        except Exception as e:
            logger.warning(f"Error fetching activities for deal {deal_id}: {e}")
            return []

    async def get_deal_notes(self, deal_id: int) -> List[Note]:
        """Get all notes for a deal."""
        try:
            # Use the general notes endpoint with deal filter
            response = await self.client.get("/v1/notes", params={"deal_id": deal_id})
            notes_data = response.get("data", [])
            return [Note(**note) for note in notes_data]
        except Exception as e:
            logger.warning(f"Error fetching notes for deal {deal_id}: {e}")
            return []

    async def get_deal_products(self, deal_id: int) -> List[DealProduct]:
        """Get all products for a deal."""
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/products")
            products_data = response.get("data", [])
            return [DealProduct(**product) for product in products_data]
        except Exception as e:
            logger.warning(f"Error fetching products for deal {deal_id}: {e}")
            return []

    async def get_deal_files(self, deal_id: int) -> List[File]:
        """Get all files for a deal."""
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/files")
            files_data = response.get("data", [])
            return [File(**file) for file in files_data]
        except Exception as e:
            logger.warning(f"Error fetching files for deal {deal_id}: {e}")
            return []

    async def get_deal_followers(self, deal_id: int) -> List[User]:
        """Get all followers for a deal."""
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/followers")
            followers_data = response.get("data", [])
            return [User(**follower) for follower in followers_data]
        except Exception as e:
            logger.warning(f"Error fetching followers for deal {deal_id}: {e}")
            return []

    async def get_deal_participants(self, deal_id: int) -> List[Person]:
        """Get all participants for a deal."""
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/participants")
            participants_data = response.get("data", [])
            return [Person(**participant) for participant in participants_data]
        except Exception as e:
            logger.warning(f"Error fetching participants for deal {deal_id}: {e}")
            return []

    async def create_deal(self, request: DealCreateRequest) -> Deal:
        """
        Create a new deal.

        Args:
            request: Deal creation request

        Returns:
            Created deal
        """
        logger.info(f"Creating deal: {request.title}")

        # Convert request to API format
        data = request.model_dump(exclude_none=True)

        response = await self.client.post("/v1/deals", data=data)
        deal_data = response.get("data")

        return Deal(**deal_data)

    async def update_deal(self, deal_id: int, request: DealUpdateRequest) -> Deal:
        """
        Update an existing deal.

        Args:
            deal_id: Deal ID
            request: Deal update request

        Returns:
            Updated deal
        """
        logger.info(f"Updating deal: {deal_id}")

        # Convert request to API format
        data = request.model_dump(exclude_none=True)

        response = await self.client.put(f"/v1/deals/{deal_id}", data=data)
        deal_data = response.get("data")

        return Deal(**deal_data)

    async def delete_deal(self, deal_id: int) -> bool:
        """
        Delete a deal.

        Args:
            deal_id: Deal ID

        Returns:
            True if successful
        """
        logger.info(f"Deleting deal: {deal_id}")

        response = await self.client.delete(f"/v1/deals/{deal_id}")
        return response.get("success", False)

    async def move_deal_to_stage(
        self,
        deal_id: int,
        stage_id: int,
    ) -> Deal:
        """
        Move deal to a different stage.

        Args:
            deal_id: Deal ID
            stage_id: Target stage ID

        Returns:
            Updated deal
        """
        logger.info(f"Moving deal {deal_id} to stage {stage_id}")

        request = DealUpdateRequest(stage_id=stage_id)
        return await self.update_deal(deal_id, request)

    async def win_deal(
        self,
        deal_id: int,
        close_date: Optional[date] = None,
    ) -> Deal:
        """
        Mark deal as won.

        Args:
            deal_id: Deal ID
            close_date: Close date (defaults to today)

        Returns:
            Updated deal
        """
        logger.info(f"Marking deal {deal_id} as won")

        if close_date is None:
            close_date = date.today()

        request = DealUpdateRequest(
            status=DealStatus.WON,
            close_time=datetime.combine(close_date, datetime.min.time()),
        )
        return await self.update_deal(deal_id, request)

    async def lose_deal(
        self,
        deal_id: int,
        lost_reason: Optional[str] = None,
        close_date: Optional[date] = None,
    ) -> Deal:
        """
        Mark deal as lost.

        Args:
            deal_id: Deal ID
            lost_reason: Reason for losing
            close_date: Close date (defaults to today)

        Returns:
            Updated deal
        """
        logger.info(f"Marking deal {deal_id} as lost: {lost_reason}")

        if close_date is None:
            close_date = date.today()

        request = DealUpdateRequest(
            status=DealStatus.LOST,
            lost_reason=lost_reason,
            close_time=datetime.combine(close_date, datetime.min.time()),
        )
        return await self.update_deal(deal_id, request)

    async def add_product_to_deal(
        self,
        deal_id: int,
        product_id: int,
        item_price: Decimal,
        quantity: int = 1,
        **kwargs,
    ) -> DealProduct:
        """
        Add a product to a deal.

        Args:
            deal_id: Deal ID
            product_id: Product ID
            item_price: Unit price
            quantity: Quantity
            **kwargs: Additional product parameters

        Returns:
            Created deal product
        """
        logger.info(f"Adding product {product_id} to deal {deal_id}")

        data = {
            "product_id": product_id,
            "item_price": float(item_price),
            "quantity": quantity,
            **kwargs,
        }

        response = await self.client.post(f"/v1/deals/{deal_id}/products", data=data)
        product_data = response.get("data")

        return DealProduct(**product_data)

    async def add_note_to_deal(
        self,
        deal_id: int,
        content: str,
    ) -> Note:
        """
        Add a note to a deal.

        Args:
            deal_id: Deal ID
            content: Note content

        Returns:
            Created note
        """
        logger.info(f"Adding note to deal {deal_id}")

        data = {
            "deal_id": deal_id,
            "content": content,
        }

        response = await self.client.post("/v1/notes", data=data)
        note_data = response.get("data")

        return Note(**note_data)

    async def get_deal_flow(self, deal_id: int) -> List[Dict[str, Any]]:
        """
        Get deal flow/updates (timeline of changes).

        Args:
            deal_id: Deal ID

        Returns:
            List of flow/update items
        """
        try:
            response = await self.client.get(f"/v1/deals/{deal_id}/flow")
            return response.get("data", [])
        except Exception as e:
            logger.warning(f"Error fetching deal flow for {deal_id}: {e}")
            return []

    async def search_deals(
        self,
        term: str,
        limit: int = 100,
    ) -> List[Deal]:
        """
        Search deals by term.

        Args:
            term: Search term
            limit: Maximum results

        Returns:
            List of matching deals
        """
        logger.info(f"Searching deals for: {term}")

        params = {
            "term": term,
            "item_type": "deal",
            "limit": limit,
        }

        response = await self.client.get("/v1/itemSearch", params=params)
        items = response.get("data", {}).get("items", [])

        # Extract deal data from search results
        deals = []
        for item in items:
            if item.get("item", {}).get("type") == "deal":
                deal_data = item.get("item", {})
                deals.append(Deal(**deal_data))

        return deals
