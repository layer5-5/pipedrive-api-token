"""
Pipedrive API client for CRM data access using official python-pipedrive package.
"""

import logging
from typing import Dict, List, Optional, Any, Union
import pipedrive
from datetime import datetime

try:
    from .models import (
        EnhancedDeal,
        DealProduct,
        StageChange,
        EnhancedPerson,
        EnhancedOrganization,
        EnhancedActivity,
        EnhancedUser,
        Product,
        validate_deal_data,
        validate_person_data,
        validate_organization_data,
    )
except ImportError:
    # Fallback for development
    EnhancedDeal = DealProduct = StageChange = EnhancedPerson = None
    EnhancedOrganization = EnhancedActivity = EnhancedUser = Product = None
    validate_deal_data = validate_person_data = validate_organization_data = None

logger = logging.getLogger(__name__)


class PipedriveClient:
    """Client for Pipedrive API v1 using official python-pipedrive package"""

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_auth: Optional[Any] = None,
        api_token_auth: Optional[Any] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Pipedrive API client using official package.

        Args:
            access_token: Pipedrive OAuth access token (for OAuth flow)
            client_auth: PipedriveClientAuth instance (for client credentials flow)
            api_token_auth: PipedriveApiTokenAuth instance (for API token flow)
            timeout: Request timeout in seconds
        """
        auth_provided = sum(
            bool(x) for x in [access_token, client_auth, api_token_auth]
        )
        if auth_provided != 1:
            raise ValueError(
                "Exactly one of access_token, client_auth, or api_token_auth must be provided"
            )

        # Get the actual API token based on auth method
        if client_auth:
            # For OAuth, we'd need to get token from client_auth
            raise NotImplementedError(
                "OAuth client credentials not yet implemented with official package"
            )
        elif api_token_auth:
            actual_token = api_token_auth.api_token
        else:
            actual_token = access_token

        self.pipedrive = pipedrive.Pipedrive(actual_token)
        self.timeout = timeout
        logger.info("Pipedrive client initialized with official package")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make request to Pipedrive API using official package.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/deals")
            params: Query parameters
            json_data: JSON body for POST/PUT requests

        Returns:
            Response data dict

        Raises:
            Exception: API returned error
        """
        try:
            logger.debug(f"{method} {endpoint}")

            # Use official package's request method
            if params:
                request_params = params
            else:
                request_params = {}

            if json_data:
                response = self.pipedrive.request(method, endpoint, json_data)
            else:
                response = self.pipedrive.request(method, endpoint, request_params)

            # Official package returns the full response
            if not response.get("success", True):
                error = response.get("error", "Unknown error")
                logger.error(f"Pipedrive API error: {error}")
                raise ValueError(f"Pipedrive API error: {error}")

            return response.get("data", response)

        except Exception as e:
            logger.error(f"Pipedrive API error: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Pipedrive API network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Pipedrive API unexpected error: {e}")
            raise

    # Deal methods
    async def get_deals(
        self,
        status: Optional[str] = None,
        stage_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get deals with optional filters"""
        params: Dict[str, Any] = {"start": start, "limit": limit}
        if status:
            params["status"] = status
        if stage_id is not None:
            params["stage_id"] = stage_id
        if pipeline_id is not None:
            params["pipeline_id"] = pipeline_id

        data = await self._make_request("GET", "/deals", params=params)
        return data if isinstance(data, list) else []

    async def get_deal(self, deal_id: int) -> Dict:
        """Get single deal by ID"""
        data = await self._make_request("GET", "/deals", {"id": deal_id})
        return data[0] if isinstance(data, list) and data else {}

    async def create_deal(self, data: Dict) -> Dict:
        """Create new deal"""
        return await self._make_request("POST", "/deals", json_data=data)

    async def update_deal(self, deal_id: int, data: Dict) -> Dict:
        """Update deal"""
        update_data = {**data, "id": deal_id}
        return await self._make_request("PUT", "/deals", json_data=update_data)

    async def get_deal_activities(self, deal_id: int) -> List[Dict]:
        """Get activities for a deal"""
        data = await self._make_request("GET", "/activities", {"deal_id": deal_id})
        return data if isinstance(data, list) else []

    async def get_deal_notes(self, deal_id: int) -> List[Dict]:
        """Get notes for a deal"""
        data = await self._make_request("GET", "/notes", {"deal_id": deal_id})
        return data if isinstance(data, list) else []

    # Person methods
    async def get_persons(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get contacts/persons"""
        params: Dict[str, Any] = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        data = await self._make_request("GET", "/persons", params=params)
        return data if isinstance(data, list) else []

    async def get_person(self, person_id: int) -> Dict:
        """Get single person by ID"""
        data = await self._make_request("GET", "/persons", {"id": person_id})
        return data[0] if isinstance(data, list) and data else {}

    async def create_person(self, data: Dict) -> Dict:
        """Create new person"""
        return await self._make_request("POST", "/persons", json_data=data)

    async def update_person(self, person_id: int, data: Dict) -> Dict:
        """Update person"""
        update_data = {**data, "id": person_id}
        return await self._make_request("PUT", "/persons", json_data=update_data)

    # Organization methods
    async def get_organizations(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get organizations/companies"""
        params: Dict[str, Any] = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        data = await self._make_request("GET", "/organizations", params=params)
        return data if isinstance(data, list) else []

    async def get_organization(self, org_id: int) -> Dict:
        """Get single organization by ID"""
        data = await self._make_request("GET", "/organizations", {"id": org_id})
        return data[0] if isinstance(data, list) and data else {}

    async def create_organization(self, data: Dict) -> Dict:
        """Create new organization"""
        return await self._make_request("POST", "/organizations", json_data=data)

    # Activity methods
    async def get_activities(
        self,
        type_filter: Optional[str] = None,
        done: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get activities"""
        params: Dict[str, Any] = {"start": start, "limit": limit}
        if type_filter:
            params["type"] = type_filter
        if done is not None:
            params["done"] = done

        data = await self._make_request("GET", "/activities", params=params)
        return data if isinstance(data, list) else []

    async def create_activity(self, data: Dict) -> Dict:
        """Create new activity"""
        return await self._make_request("POST", "/activities", json_data=data)

    # User methods
    async def get_users(self) -> List[Dict]:
        """Get all users in account"""
        data = await self._make_request("GET", "/users")
        return data if isinstance(data, list) else []

    async def get_user(self, user_id: int) -> Dict:
        """Get single user by ID"""
        data = await self._make_request("GET", "/users", {"id": user_id})
        return data[0] if isinstance(data, list) and data else {}

    async def close(self):
        """Close client (no-op for official package)"""
        # Official package doesn't require explicit cleanup
        pass

        try:
            if isinstance(date_string, str):
                date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            else:
                date = date_string

            hours = (datetime.now(date.tzinfo) - date).total_seconds() / 3600
            return int(hours)
        except Exception:
            return None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
