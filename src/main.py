"""FastAPI application for Pipedrive MCP Server V2."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import settings
from src.utils.errors import PipedriveError, PipedriveValidationError
from src.services.deal_service import DealService
from src.services.contact_service import ContactService
from src.services.company_service import CompanyService
from src.services.activity_service import ActivityService
from src.services.pipeline_service import PipelineService
from src.services.product_service import ProductService
from src.services.user_service import UserService


# Configure logging
if settings.log_format == "json":
    import json
    from datetime import datetime

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry)

    # Set up JSON logging for all handlers
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(getattr(logging, settings.log_level.upper()))
else:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pipedrive MCP Server V2 - Complete rewrite with official SDK",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "api_base_url": settings.pipedrive_api_base_url,
        "features": [
            "comprehensive_deal_management",
            "contact_management",
            "company_management",
            "activity_tracking",
            "pipeline_management",
            "user_management",
            "product_catalog",
            "analytics_reporting",
            "advanced_search",
            "mcp_protocol_support",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-11-23T12:00:00Z",
        "version": settings.app_version,
    }


@app.get("/mcp/tools/public")
async def get_public_tools():
    """Get publicly available MCP tools."""
    return {
        "tools": [
            {
                "name": "search_deals",
                "description": "Search for deals in Pipedrive",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
            {
                "name": "get_deal",
                "description": "Get a specific deal by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {"id": {"type": "integer", "description": "Deal ID"}},
                    "required": ["id"],
                },
            },
            {
                "name": "create_deal",
                "description": "Create a new deal",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Deal title"},
                        "value": {"type": "string", "description": "Deal value"},
                        "currency": {"type": "string", "default": "USD"},
                        "person_id": {"type": "integer"},
                        "organization_id": {"type": "integer"},
                        "stage_id": {"type": "integer"},
                    },
                    "required": ["title"],
                },
            },
            {
                "name": "update_deal",
                "description": "Update an existing deal",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Deal ID"},
                        "title": {"type": "string"},
                        "value": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["id"],
                },
            },
            {
                "name": "search_persons",
                "description": "Search for persons/contacts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
            {
                "name": "get_person",
                "description": "Get a specific person by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Person ID"}
                    },
                    "required": ["id"],
                },
            },
            {
                "name": "create_person",
                "description": "Create a new person/contact",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Person name"},
                        "email": {"type": "string", "description": "Email address"},
                        "phone": {"type": "string", "description": "Phone number"},
                        "organization_id": {"type": "integer"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "search_organizations",
                "description": "Search for organizations/companies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
            {
                "name": "get_organization",
                "description": "Get a specific organization by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Organization ID"}
                    },
                    "required": ["id"],
                },
            },
            {
                "name": "create_organization",
                "description": "Create a new organization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Organization name"},
                        "address": {"type": "string"},
                        "website": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "get_activities",
                "description": "Get activities for a deal or person",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "deal_id": {"type": "integer"},
                        "person_id": {"type": "integer"},
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            },
            {
                "name": "create_activity",
                "description": "Create a new activity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Activity subject",
                        },
                        "type": {"type": "string", "description": "Activity type"},
                        "deal_id": {"type": "integer"},
                        "person_id": {"type": "integer"},
                        "due_date": {
                            "type": "string",
                            "description": "Due date (YYYY-MM-DD)",
                        },
                        "notes": {"type": "string"},
                    },
                    "required": ["subject", "type"],
                },
            },
            {
                "name": "get_pipelines",
                "description": "Get all pipelines with their names and IDs",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_pipeline_stages",
                "description": "Get all pipeline stages (accepts either pipeline name or ID)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pipeline": {
                            "type": "string",
                            "description": "Pipeline name (e.g., 'Sales Pipeline') or ID (e.g., 1). If not provided, uses default pipeline.",
                        }
                    },
                },
            },
            {
                "name": "get_products",
                "description": "Get products from catalog",
                "inputSchema": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "default": 10}},
                },
            },
        ]
    }


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest, http_request: Request):
    """Execute an MCP tool."""
    try:
        # Get API token from header
        api_token = http_request.headers.get("X-API-Token")
        if not api_token:
            raise HTTPException(status_code=401, detail="API token required")

        # Mock tool implementations (replace with actual Pipedrive API calls)
        if request.name == "search_deals":
            query = request.arguments.get("query", "")
            limit = request.arguments.get("limit", 10)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Found {limit} deals matching '{query}'. (Mock response - implement actual Pipedrive API integration)",
                    }
                ]
            }

        elif request.name == "get_deal":
            deal_id = request.arguments.get("id")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Retrieved deal {deal_id}. (Mock response - implement actual Pipedrive API integration)",
                    }
                ]
            }

        elif request.name == "get_pipelines":
            pipeline_service = await get_pipeline_service(http_request)

            try:
                pipelines = await pipeline_service.get_pipelines()

                if not pipelines:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "No pipelines found in your Pipedrive account",
                            }
                        ]
                    }

                # Format pipelines for display
                pipelines_text = f"Found {len(pipelines)} pipelines:\n\n"
                for pipeline in pipelines:
                    stages_count = len(pipeline.stages) if pipeline.stages else 0
                    pipelines_text += f"• {pipeline.name} (ID: {pipeline.id}, {stages_count} stages)\n"

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": pipelines_text.strip(),
                        }
                    ]
                }

            except Exception as e:
                return create_error_response(
                    tool_name="get_pipelines",
                    error_type="api_error",
                    message=f"Failed to retrieve pipelines: {str(e)}",
                    suggestions=[
                        "Check if your Pipedrive account has pipelines configured",
                        "Verify your API token has pipeline read permissions",
                        "Try accessing Pipedrive directly to confirm pipeline access",
                    ],
                )

        elif request.name == "get_pipeline_stages":
            pipeline = request.arguments.get(
                "pipeline", "1"
            )  # Changed from pipeline_id to pipeline
            pipeline_service = await get_pipeline_service(http_request)

            # Helper function to resolve pipeline name to ID
            async def resolve_pipeline_id(pipeline_input):
                """Convert pipeline name or ID to pipeline ID."""
                try:
                    # If it's a number, treat as ID
                    if str(pipeline_input).isdigit():
                        return int(pipeline_input)

                    # Otherwise, search by name
                    pipelines = await pipeline_service.get_pipelines()
                    for p in pipelines:
                        if p.name.lower() == str(pipeline_input).lower():
                            return p.id

                    # Try partial match
                    for p in pipelines:
                        if str(pipeline_input).lower() in p.name.lower():
                            logger.info(
                                f"Partial match: '{pipeline_input}' -> '{p.name}' (ID: {p.id})"
                            )
                            return p.id

                    return None  # Not found
                except Exception as e:
                    logger.error(f"Error resolving pipeline '{pipeline_input}': {e}")
                    return None

            try:
                # Resolve pipeline name/ID to actual pipeline ID
                resolved_pipeline_id = await resolve_pipeline_id(pipeline)

                if resolved_pipeline_id is None:
                    return create_error_response(
                        tool_name="get_pipeline_stages",
                        error_type="not_found",
                        message=f"Pipeline '{pipeline}' not found",
                        suggestions=[
                            f"Use get_pipelines to see all available pipelines",
                            f"Check pipeline name spelling (you searched for: '{pipeline}')",
                            "Try using pipeline ID number instead of name",
                            "Common pipeline names: 'Sales Pipeline', 'Onboarding', 'Lead Qualification'",
                        ],
                    )

                stages_response = await pipeline_service.get_stages(
                    pipeline_id=resolved_pipeline_id
                )
                stages = stages_response.data

                if not stages:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Pipeline '{pipeline}' (ID: {resolved_pipeline_id}) has no stages configured",
                            }
                        ]
                    }

                # Format stages for display
                stages_text = f"Found {len(stages)} stages for pipeline '{pipeline}' (ID: {resolved_pipeline_id}):\n\n"
                for stage in stages:
                    prob_text = (
                        f" ({stage.deal_probability}%)"
                        if stage.deal_probability
                        else ""
                    )
                    stages_text += f"• {stage.name} (ID: {stage.id}, Order: {stage.order_nr}){prob_text}\n"

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": stages_text.strip(),
                        }
                    ]
                }

            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "Not Found" in error_msg:
                    return create_error_response(
                        tool_name="get_pipeline_stages",
                        error_type="not_found",
                        message=f"Pipeline '{pipeline}' not found or has no stages",
                        suggestions=[
                            f"Use get_pipelines to see all available pipelines",
                            f"Check pipeline name spelling (you searched for: '{pipeline}')",
                            "Try using pipeline ID number instead of name",
                            "Common pipeline names: 'Sales Pipeline', 'Onboarding', 'Lead Qualification'",
                        ],
                    )
                else:
                    return create_error_response(
                        tool_name="get_pipeline_stages",
                        error_type="api_error",
                        message=f"Pipedrive API error: {error_msg}",
                        suggestions=[
                            "Check if pipeline name is valid",
                            f"Try with pipeline name from get_pipelines results",
                            "Verify your Pipedrive account has pipeline access",
                        ],
                    )

        else:
            # Generic mock response for other tools
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Executed {request.name} with arguments {request.arguments}. (Mock response - implement actual Pipedrive API integration)",
                    }
                ]
            }

    except Exception as e:
        logger.error(f"Error executing tool {request.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@app.exception_handler(PipedriveError)
async def pipedrive_exception_handler(request: Request, exc: PipedriveError):
    """Handle Pipedrive-specific exceptions."""
    logger.error(f"Pipedrive error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "type": "pipedrive_error"},
    )


@app.exception_handler(PipedriveValidationError)
async def validation_exception_handler(request: Request, exc: PipedriveValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=422,
        content={"error": exc.message, "type": "validation_error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": "internal_error"},
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"API Base URL: {settings.pipedrive_api_base_url}")
    logger.info(f"Server running on {settings.host}:{settings.port}")

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development",
    )
