"""
Pipedrive client wrapper using official python-pipedrive package
"""

import logging
from typing import Dict, List, Optional, Any
import pipedrive

logger = logging.getLogger(__name__)


class PipedriveOfficialClient:
    """Client for Pipedrive API using official python-pipedrive package"""

    def __init__(self, api_token: str):
        """
        Initialize Pipedrive client with official package

        Args:
            api_token: Pipedrive API token
        """
        self.pipedrive = pipedrive.Pipedrive(api_token)
        logger.info("Pipedrive official client initialized")

    async def get_deals(
        self,
        status: Optional[str] = None,
        stage_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get deals with optional filters"""
        params = {"start": start, "limit": limit}
        if status:
            params["status"] = status
        if stage_id is not None:
            params["stage_id"] = stage_id
        if pipeline_id is not None:
            params["pipeline_id"] = pipeline_id

        try:
            response = self.pipedrive.request("GET", "/deals", params)
            return response.get("data", []) if isinstance(response, dict) else []
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            raise

    async def get_deal(self, deal_id: int) -> Dict:
        """Get single deal by ID"""
        try:
            response = self.pipedrive.request("GET", "/deals", {"id": deal_id})
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            raise

    async def create_deal(self, data: Dict) -> Dict:
        """Create new deal"""
        try:
            response = self.pipedrive.request("POST", "/deals", data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            raise

    async def update_deal(self, deal_id: int, data: Dict) -> Dict:
        """Update deal"""
        try:
            update_data = {**data, "id": deal_id}
            response = self.pipedrive.request("PUT", "/deals", update_data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            raise

    async def create_deal(self, data: Dict) -> Dict:
        """Create new deal"""
        try:
            response = self.pipedrive.deals(data, method="POST")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            raise

    async def update_deal(self, deal_id: int, data: Dict) -> Dict:
        """Update deal"""
        try:
            update_data = {**data, "id": deal_id}
            response = self.pipedrive.deals(update_data, method="PUT")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            raise

    async def get_deal_activities(self, deal_id: int) -> List[Dict]:
        """Get activities for a deal"""
        try:
            response = self.pipedrive.request(
                "GET", "/activities", {"deal_id": deal_id}
            )
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting deal activities for {deal_id}: {e}")
            raise

    async def get_deal_notes(self, deal_id: int) -> List[Dict]:
        """Get notes for a deal"""
        try:
            response = self.pipedrive.request("GET", "/notes", {"deal_id": deal_id})
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting deal notes for {deal_id}: {e}")
            raise

    async def get_persons(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get contacts/persons"""
        params = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        try:
            response = self.pipedrive.request("GET", "/persons", params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting persons: {e}")
            raise

    async def get_person(self, person_id: int) -> Dict:
        """Get single person by ID"""
        try:
            response = self.pipedrive.request("GET", "/persons", {"id": person_id})
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting person {person_id}: {e}")
            raise

    async def create_person(self, data: Dict) -> Dict:
        """Create new person"""
        try:
            response = self.pipedrive.request("POST", "/persons", data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating person: {e}")
            raise

    async def update_person(self, person_id: int, data: Dict) -> Dict:
        """Update person"""
        try:
            update_data = {**data, "id": person_id}
            response = self.pipedrive.request("PUT", "/persons", update_data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error updating person {person_id}: {e}")
            raise

    async def get_organizations(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get organizations/companies"""
        params = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        try:
            response = self.pipedrive.request("GET", "/organizations", params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting organizations: {e}")
            raise

    async def get_organization(self, org_id: int) -> Dict:
        """Get single organization by ID"""
        try:
            response = self.pipedrive.request("GET", "/organizations", {"id": org_id})
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            raise

    async def create_organization(self, data: Dict) -> Dict:
        """Create new organization"""
        try:
            response = self.pipedrive.request("POST", "/organizations", data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise

    async def get_activities(
        self,
        type_filter: Optional[str] = None,
        done: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get activities"""
        params = {"start": start, "limit": limit}
        if type_filter:
            params["type"] = type_filter
        if done is not None:
            params["done"] = done

        try:
            response = self.pipedrive.request("GET", "/activities", params)
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            raise

    async def create_activity(self, data: Dict) -> Dict:
        """Create new activity"""
        try:
            response = self.pipedrive.request("POST", "/activities", data)
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise

    async def get_users(self) -> List[Dict]:
        """Get all users in account"""
        try:
            response = self.pipedrive.request("GET", "/users", {})
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise

    async def get_user(self, user_id: int) -> Dict:
        """Get single user by ID"""
        try:
            response = self.pipedrive.request("GET", "/users", {"id": user_id})
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise

    async def get_deal_notes(self, deal_id: int) -> List[Dict]:
        """Get notes for a deal"""
        try:
            response = self.pipedrive.notes({"deal_id": deal_id}, method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting deal notes for {deal_id}: {e}")
            raise

    async def get_persons(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get contacts/persons"""
        params = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        try:
            response = self.pipedrive.persons(params, method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting persons: {e}")
            raise

    async def get_person(self, person_id: int) -> Dict:
        """Get single person by ID"""
        try:
            response = self.pipedrive.persons({"id": person_id}, method="GET")
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting person {person_id}: {e}")
            raise

    async def create_person(self, data: Dict) -> Dict:
        """Create new person"""
        try:
            response = self.pipedrive.persons(data, method="POST")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating person: {e}")
            raise

    async def update_person(self, person_id: int, data: Dict) -> Dict:
        """Update person"""
        try:
            update_data = {**data, "id": person_id}
            response = self.pipedrive.persons(update_data, method="PUT")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error updating person {person_id}: {e}")
            raise

    async def get_organizations(
        self, filter_id: Optional[int] = None, start: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Get organizations/companies"""
        params = {"start": start, "limit": limit}
        if filter_id:
            params["filter_id"] = filter_id

        try:
            response = self.pipedrive.organizations(params, method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting organizations: {e}")
            raise

    async def get_organization(self, org_id: int) -> Dict:
        """Get single organization by ID"""
        try:
            response = self.pipedrive.organizations({"id": org_id}, method="GET")
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            raise

    async def create_organization(self, data: Dict) -> Dict:
        """Create new organization"""
        try:
            response = self.pipedrive.organizations(data, method="POST")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise

    async def get_activities(
        self,
        type_filter: Optional[str] = None,
        done: Optional[int] = None,
        start: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        """Get activities"""
        params = {"start": start, "limit": limit}
        if type_filter:
            params["type"] = type_filter
        if done is not None:
            params["done"] = done

        try:
            response = self.pipedrive.activities(params, method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting activities: {e}")
            raise

    async def create_activity(self, data: Dict) -> Dict:
        """Create new activity"""
        try:
            response = self.pipedrive.activities(data, method="POST")
            return response.get("data", {})
        except Exception as e:
            logger.error(f"Error creating activity: {e}")
            raise

    async def get_users(self) -> List[Dict]:
        """Get all users in account"""
        try:
            response = self.pipedrive.users(method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise

    async def get_user(self, user_id: int) -> Dict:
        """Get single user by ID"""
        try:
            response = self.pipedrive.users({"id": user_id}, method="GET")
            data = response.get("data", [])
            return data[0] if isinstance(data, list) and data else {}
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise

    async def close(self):
        """Close client (no-op for official package)"""
        # Official package doesn't require explicit cleanup
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
