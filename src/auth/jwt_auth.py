"""JWT authentication utilities for Pipedrive MCP Server."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, status, Request

from ..config import settings

logger = logging.getLogger(__name__)


class JWTAuthenticator:
    """JWT token authentication and validation."""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_minutes = settings.jwt_expiration_minutes

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT access token.

        Args:
            data: Payload data to encode

        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        to_encode.update({"exp": expire})

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info("Created JWT access token")
        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from request headers.

        Args:
            request: FastAPI request object

        Returns:
            Token string if found, None otherwise
        """
        # Check Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]

        # Fall back to X-API-Token header
        api_token = request.headers.get("X-API-Token")
        if api_token:
            return api_token

        return None

    def authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate incoming request and return user info.

        Args:
            request: FastAPI request object

        Returns:
            User information from token payload

        Raises:
            HTTPException: If authentication fails
        """
        token = self.extract_token_from_request(request)
        if not token:
            logger.warning("No authentication token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return self.verify_token(token)

    def get_user_id(self, request: Request) -> Optional[int]:
        """
        Extract user ID from authenticated request.

        Args:
            request: FastAPI request object

        Returns:
            User ID if available, None otherwise
        """
        try:
            payload = self.authenticate_request(request)
            return payload.get("user_id")
        except HTTPException:
            return None

    def get_pipedrive_token(self, request: Request) -> Optional[str]:
        """
        Extract Pipedrive API token from authenticated request.

        Args:
            request: FastAPI request object

        Returns:
            Pipedrive API token if available, None otherwise
        """
        try:
            payload = self.authenticate_request(request)
            return payload.get("pipedrive_token")
        except HTTPException:
            return None


# Global authenticator instance
authenticator = JWTAuthenticator()


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        request: FastAPI request object

    Returns:
        User information from token
    """
    return authenticator.authenticate_request(request)


def get_pipedrive_token_from_auth(request: Request) -> str:
    """
    FastAPI dependency to get Pipedrive token from authentication.

    Args:
        request: FastAPI request object

    Returns:
        Pipedrive API token

    Raises:
        HTTPException: If token not available
    """
    token = authenticator.get_pipedrive_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pipedrive token not found in authentication",
        )
    return token
