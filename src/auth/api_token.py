"""
Pipedrive API token authentication handler.
"""

import os
import logging
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class PipedriveApiTokenAuth:
    """Handler for Pipedrive API token authentication"""

    PIPEDRIVE_API_BASE_URL = "https://api.pipedrive.com/v1"

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize API token handler.

        Args:
            api_token: Pipedrive API token (if not provided, loads from env)
        """
        self.api_token = api_token or os.getenv("PIPEDRIVE_API_TOKEN")

        if not self.api_token:
            raise ValueError(
                "API token must be provided either as parameter or via PIPEDRIVE_API_TOKEN environment variable"
            )

        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Pipedrive API token handler initialized")

    async def test_connection(self) -> Dict:
        """
        Test the API token by making a simple API call.

        Returns:
            User information from Pipedrive

        Raises:
            httpx.HTTPStatusError: API request failed
            ValueError: Invalid token or response
        """
        try:
            logger.debug("Testing API token connection")

            response = await self.client.get(
                f"{self.PIPEDRIVE_API_BASE_URL}/users/me",
                params={"api_token": self.api_token},
                headers={"Accept": "application/json"},
            )

            logger.debug(f"API response status: {response.status_code}")

            if response.status_code == 401:
                raise ValueError("Invalid API token")
            elif response.status_code == 403:
                raise ValueError("API token does not have required permissions")
            elif response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    "Pipedrive API server error",
                    request=response.request,
                    response=response,
                )

            response.raise_for_status()

            user_data = response.json()

            if not user_data.get("success", False):
                error_msg = user_data.get("error", "Unknown error")
                raise ValueError(f"API test failed: {error_msg}")

            logger.info("API token validation successful")
            return user_data.get("data", {})

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error testing API token: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error testing API token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error testing API token: {e}")
            raise

    async def make_api_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make an authenticated API request to Pipedrive.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for httpx request

        Returns:
            API response data

        Raises:
            httpx.HTTPStatusError: API request failed
            ValueError: Invalid response
        """
        url = f"{self.PIPEDRIVE_API_BASE_URL}/{endpoint.lstrip('/')}"

        # Add API token to params
        params = kwargs.get("params", {})
        params["api_token"] = self.api_token
        kwargs["params"] = params

        try:
            response = await self.client.request(method, url, **kwargs)

            if response.status_code >= 400:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                response.raise_for_status()

            response_data = response.json()

            if not response_data.get("success", False):
                error_msg = response_data.get("error", "Unknown API error")
                raise ValueError(f"API error: {error_msg}")

            return response_data.get("data", {})

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in API request: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error in API request: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            raise

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
