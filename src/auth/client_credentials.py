"""
Pipedrive client credentials authentication handler.
"""

import os
import logging
from typing import Dict, Optional
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PipedriveClientAuth:
    """Handler for Pipedrive client credentials authentication"""

    OAUTH_TOKEN_URL = "https://oauth.pipedrive.com/oauth/token"

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None
    ):
        """
        Initialize client credentials handler.

        Args:
            client_id: Pipedrive OAuth client ID (if not provided, loads from env)
            client_secret: Pipedrive OAuth client secret (if not provided, loads from env)
        """
        self.client_id = client_id or os.getenv("PIPEDRIVE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PIPEDRIVE_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Both client_id and client_secret must be provided either as parameters "
                "or via PIPEDRIVE_CLIENT_ID and PIPEDRIVE_CLIENT_SECRET environment variables"
            )

        self.access_token = None
        self.token_expires_at = None
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Pipedrive client credentials handler initialized")

    async def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token for Pipedrive API

        Raises:
            httpx.HTTPStatusError: OAuth token request failed
            ValueError: Invalid credentials or response
        """
        # Check if current token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.debug("Using cached access token")
                return self.access_token

        # Request new access token
        return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """
        Request a new access token using client credentials flow.

        Returns:
            New access token

        Raises:
            httpx.HTTPStatusError: Token request failed
            ValueError: Invalid response
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "deals:read contacts:read activities:read organizations:read",
        }

        try:
            logger.debug("Requesting new access token using client credentials")
            logger.debug(f"Client ID: {self.client_id}")
            logger.debug(
                f"Client Secret length: {len(self.client_secret) if self.client_secret else 0}"
            )
            logger.debug(
                f"Request data: {{grant_type: 'client_credentials', client_id: '{self.client_id}', client_secret: '***'}}"
            )

            response = await self.client.post(
                self.OAUTH_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            logger.debug(f"OAuth response status: {response.status_code}")
            logger.debug(f"OAuth response headers: {dict(response.headers)}")
            if response.status_code != 200:
                logger.debug(f"OAuth response body: {response.text}")

            # Handle OAuth errors
            if response.status_code == 400:
                error_data = response.json()
                error_desc = error_data.get("error_description", "Bad request")
                error = error_data.get("error", "unknown")
                logger.error(f"OAuth request failed (400): {error} - {error_desc}")
                logger.error(f"Full error response: {error_data}")
                raise ValueError(f"OAuth authentication failed: {error_desc}")
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    error_desc = error_data.get(
                        "error_description", "Invalid client credentials"
                    )
                    error = error_data.get("error", "invalid_client")
                    logger.error(
                        f"Invalid client credentials (401): {error} - {error_desc}"
                    )
                    logger.error(f"Full error response: {error_data}")
                except:
                    logger.error(f"Invalid client credentials (401): {response.text}")
                raise ValueError(
                    f"Invalid client ID or secret. Please check:\n"
                    f"1. Client ID and secret are correct in your Pipedrive OAuth app\n"
                    f"2. Callback URL is set to: https://your-domain.com/mcp/oauth/callback\n"
                    f"3. Client Credentials flow is enabled in Pipedrive app settings\n"
                    f"4. App has required scopes: deals:read contacts:read activities:read organizations:read"
                )
            elif response.status_code >= 500:
                logger.error(f"Pipedrive OAuth server error: {response.status_code}")
                raise httpx.HTTPStatusError(
                    "Pipedrive OAuth server error",
                    request=response.request,
                    response=response,
                )

            response.raise_for_status()

            # Parse response
            token_data = response.json()

            # Validate required fields
            if "access_token" not in token_data:
                raise ValueError("OAuth response missing 'access_token' field")

            # Store token and expiration
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

            # Set expiration time with 5-minute buffer
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Successfully obtained new access token")

            return self.access_token

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting access token: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error getting access token: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting access token: {e}")
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
