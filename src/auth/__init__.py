"""Authentication module for Pipedrive MCP Server."""

# API Key Authentication (primary method)
from .api_key_auth import (
    APIKeyAuthenticator,
    authenticator,
    require_api_key,
    inject_api_key,
    get_api_key_from_request,
    require_api_key_dependency,
)

# Legacy JWT Authentication (deprecated)
from .jwt_auth import (
    JWTAuthenticator as LegacyJWTAuthenticator,
    authenticator as legacy_jwt_authenticator,
    get_current_user as legacy_get_current_user,
    get_pipedrive_token_from_auth as legacy_get_pipedrive_token_from_auth,
)

# Legacy Layer55 Client (deprecated)
from .layer55_client import (
    Layer55Client as LegacyLayer55Client,
    layer55_client as legacy_layer55_client,
)

__all__ = [
    # API Key Authentication (recommended)
    "APIKeyAuthenticator",
    "authenticator",
    "require_api_key",
    "inject_api_key",
    "get_api_key_from_request",
    "require_api_key_dependency",
    # Legacy JWT Authentication (deprecated)
    "LegacyJWTAuthenticator",
    "legacy_jwt_authenticator",
    "legacy_get_current_user",
    "legacy_get_pipedrive_token_from_auth",
    "LegacyLayer55Client",
    "legacy_layer55_client",
]
