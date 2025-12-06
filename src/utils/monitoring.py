"""Langfuse monitoring integration for Pipedrive MCP Server."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import Request, Response

from ..config import settings

logger = logging.getLogger(__name__)

# Global Langfuse client
langfuse_client: Optional[Any] = None
LANGFUSE_AVAILABLE = False

# Try to import Langfuse
try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    logger.warning("Langfuse not available - monitoring disabled")
    Langfuse = None


def initialize_langfuse():
    """Initialize Langfuse client with configuration."""
    global langfuse_client

    if not settings.langfuse_enabled or not LANGFUSE_AVAILABLE:
        logger.info("Langfuse monitoring is disabled or not available")
        return None

    if not all(
        [
            settings.langfuse_secret_key,
            settings.langfuse_public_key,
            settings.langfuse_base_url,
        ]
    ):
        logger.warning("Langfuse configuration incomplete - monitoring disabled")
        return None

    try:
        langfuse_client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_base_url,
        )
        logger.info(f"Langfuse initialized with base URL: {settings.langfuse_base_url}")
        return langfuse_client
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return None


def get_langfuse_client() -> Optional[Any]:
    """Get Langfuse client instance."""
    global langfuse_client
    if langfuse_client is None:
        langfuse_client = initialize_langfuse()
    return langfuse_client


class LangfuseTracer:
    """Langfuse tracing utility for MCP operations."""

    def __init__(self):
        self.client = get_langfuse_client()

    def create_trace(
        self, name: str, user_id: Optional[str] = None, **kwargs
    ) -> Optional[Any]:
        """Create a new Langfuse trace."""
        if not self.client:
            return None

        try:
            trace = self.client.trace(name=name, user_id=user_id, **kwargs)
            return trace
        except Exception as e:
            logger.error(f"Failed to create Langfuse trace: {e}")
            return None

    def create_span(self, trace_id: str, name: str, **kwargs) -> Optional[Any]:
        """Create a new Langfuse span."""
        if not self.client:
            return None

        try:
            span = self.client.span(trace_id=trace_id, name=name, **kwargs)
            return span
        except Exception as e:
            logger.error(f"Failed to create Langfuse span: {e}")
            return None

    def create_event(self, trace_id: str, name: str, **kwargs) -> Optional[Any]:
        """Create a new Langfuse event."""
        if not self.client:
            return None

        try:
            event = self.client.event(trace_id=trace_id, name=name, **kwargs)
            return event
        except Exception as e:
            logger.error(f"Failed to create Langfuse event: {e}")
            return None


# Global tracer instance
tracer = LangfuseTracer()


def observe_mcp_operation(operation_name: str):
    """
    Decorator to observe MCP operations with Langfuse.

    Args:
        operation_name: Name of MCP operation to observe
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not settings.langfuse_enabled or not LANGFUSE_AVAILABLE:
                return await func(*args, **kwargs)

            # Extract request from args/kwargs for context
            request = None
            api_key = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break

            # Extract API key for user identification
            if request:
                api_key = request.headers.get("X-API-Key") or request.headers.get(
                    "X-API-Token"
                )

            # Create trace
            trace = tracer.create_trace(
                name=f"mcp_{operation_name}",
                user_id=api_key[:8] + "..." if api_key else "anonymous",
                input={
                    "operation": operation_name,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
            )

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Record successful execution
                if trace:
                    trace.update(
                        output={
                            "status": "success",
                            "execution_time": time.time() - start_time,
                        },
                        usage={
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                        },  # Placeholder
                    )

                return result

            except Exception as e:
                # Record error
                if trace:
                    trace.update(
                        output={
                            "status": "error",
                            "error": str(e),
                            "execution_time": time.time() - start_time,
                        },
                        level="ERROR",
                    )

                # Create error event
                tracer.create_event(
                    trace_id=trace.id if trace else "unknown",
                    name="error",
                    data={"error_type": type(e).__name__, "error_message": str(e)},
                )

                raise

        return wrapper

    return decorator


def observe_pipedrive_api_call(operation: str):
    """
    Decorator to observe Pipedrive API calls with Langfuse.

    Args:
        operation: Name of Pipedrive API operation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not settings.langfuse_enabled or not LANGFUSE_AVAILABLE:
                return await func(*args, **kwargs)

            # Create span for API call
            span = tracer.create_span(
                trace_id="pipedrive_api",  # This should be replaced with actual trace ID
                name=f"pipedrive_{operation}",
                input={"operation": operation, "args_count": len(args)},
            )

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Record successful API call
                if span:
                    span.update(
                        output={
                            "status": "success",
                            "execution_time": time.time() - start_time,
                        }
                    )

                return result

            except Exception as e:
                # Record API error
                if span:
                    span.update(
                        output={
                            "status": "error",
                            "error": str(e),
                            "execution_time": time.time() - start_time,
                        },
                        level="ERROR",
                    )

                raise

        return wrapper

    return decorator


@asynccontextmanager
async def create_request_trace(request: Request, operation_name: str):
    """
    Context manager to create a trace for HTTP requests.

    Args:
        request: FastAPI request object
        operation_name: Name of operation being traced
    """
    if not settings.langfuse_enabled or not LANGFUSE_AVAILABLE:
        yield
        return

    # Extract API key for user identification
    api_key = request.headers.get("X-API-Key") or request.headers.get("X-API-Token")
    user_id = api_key[:8] + "..." if api_key else "anonymous"

    # Create trace
    trace = tracer.create_trace(
        name=f"http_{operation_name}",
        user_id=user_id,
        input={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": request.client.host if request.client else "unknown",
        },
    )

    start_time = time.time()

    try:
        yield trace
    except Exception as e:
        # Record error
        if trace:
            trace.update(
                output={
                    "status": "error",
                    "error": str(e),
                    "execution_time": time.time() - start_time,
                },
                level="ERROR",
            )
        raise


def log_tool_execution(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Any,
    execution_time: float,
    error: Optional[Exception] = None,
):
    """
    Log MCP tool execution to Langfuse.

    Args:
        tool_name: Name of executed tool
        arguments: Tool arguments
        result: Tool execution result
        execution_time: Time taken to execute the tool
        error: Error if execution failed
    """
    if not settings.langfuse_enabled or not LANGFUSE_AVAILABLE:
        return

    trace = tracer.create_trace(
        name=f"tool_{tool_name}", input={"tool": tool_name, "arguments": arguments}
    )

    if trace:
        if error:
            trace.update(
                output={
                    "status": "error",
                    "error": str(error),
                    "execution_time": execution_time,
                },
                level="ERROR",
            )
        else:
            trace.update(
                output={
                    "status": "success",
                    "result_preview": str(result)[:200],
                    "execution_time": execution_time,
                }
            )


def flush_langfuse():
    """Flush any pending Langfuse data."""
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
            logger.info("Langfuse data flushed")
        except Exception as e:
            logger.error(f"Failed to flush Langfuse data: {e}")


# Initialize Langfuse on module import
initialize_langfuse()
