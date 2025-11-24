"""Custom exception classes for Pipedrive MCP Server."""

from typing import Any, Dict, Optional


class PipedriveError(Exception):
    """Base exception for all Pipedrive-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.details = kwargs


class PipedriveAPIError(PipedriveError):
    """Exception for Pipedrive API errors (4xx, 5xx responses)."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class PipedriveAuthError(PipedriveError):
    """Exception for authentication errors."""

    pass


class PipedriveRateLimitError(PipedriveError):
    """Exception for rate limit errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class PipedriveValidationError(PipedriveError):
    """Exception for input validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


class PipedriveNotFoundError(PipedriveAPIError):
    """Exception for resource not found errors (404)."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
    ):
        super().__init__(message, status_code=404)
        self.resource_type = resource_type
        self.resource_id = resource_id
