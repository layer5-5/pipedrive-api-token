"""
Layer55 API client for OAuth token retrieval.
"""
import os
import logging
from typing import Dict, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class Layer55Client:
    """Client for interacting with Layer55 API"""

    def __init__(self, api_url: Optional[str] = None, timeout: float = 10.0):
        """
        Initialize Layer55 API client.

        Args:
            api_url: Base URL of Layer55 API (if not provided, loads from env)
            timeout: Request timeout in seconds
        """
        self.api_url = (api_url or os.getenv("LAYER55_API_URL", "")).rstrip("/")
        if not self.api_url:
            raise ValueError("LAYER55_API_URL must be set in environment variables")

        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"Layer55 client initialized with API URL: {self.api_url}")

    async def get_oauth_tokens(
        self,
        server_id: str,
        jwt_token: str
    ) -> Dict[str, any]:
        """
        Retrieve OAuth tokens for a specific MCP server.

        Args:
            server_id: MCP server ID
            jwt_token: JWT token from Layer55 (contains user_id)

        Returns:
            Dict containing:
                - access_token: OAuth access token
                - refresh_token: OAuth refresh token (optional)
                - expires_at: Token expiration timestamp
                - token_type: Token type (e.g., "Bearer")
                - scope: OAuth scope (optional)

        Raises:
            httpx.HTTPStatusError: API returned error status
            httpx.RequestError: Network or connection error
            ValueError: Invalid response format
        """
        url = f"{self.api_url}/api/v1/mcp/servers/{server_id}/tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

        try:
            logger.debug(f"Fetching OAuth tokens for server_id: {server_id}")

            response = await self.client.get(url, headers=headers)

            # Handle different error scenarios
            if response.status_code == 401:
                logger.error("JWT token invalid or expired when fetching OAuth tokens")
                raise httpx.HTTPStatusError(
                    "Unauthorized: Invalid or expired JWT token",
                    request=response.request,
                    response=response
                )
            elif response.status_code == 403:
                logger.error(f"User does not own server {server_id}")
                raise httpx.HTTPStatusError(
                    f"Forbidden: User does not have access to server {server_id}",
                    request=response.request,
                    response=response
                )
            elif response.status_code == 404:
                logger.error(f"Server {server_id} not found")
                raise httpx.HTTPStatusError(
                    f"Not Found: Server {server_id} does not exist",
                    request=response.request,
                    response=response
                )
            elif response.status_code >= 500:
                logger.error(f"Layer55 API server error: {response.status_code}")
                raise httpx.HTTPStatusError(
                    "Layer55 API server error",
                    request=response.request,
                    response=response
                )

            response.raise_for_status()

            # Parse response
            data = response.json()

            # Validate required fields
            if "access_token" not in data:
                raise ValueError("Response missing 'access_token' field")

            logger.info(f"Successfully retrieved OAuth tokens for server {server_id}")

            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": data.get("expires_at"),
                "token_type": data.get("token_type", "Bearer"),
                "scope": data.get("scope")
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching tokens: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error fetching tokens: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching tokens: {e}")
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
