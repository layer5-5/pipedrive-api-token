"""API key authentication decorators for Pipedrive MCP Server."""

import logging
from functools import wraps
from typing import Callable, Optional, Any

from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader

from ..config import settings

logger = logging.getLogger(__name__)

# API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuthenticator:
    """API key authentication and validation.

    Extracts API keys from request headers and validates them.
    API tokens come from the X-API-Token header in incoming requests,
    NOT from environment variables or settings. This ensures security
    and allows per-request authentication.
    """

    def __init__(self):
        self.valid_api_keys = set(getattr(settings, "valid_api_keys", []))
        self.api_key_header_name = "X-API-Key"

    def extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from request headers.

        Args:
            request: FastAPI request object

        Returns:
            API key string if found, None otherwise
        """
        logger.debug(f"[API_KEY_EXTRACTION] Starting extraction from request headers")
        logger.debug(
            f"[API_KEY_EXTRACTION] Available headers: {list(request.headers.keys())}"
        )

        # Check X-API-Key header first
        api_key = request.headers.get(self.api_key_header_name)
        if api_key:
            logger.info(
                f"[API_KEY_EXTRACTION] SUCCESS: Found API key in X-API-Key header (masked: {api_key[:8]}...)"
            )
            return api_key
        else:
            logger.debug(f"[API_KEY_EXTRACTION] X-API-Key header not found")

        # Fall back to Authorization header with Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ")[1]
            logger.info(
                f"[API_KEY_EXTRACTION] SUCCESS: Found API key in Authorization Bearer header (masked: {bearer_token[:8]}...)"
            )
            return bearer_token
        else:
            logger.debug(f"[API_KEY_EXTRACTION] Authorization Bearer header not found")

        # Fall back to X-API-Token header (for backward compatibility)
        api_token = request.headers.get("X-API-Token")
        if api_token:
            token_suffix = api_token[-4:] if len(api_token) >= 4 else api_token
            logger.info(
                f"[API_KEY_EXTRACTION] SUCCESS: Found API key in X-API-Token header (last 4 chars: {token_suffix})"
            )
            return api_token
        else:
            logger.debug(f"[API_KEY_EXTRACTION] X-API-Token header not found")

        logger.warning(f"[API_KEY_EXTRACTION] FAILED: No API key found in any header")
        return None

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key against configured keys.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        key_suffix = api_key[-4:] if len(api_key) >= 4 else api_key
        logger.debug(
            f"[API_KEY_VALIDATION] Starting validation for key (last 4 chars: {key_suffix})"
        )

        if not self.valid_api_keys:
            # If no keys are configured, accept any non-empty key (development mode)
            is_valid = bool(api_key.strip())
            logger.warning(
                f"[API_KEY_VALIDATION] No API keys configured in settings - accepting any non-empty key. Is valid: {is_valid}"
            )
            return is_valid

        is_valid = api_key in self.valid_api_keys
        logger.debug(
            f"[API_KEY_VALIDATION] Checked against {len(self.valid_api_keys)} configured keys. Is valid: {is_valid}"
        )
        if not is_valid:
            logger.warning(
                f"[API_KEY_VALIDATION] FAILED: API key not in configured valid keys"
            )
        return is_valid

    def authenticate_request(self, request: Request) -> str:
        """
        Authenticate incoming request and return API key.

        Args:
            request: FastAPI request object

        Returns:
            Validated API key

        Raises:
            HTTPException: If authentication fails
        """
        logger.info(
            f"[API_KEY_AUTH] Starting authentication for request to {request.url.path}"
        )

        api_key = self.extract_api_key(request)
        if not api_key:
            logger.error(
                f"[API_KEY_AUTH] STAGE 1 FAILURE: No API key found in request headers"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        logger.debug(f"[API_KEY_AUTH] STAGE 1 SUCCESS: API key extracted")

        if not self.validate_api_key(api_key):
            logger.error(
                f"[API_KEY_AUTH] STAGE 2 FAILURE: API key validation failed for key {api_key[:8]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        logger.info(
            f"[API_KEY_AUTH] SUCCESS: Request authenticated with API key {api_key[:8]}..."
        )
        return api_key


# Global authenticator instance
authenticator = APIKeyAuthenticator()


def require_api_key(func: Callable) -> Callable:
    """
    Decorator to require API key authentication for a function.

    This decorator extracts the API key from the request headers,
    validates it, and injects the validated key into the function
    as a keyword argument called 'api_key'.

    Usage:
        @require_api_key
        async def my_function(request: Request, api_key: str):
            # Function logic here
            pass

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Find the Request object in args or kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            # Check kwargs for Request object
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

        if request is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found in function arguments",
            )

        # Authenticate and get API key
        api_key = authenticator.authenticate_request(request)

        # Inject api_key into kwargs
        kwargs["api_key"] = api_key

        # Call the original function
        return await func(*args, **kwargs)

    return wrapper


def inject_api_key(func: Callable) -> Callable:
    """
    Decorator to inject API key into function if present, but not require it.

    This decorator extracts the API key from the request headers,
    validates it if present, and injects the validated key into the function
    as a keyword argument called 'api_key'. If no API key is present,
    the function is called with api_key=None.

    Usage:
        @inject_api_key
        async def my_function(request: Request, api_key: Optional[str]):
            # Function logic here
            if api_key:
                # Authenticated logic
            else:
                # Unauthenticated logic
            pass

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Find the Request object in args or kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            # Check kwargs for Request object
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

        if request is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found in function arguments",
            )

        # Try to extract and validate API key
        api_key = authenticator.extract_api_key(request)
        if api_key and authenticator.validate_api_key(api_key):
            logger.info(
                f"Successfully authenticated request with API key: {api_key[:8]}..."
            )
        elif api_key:
            logger.warning(f"Invalid API key provided: {api_key[:8]}...")
            api_key = None

        # Inject api_key into kwargs
        kwargs["api_key"] = api_key

        # Call the original function
        return await func(*args, **kwargs)

    return wrapper


async def get_api_key_from_request(request: Request) -> Optional[str]:
    """
    FastAPI dependency to get API key from request.

    Args:
        request: FastAPI request object

    Returns:
        API key if present and valid, None otherwise
    """
    logger.debug(
        f"[DEPENDENCY_OPTIONAL] get_api_key_from_request called for {request.url.path}"
    )
    api_key = authenticator.extract_api_key(request)
    if api_key and authenticator.validate_api_key(api_key):
        logger.debug(
            f"[DEPENDENCY_OPTIONAL] SUCCESS: API key found and validated (masked: {api_key[:8]}...)"
        )
        return api_key
    logger.debug(f"[DEPENDENCY_OPTIONAL] No valid API key found")
    return None


async def require_api_key_dependency(request: Request) -> str:
    """
    FastAPI dependency that requires API key authentication.

    Args:
        request: FastAPI request object

    Returns:
        Validated API key

    Raises:
        HTTPException: If authentication fails
    """
    logger.debug(
        f"[DEPENDENCY_REQUIRED] require_api_key_dependency called for {request.url.path}"
    )
    try:
        api_key = authenticator.authenticate_request(request)
        logger.debug(
            f"[DEPENDENCY_REQUIRED] STAGE 3 SUCCESS: API key injected into dependency (masked: {api_key[:8]}...)"
        )
        return api_key
    except HTTPException as e:
        logger.error(
            f"[DEPENDENCY_REQUIRED] STAGE 3 FAILURE: HTTPException raised - {e.detail}"
        )
        raise
