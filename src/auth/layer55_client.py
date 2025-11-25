"""Layer55 API client for retrieving user tokens."""

import logging
from typing import Optional

import httpx
from fastapi import HTTPException, Request

from ..config import settings

logger = logging.getLogger(__name__)


class Layer55Client:
    """Client for communicating with Layer55 API backend."""

    def __init__(self):
        self.base_url = settings.layer55_api_url
        self.server_id = settings.pipedrive_server_id

    async def get_user_pipedrive_token(self, request: Request) -> str:
        """
        Get Pipedrive API token for a user from Layer55 backend.

        Args:
            request: FastAPI request object for forwarding headers

        Returns:
            Pipedrive API token

        Raises:
            HTTPException: If token retrieval fails
        """
        # Forward the original JWT token to Layer55 API
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401, detail="No authorization token provided"
            )

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/api/v1/mcp/servers/{self.server_id}/tokens"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if not token:
                        raise HTTPException(
                            status_code=500, detail="No token returned from Layer55 API"
                        )
                    logger.info(f"Retrieved API token with length: {len(token)}")
                    return token
                else:
                    logger.error(
                        f"Layer55 API error: {response.status_code} - {response.text}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to retrieve token from Layer55 API: {response.text}",
                    )

        except httpx.RequestError as e:
            logger.error(f"Request to Layer55 API failed: {e}")
            raise HTTPException(status_code=503, detail="Layer55 API unavailable")

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/internal/mcp/{self.server_id}/token"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if not token:
                        raise HTTPException(
                            status_code=500, detail="No token returned from Layer55 API"
                        )
                    logger.info(f"Retrieved API token with length: {len(token)}")
                    return token
                else:
                    logger.error(
                        f"Layer55 API error: {response.status_code} - {response.text}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to retrieve token from Layer55 API: {response.text}",
                    )

        except httpx.RequestError as e:
            logger.error(f"Request to Layer55 API failed: {e}")
            raise HTTPException(status_code=503, detail="Layer55 API unavailable")

    async def get_user_info(self, request: Request) -> dict:
        """
        Get user information from Layer55 backend.

        Args:
            request: FastAPI request object

        Returns:
            User information dictionary

        Raises:
            HTTPException: If user info retrieval fails
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401, detail="No authorization token provided"
            )

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/internal/mcp/{self.server_id}/user"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        f"Layer55 API error: {response.status_code} - {response.text}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to retrieve user info from Layer55 API: {response.text}",
                    )

        except httpx.RequestError as e:
            logger.error(f"Request to Layer55 API failed: {e}")
            raise HTTPException(status_code=503, detail="Layer55 API unavailable")


# Global client instance
layer55_client = Layer55Client()


async def get_pipedrive_token_from_layer55(request: Request) -> str:
    """
    Get Pipedrive token from Layer55 backend.

    This function calls Layer55 API to get the user's Pipedrive API token.
    Layer55 handles the JWT validation.

    Args:
        request: FastAPI request object

    Returns:
        Pipedrive API token
    """
    return await layer55_client.get_user_pipedrive_token(request)
