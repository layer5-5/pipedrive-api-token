"""
Pipedrive MCP Server - FastAPI application
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlencode
from fastapi import FastAPI, HTTPException, Header, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import httpx
import requests

from auth.api_token import PipedriveApiTokenAuth
from pipedrive.tools import PIPEDRIVE_TOOLS, format_mcp_response


# Fixed Pipedrive client (inlined to avoid import issues)
class PipedriveFixed:
    """Fixed Pipedrive client that properly uses api.pipedrive.com"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"

    def __init__(self, token):
        self._token = token
        # Fixed: Use the correct API base URL instead of the broken 'app.pipedrive.com'
        self._origin = "https://api.pipedrive.com"
        logger.info(
            "Pipedrive client initialized with correct base URL: " + self._origin
        )

    def request(self, method, path, data=None):
        """Make HTTP request to Pipedrive API"""
        if data is None:
            data = {}

        # Ensure path starts with /v1
        if not path.startswith("/v1"):
            path = "/v1" + path

        url = self._origin + path + "?api_token=%s" % self._token

        if method == self.GET and data:
            url += "&" + urlencode(data)

        logger.debug(f"Making request: {method} {url}")

        # DATA RETRIEVAL LOGGING - Log API request details
        if ENABLE_DATA_RETRIEVAL_LOGGING:
            logger.info(f"=== API REQUEST LOG ===")
            logger.info(f"Method: {method}")
            logger.info(f"Path: {path}")
            logger.info(f"Full URL: {url}")
            if data:
                logger.info(f"Request Data: {json.dumps(data, indent=2)}")
            logger.info(f"=== END API REQUEST LOG ===")

        r = requests.request(
            method,
            url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        response = r.json()

        # DATA RETRIEVAL LOGGING - Log API response summary
        if ENABLE_DATA_RETRIEVAL_LOGGING:
            logger.info(f"=== API RESPONSE LOG ===")
            logger.info(f"Status Code: {r.status_code}")
            logger.info(f"Success: {response.get('success', 'Unknown')}")
            if "data" in response:
                data_count = (
                    len(response["data"])
                    if isinstance(response["data"], (list, dict))
                    else "N/A"
                )
                logger.info(f"Data Items Count: {data_count}")
            if "error" in response:
                logger.error(f"API Error: {response['error']}")
            logger.info(f"=== END API RESPONSE LOG ===")

        if not response.get("success", True) and "error" in response:
            logger.error(f"Pipedrive API error: {response.get('error')}")

        return response

    def __getattr__(self, name):
        """Handle dynamic method calls like get_users(), create_deals(), etc."""

        def wrapper(data=None):
            if data is None:
                data = {}

            try:
                action, raw_path = name.split("_", 1)
            except ValueError:
                raise AttributeError(f"Invalid method name: {name}")

            # Map action to HTTP method
            method_map = {
                "get": self.GET,
                "create": self.POST,
                "update": self.PUT,
                "delete": self.DELETE,
            }

            if action not in method_map:
                raise AttributeError(f"Invalid action: {action}")

            method = method_map[action]
            path = raw_path.replace("_", "/")

            # Handle PUT requests with ID
            if method == self.PUT:
                if "id" not in data:
                    raise ValueError("PUT requests require an 'id' field in data")
                id_val = data.pop("id")
                path = "%s/%d" % (path, id_val)

            # Make the request with /v1 prefix (request() method will add /v1/ if needed)
            r_data = self.request(method, path, data)

            if "error" in r_data:
                error_msg = r_data.get("error", "Unknown error")
                raise Exception(f"Pipedrive API Error: {error_msg}")

            return r_data

        return wrapper

    class Error(Exception):
        """Pipedrive error"""

        def __init__(self, response):
            self.response = response

        def __str__(self):
            return self.response.get("error", "No error provided")


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Pipedrive MCP Server",
    description="MCP server for Pipedrive CRM integration with Layer55 authentication",
    version="1.0.0",
)

# No JWT validation needed for API token authentication

# Configuration
LAYER55_API_URL = os.getenv("LAYER55_API_URL")
SERVER_ID = os.getenv(
    "PIPEDRIVE_SERVER_ID", "pipedrive"
)  # Default server ID for token lookup


class InitializeRequest(BaseModel):
    """MCP initialize request"""

    protocolVersion: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    clientInfo: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    """MCP tool call request"""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    client_credentials: Optional[Dict[str, Any]] = Field(default=None)
    api_token: Optional[str] = Field(default=None)  # For API token authentication


class ApiTokenRequest(BaseModel):
    """API token authentication request"""

    api_token: str = Field(..., description="Pipedrive API token")


# Simple API token authentication middleware
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Middleware to validate API tokens for protected endpoints"""

    # Skip authentication for health, root, public tools, and test endpoints
    skip_paths = [
        "/",
        "/health",
        "/mcp/tools/public",
        "/mcp/tools/public/",
        "/test-connection",
    ]
    if request.url.path in skip_paths:
        logger.info(f"Skipping authentication for path: {request.url.path}")
        return await call_next(request)

    # Check for API token in header
    api_token = request.headers.get("X-API-Token")
    if not api_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "X-API-Token header is required"},
        )

    logger.info(f"API token authentication for path: {request.url.path}")
    # Store API token in request state for later use
    request.state.api_token = api_token
    return await call_next(request)


@app.get("/")
async def root():
    """Server information endpoint"""
    return {
        "name": "pipedrive-mcp",
        "version": "1.0.0",
        "description": "Pipedrive MCP Server with Layer55 authentication",
        "tools_count": len(PIPEDRIVE_TOOLS),
        "package": "python-pipedrive",
        "test_endpoint": "/test-connection",
        "features": {
            "official_package": True,
            "api_test": True,
            "backend_integration": True,
            "multi_user": True,
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "pipedrive-mcp", "version": "1.0.0"}


@app.get("/test-connection")
async def test_connection():
    """Test Pipedrive connection using backend authentication"""
    logger.info("Test connection endpoint called")

    try:
        # Get the current user's API key from Layer55 backend (same way chat service gets it)
        layer55_api_url = os.getenv("LAYER55_API_URL", "https://api.layer55.eu")
        server_id = os.getenv("PIPEDRIVE_SERVER_ID", "pipedrive")

        # Call Layer55 API to get the API key for this server and user
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{layer55_api_url}/api/v1/mcp/servers/{server_id}/tokens",
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to get API key from Layer55: {response.status_code}",
                }

            token_data = response.json()
            api_token = token_data.get("access_token")

            if not api_token:
                return {
                    "status": "error",
                    "message": "No API token found in Layer55 backend",
                }

        # Test the API key using fixed Pipedrive client
        test_client = PipedriveFixed(api_token)

        # Make a simple API call to verify connection
        users = test_client.get_users()
        user_count = len(users.get("data", [])) if users else 0

        logger.info(f"Connection test successful: found {user_count} users")

        return {
            "status": "success",
            "message": f"Pipedrive connection working! Found {user_count} users",
            "package": "python-pipedrive-fixed",
            "backend_source": "layer55_user_secrets",
            "test_result": {
                "users_count": user_count,
                "api_valid": True,
                "package_working": True,
            },
        }

    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "package": "python-pipedrive",
            "backend_source": "layer55_user_secrets",
            "error": str(e),
        }


@app.post("/mcp/initialize")
async def initialize(request_data: InitializeRequest, request: Request):
    """MCP initialize endpoint"""
    logger.info("Initialize request with API token authentication")

    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {"name": "pipedrive-mcp-api-token", "version": "1.0.0"},
        "capabilities": {"tools": {}},
    }


@app.get("/mcp/tools")
async def list_tools():
    """List all available Pipedrive tools"""
    logger.info("List tools request")

    return {"tools": PIPEDRIVE_TOOLS}


@app.get("/mcp/tools/public")
async def list_tools_public():
    """List all available Pipedrive tools without authentication"""
    logger.info(f"Public tools request - returning {len(PIPEDRIVE_TOOLS)} tools")

    # Log each tool being returned
    for i, tool in enumerate(PIPEDRIVE_TOOLS):
        logger.info(
            f"Tool {i + 1}: {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')[:50]}..."
        )

    response_data = {"tools": PIPEDRIVE_TOOLS}
    logger.info(f"Response data keys: {list(response_data.keys())}")
    logger.info(f"Response tools count: {len(response_data.get('tools', []))}")

    return response_data


@app.post("/mcp/tools/call")
async def call_tool(tool_request: ToolCallRequest, request: Request):
    """Execute a Pipedrive tool"""
    tool_name = tool_request.name
    arguments = tool_request.arguments

    # Get API token from request body or header
    api_token = tool_request.api_token or request.headers.get("X-API-Token")

    if not api_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "API token required"},
        )

    logger.info(f"Tool call: {tool_name} with API token authentication")
    logger.info(f"API token length: {len(api_token) if api_token else 0}")

    try:
        # Use fixed Pipedrive client that works around the broken python-pipedrive package
        pipedrive = PipedriveFixed(api_token)
        result = await execute_tool(pipedrive, tool_name, arguments)
        return format_mcp_response(result)

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}", exc_info=True)
        return format_mcp_response({"error": str(e), "tool": tool_name}, is_error=True)


# ============================================================================
# DATA RETRIEVAL LOGGING CONFIGURATION
# ============================================================================
# Set this to False to disable all data retrieval logging
ENABLE_DATA_RETRIEVAL_LOGGING = (
    os.getenv("ENABLE_DATA_RETRIEVAL_LOGGING", "true").lower() == "true"
)
# ============================================================================


async def execute_tool(pipedrive: PipedriveFixed, tool_name: str, args: Dict) -> Any:
    """
    Execute specific Pipedrive tool.

    Args:
        pipedrive: Pipedrive API client
        tool_name: Name of tool to execute
        args: Tool arguments

    Returns:
        Tool execution result
    """
    # Call dynamic method on pipedrive client
    # The PipedriveFixed client uses __getattr__ to handle method calls
    # Method names are converted to API paths (e.g., get_deals -> GET /v1/deals)
    try:
        method = getattr(pipedrive, tool_name)
        result = method(args)

        # DATA RETRIEVAL LOGGING - Easily removable section
        if ENABLE_DATA_RETRIEVAL_LOGGING:
            _log_data_retrieval(tool_name, args, result)
        # END DATA RETRIEVAL LOGGING

        return result
    except AttributeError:
        raise ValueError(f"Unknown tool: {tool_name}")
    except Exception as e:
        logger.error(f"Tool execution error for {tool_name}: {str(e)}", exc_info=True)
        raise


def _log_data_retrieval(tool_name: str, args: Dict, result: Any) -> None:
    """
    Log data retrieval information for debugging and monitoring.

    This function can be easily disabled by setting ENABLE_DATA_RETRIEVAL_LOGGING=False
    or by commenting out the call in execute_tool().

    Args:
        tool_name: Name of the tool that was executed
        args: Arguments passed to the tool
        result: Result returned from the API call
    """
    try:
        # Log basic tool execution info
        logger.info(f"=== DATA RETRIEVAL LOG ===")
        logger.info(f"Tool: {tool_name}")
        logger.info(f"Arguments: {json.dumps(args, indent=2)}")

        # Analyze and log result summary
        if isinstance(result, dict):
            if "success" in result:
                logger.info(f"API Success: {result.get('success')}")

            if "data" in result:
                data = result["data"]
                if isinstance(data, list):
                    logger.info(f"Records Retrieved: {len(data)}")

                    # Log first few records for debugging
                    if data and len(data) > 0:
                        sample_record = data[0]
                        logger.info(
                            f"Sample Record Keys: {list(sample_record.keys()) if isinstance(sample_record, dict) else 'Non-dict record'}"
                        )

                        # Log specific important fields for common data types
                        if tool_name.startswith("get_deal") and isinstance(
                            sample_record, dict
                        ):
                            logger.info(
                                f"Sample Deal - ID: {sample_record.get('id')}, Title: {sample_record.get('title', 'N/A')}, Value: {sample_record.get('value', 'N/A')}"
                            )
                        elif tool_name.startswith("get_person") and isinstance(
                            sample_record, dict
                        ):
                            logger.info(
                                f"Sample Person - ID: {sample_record.get('id')}, Name: {sample_record.get('name', 'N/A')}, Email: {sample_record.get('email', 'N/A')}"
                            )
                        elif tool_name.startswith("get_organization") and isinstance(
                            sample_record, dict
                        ):
                            logger.info(
                                f"Sample Org - ID: {sample_record.get('id')}, Name: {sample_record.get('name', 'N/A')}"
                            )
                        elif tool_name.startswith("get_activit") and isinstance(
                            sample_record, dict
                        ):
                            logger.info(
                                f"Sample Activity - ID: {sample_record.get('id')}, Type: {sample_record.get('type', 'N/A')}, Subject: {sample_record.get('subject', 'N/A')}"
                            )

                        # Log total value for deals if available
                        if tool_name.startswith("get_deal") and data:
                            total_value = sum(
                                deal.get("value", 0) or 0
                                for deal in data
                                if isinstance(deal, dict)
                            )
                            logger.info(f"Total Deal Value: {total_value}")

                elif isinstance(data, dict):
                    logger.info(f"Single Record Retrieved: {list(data.keys())}")

                    # Log key info for single record types
                    if tool_name == "get_deal":
                        logger.info(
                            f"Deal - ID: {data.get('id')}, Title: {data.get('title', 'N/A')}, Value: {data.get('value', 'N/A')}"
                        )
                    elif tool_name == "get_person":
                        logger.info(
                            f"Person - ID: {data.get('id')}, Name: {data.get('name', 'N/A')}"
                        )
                    elif tool_name == "get_organization":
                        logger.info(
                            f"Organization - ID: {data.get('id')}, Name: {data.get('name', 'N/A')}"
                        )

            # Log pagination info if available
            if "additional_data" in result:
                additional_data = result["additional_data"]
                if isinstance(additional_data, dict):
                    pagination = additional_data.get("pagination", {})
                    if pagination:
                        logger.info(
                            f"Pagination - Start: {pagination.get('start')}, Limit: {pagination.get('limit')}, More: {pagination.get('more_items_in_collection', False)}"
                        )

            # Log errors if present
            if "error" in result:
                logger.error(f"API Error: {result['error']}")

        elif isinstance(result, list):
            logger.info(f"Direct List Result: {len(result)} items")
            if result and isinstance(result[0], dict):
                logger.info(f"Sample Item Keys: {list(result[0].keys())}")

        else:
            logger.info(f"Non-standard result type: {type(result)}")

        logger.info(f"=== END DATA RETRIEVAL LOG ===")

    except Exception as e:
        # Don't let logging errors break the main functionality
        logger.error(f"Error in data retrieval logging: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8002))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        reload=os.getenv("ENVIRONMENT") == "development",
    )
