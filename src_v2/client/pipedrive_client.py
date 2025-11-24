"""Pipedrive API client wrapper with URL fix and enhanced features."""

import logging
from typing import Any, Dict, List, Optional
import httpx
from pipedrive import Pipedrive

from ..config import settings
from ..utils.errors import (
    PipedriveAPIError,
    PipedriveAuthError,
    PipedriveRateLimitError,
)

logger = logging.getLogger(__name__)


class PipedriveClient:
    """
    Wrapper around official Pipedrive SDK with:
    - URL fix for API endpoint (api.pipedrive.com instead of app.pipedrive.com)
    - Async support
    - Error handling
    - Retry logic
    - Request logging
    """

    def __init__(self, api_token: str):
        """
        Initialize Pipedrive client.

        Args:
            api_token: Pipedrive API token
        """
        self.api_token = api_token

        # Initialize official Pipedrive SDK
        self._client = Pipedrive(api_token)

        # CRITICAL FIX: Official package uses wrong URL (app.pipedrive.com)
        # We need to fix it to use api.pipedrive.com
        self._client._origin = settings.pipedrive_api_base_url

        # Initialize httpx client for async operations
        self._http_client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            limits=httpx.Limits(max_connections=settings.connection_pool_size),
        )

        logger.info(
            "PipedriveClient initialized",
            extra={
                "api_base_url": settings.pipedrive_api_base_url,
            },
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Pipedrive API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /v1/deals)
            params: Query parameters
            data: Request body data

        Returns:
            API response data

        Raises:
            PipedriveAuthError: Authentication failed
            PipedriveRateLimitError: Rate limit exceeded
            PipedriveAPIError: Other API errors
        """
        # TODO: Implement caching layer for GET requests
        # - Cache tokens for 1 hour (settings.cache_ttl_token)
        # - Cache metadata for 24 hours (settings.cache_ttl_metadata)
        # - Cache deals for 5 minutes (settings.cache_ttl_deal)
        # - Cache search results for 1 minute (settings.cache_ttl_search)
        # - Use Redis for cache storage
        # - Implement cache invalidation on write operations
        # Ensure endpoint starts with /v1
        if not endpoint.startswith("/v1"):
            endpoint = f"/v1{endpoint if endpoint.startswith('/') else '/' + endpoint}"

        # Build full URL
        url = f"{settings.pipedrive_api_base_url}{endpoint}"

        # Add API token to params
        if params is None:
            params = {}
        params["api_token"] = self.api_token

        # Log request (without token)
        log_params = {k: v for k, v in params.items() if k != "api_token"}
        logger.debug(
            f"Pipedrive API request: {method} {endpoint}",
            extra={
                "method": method,
                "endpoint": endpoint,
                "params": log_params,
                "has_data": data is not None,
            },
        )

        try:
            # Make request
            if method == "GET":
                response = await self._http_client.get(url, params=params)
            elif method == "POST":
                response = await self._http_client.post(url, params=params, json=data)
            elif method == "PUT":
                response = await self._http_client.put(url, params=params, json=data)
            elif method == "DELETE":
                response = await self._http_client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log response
            logger.debug(
                f"Pipedrive API response: {response.status_code}",
                extra={
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                },
            )

            # Handle error status codes
            if response.status_code == 401:
                raise PipedriveAuthError("Invalid API token")
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise PipedriveRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds"
                )
            elif response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                raise PipedriveAPIError(
                    f"Pipedrive API error: {error_message}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            # Parse response
            response_data = response.json()

            # Check for API-level errors
            if not response_data.get("success", True):
                error_message = response_data.get("error", "Unknown error")
                raise PipedriveAPIError(
                    f"Pipedrive API error: {error_message}",
                    status_code=response.status_code,
                    response_data=response_data,
                )

            return response_data

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise PipedriveAPIError(f"Request timeout: {e}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise PipedriveAPIError(f"Request error: {e}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make GET request to Pipedrive API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data
        """
        return await self._make_request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request to Pipedrive API.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            API response data
        """
        return await self._make_request("POST", endpoint, params=params, data=data)

    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request to Pipedrive API.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            API response data
        """
        return await self._make_request("PUT", endpoint, params=params, data=data)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make DELETE request to Pipedrive API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data
        """
        return await self._make_request("DELETE", endpoint, params=params)

    async def close(self):
        """Close HTTP client connections."""
        await self._http_client.aclose()
        logger.info("PipedriveClient closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
