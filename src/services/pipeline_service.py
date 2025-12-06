"""Pipeline and stage management service."""

import logging
from typing import List, Optional, Dict, Any

from ..client.pipedrive_client import PipedriveClient
from ..models.pipeline import Pipeline, Stage
from ..models.common import PaginatedResponse, PaginationInfo
from ..utils.errors import PipedriveNotFoundError, PipedriveAPIError

logger = logging.getLogger(__name__)


class PipelineService:
    """Pipeline and stage management service."""

    def __init__(self, client: PipedriveClient):
        self.client = client

    async def get_pipelines(self) -> List[Pipeline]:
        """Get all pipelines."""
        response = await self.client.get("/v1/pipelines")

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get pipelines: {error_message}")

        pipelines_data = response.get("data", [])

        pipelines = []
        for pipeline_data in pipelines_data:
            # Convert stages if present
            stages_data = pipeline_data.get("stages", [])
            stages = [Stage(**stage_data) for stage_data in stages_data]

            # Create pipeline with stages
            pipeline_dict = {**pipeline_data, "stages": stages}
            pipelines.append(Pipeline(**pipeline_dict))

        return pipelines

    async def get_pipeline(self, pipeline_id: int) -> Pipeline:
        """Get single pipeline by ID."""
        response = await self.client.get(f"/v1/pipelines/{pipeline_id}")

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get pipeline: {error_message}")

        pipeline_data = response.get("data")

        if not pipeline_data:
            raise PipedriveNotFoundError(
                f"Pipeline {pipeline_id} not found", "pipeline", pipeline_id
            )

        # Convert stages if present
        stages_data = pipeline_data.get("stages", [])
        stages = [Stage(**stage_data) for stage_data in stages_data]

        # Create pipeline with stages
        pipeline_dict = {**pipeline_data, "stages": stages}
        return Pipeline(**pipeline_dict)

    async def get_stages(
        self,
        pipeline_id: Optional[int] = None,
        sort_by: str = "id",
        sort_direction: str = "asc",
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> PaginatedResponse[Stage]:
        """
        Get stages with optional filtering.

        Args:
            pipeline_id: Filter by pipeline ID (optional)
            sort_by: Sort field (id, update_time, add_time, order_nr)
            sort_direction: Sort direction (asc, desc)
            limit: Pagination limit
            cursor: Pagination cursor
        """
        params: Dict[str, Any] = {
            "sort_by": sort_by,
            "sort_direction": sort_direction,
        }

        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor

        response = await self.client.get("/v2/stages", params=params)

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get stages: {error_message}")

        stages_data = response.get("data", [])
        stages = [Stage(**stage_data) for stage_data in stages_data]

        # Handle pagination
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None

        return PaginatedResponse(data=stages, pagination=pagination)

    async def get_pipeline_stages(self, pipeline: Optional[str] = None) -> List[Stage]:
        """
        Get all pipeline stages (accepts either pipeline name or ID).

        Args:
            pipeline: Pipeline name (e.g., 'Sales Pipeline') or ID (e.g., 1).
                     If not provided, uses default pipeline.

        Returns:
            List of stages
        """
        if pipeline is None:
            # Get default pipeline stages
            pipelines = await self.get_pipelines()
            if pipelines:
                default_pipeline = pipelines[0]  # First pipeline is usually default
                return default_pipeline.stages or []
            return []

        # Check if pipeline is numeric (ID) or string (name)
        try:
            pipeline_id = int(pipeline)
            # Get specific pipeline by ID
            pipeline_obj = await self.get_pipeline(pipeline_id)
            return pipeline_obj.stages or []
        except ValueError:
            # Pipeline is a name, search for it
            pipelines = await self.get_pipelines()
            for pipeline_obj in pipelines:
                if pipeline_obj.name and pipeline_obj.name.lower() == pipeline.lower():
                    return pipeline_obj.stages or []
            raise PipedriveNotFoundError(
                f"Pipeline '{pipeline}' not found",
                resource_type="pipeline",
                resource_id=pipeline,
            )

    async def get_stage(self, stage_id: int) -> Stage:
        """Get single stage by ID."""
        response = await self.client.get(f"/v2/stages/{stage_id}")

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get stage: {error_message}")

        stage_data = response.get("data")

        if not stage_data:
            raise PipedriveNotFoundError(
                f"Stage {stage_id} not found", "stage", stage_id
            )

        return Stage(**stage_data)

    async def get_deals_in_stage(
        self,
        stage_id: int,
        filter_id: Optional[int] = None,
        user_id: Optional[int] = None,
        everyone: Optional[bool] = None,
        start: int = 0,
        limit: int = 100,
    ) -> PaginatedResponse:
        """
        Get deals in a specific stage.

        Note: This endpoint is deprecated in v1, use deals endpoint with stage_id filter instead.
        """
        from ..models.deal import Deal

        params: Dict[str, Any] = {
            "start": start,
            "limit": limit,
        }

        if filter_id:
            params["filter_id"] = filter_id
        if user_id:
            params["user_id"] = user_id
        if everyone is not None:
            params["everyone"] = 1 if everyone else 0

        response = await self.client.get(f"/v1/stages/{stage_id}/deals", params=params)

        if not response.get("success", True):
            error_message = response.get("error", "Unknown error")
            raise PipedriveAPIError(f"Failed to get deals in stage: {error_message}")

        deals_data = response.get("data", [])
        deals = [Deal(**deal_data) for deal_data in deals_data]

        # Handle pagination
        pagination_data = response.get("additional_data", {}).get("pagination", {})
        pagination = PaginationInfo(**pagination_data) if pagination_data else None

        return PaginatedResponse(data=deals, pagination=pagination)
