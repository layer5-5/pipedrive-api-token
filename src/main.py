"""Clean, simple FastAPI application for Pipedrive MCP Server."""

import logging
import os
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import settings
from src.client.pipedrive_client import PipedriveClient
from src.services.deal_service import DealService
from src.services.pipeline_service import PipelineService
from src.utils.errors import PipedriveError, PipedriveValidationError
from src.auth.api_key_auth import require_api_key, require_api_key_dependency


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pipedrive MCP Server - Simple & Clean",
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


# === Models ===


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict


# === Helper Functions ===


def create_mcp_response(text: str) -> Dict[str, Any]:
    """Create standardized MCP response."""
    return {"content": [{"type": "text", "text": text}]}


def create_error_response(text: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return create_mcp_response(f"Error: {text}")


async def get_service_client(api_token: str, service_class):
    """Create service instance with client."""
    client = PipedriveClient(api_token)
    return service_class(client)


# === API Endpoints ===


@app.get("/")
async def root():
    """Server information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "api_base_url": settings.pipedrive_api_base_url,
    }


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.post("/mcp/initialize")
async def initialize_mcp():
    """Initialize MCP connection."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {"listChanged": True}},
        "serverInfo": {"name": settings.app_name, "version": settings.app_version},
    }


@app.get("/mcp/tools/public")
async def get_public_tools():
    """Get available tools."""
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
                "name": "get_pipelines",
                "description": "Get all pipelines",
                "inputSchema": {"type": "object", "properties": {}},
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
                "description": "Get all pipelines",
                "inputSchema": {"type": "object", "properties": {}},
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


# === Tool Handlers ===


async def handle_search_deals(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle search_deals tool."""
    query = arguments.get("query", "")
    limit = arguments.get("limit", 10)

    deal_service = await get_service_client(api_token, DealService)
    deals = await deal_service.search_deals(term=query, limit=limit)

    if not deals:
        return create_mcp_response(f"No deals found matching '{query}'")

    result_text = f"Found {len(deals)} deals matching '{query}':\n\n"
    for deal in deals:
        result_text += f"• {deal.title} (ID: {deal.id})\n"
        if deal.value:
            result_text += f"  Value: {deal.value}\n"
        result_text += f"  Status: {deal.status}\n"

    return create_mcp_response(result_text.strip())


async def handle_get_deal(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_deal tool."""
    deal_id = arguments.get("id")
    if not deal_id:
        return create_error_response("Deal ID is required")

    deal_service = await get_service_client(api_token, DealService)
    deal = await deal_service.get_deal(deal_id)

    if not deal:
        return create_mcp_response(f"Deal with ID {deal_id} not found")

    deal_text = f"Deal: {deal.title}\nID: {deal.id}\nStatus: {deal.status}"
    if deal.value:
        deal_text += f"\nValue: {deal.value}"

    return create_mcp_response(deal_text)


async def handle_create_deal(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle create_deal tool."""
    title = arguments.get("title")
    if not title:
        return create_error_response("Deal title is required")

    deal_service = await get_service_client(api_token, DealService)
    deal = await deal_service.create_deal(
        title=title,
        value=arguments.get("value"),
        currency=arguments.get("currency", "USD"),
        person_id=arguments.get("person_id"),
        organization_id=arguments.get("organization_id"),
        stage_id=arguments.get("stage_id"),
    )

    deal_text = f"Created deal: {deal.title}\nID: {deal.id}"
    if deal.value:
        deal_text += f"\nValue: {deal.value}"

    return create_mcp_response(deal_text)


async def handle_update_deal(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle update_deal tool."""
    deal_id = arguments.get("id")
    if not deal_id:
        return create_error_response("Deal ID is required")

    deal_service = await get_service_client(api_token, DealService)
    deal = await deal_service.update_deal(
        deal_id=deal_id,
        title=arguments.get("title"),
        value=arguments.get("value"),
        status=arguments.get("status"),
    )

    deal_text = f"Updated deal: {deal.title}\nID: {deal.id}\nStatus: {deal.status}"
    if deal.value:
        deal_text += f"\nValue: {deal.value}"

    return create_mcp_response(deal_text)


async def handle_get_pipelines(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_pipelines tool."""
    pipeline_service = await get_service_client(api_token, PipelineService)
    pipelines = await pipeline_service.get_pipelines()

    if not pipelines:
        return create_mcp_response("No pipelines found")

    result_text = f"Found {len(pipelines)} pipelines:\n\n"
    for pipeline in pipelines:
        stages_count = len(pipeline.stages) if pipeline.stages else 0
        result_text += f"• {pipeline.name} (ID: {pipeline.id}, {stages_count} stages)\n"

    return create_mcp_response(result_text.strip())


async def handle_get_pipeline_stages(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_pipeline_stages tool."""
    pipeline = arguments.get("pipeline")

    pipeline_service = await get_service_client(api_token, PipelineService)
    stages = await pipeline_service.get_pipeline_stages(pipeline)

    if not stages:
        pipeline_desc = f"pipeline '{pipeline}'" if pipeline else "default pipeline"
        return create_mcp_response(f"No stages found for {pipeline_desc}")

    result_text = f"Found {len(stages)} stages:\n\n"
    for stage in stages:
        result_text += f"• {stage.name} (ID: {stage.id}"
        if hasattr(stage, "order_nr") and stage.order_nr is not None:
            result_text += f", Order: {stage.order_nr}"
        result_text += ")\n"

    return create_mcp_response(result_text.strip())


async def handle_search_persons(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle search_persons tool."""
    from src.services.contact_service import ContactService

    query = arguments.get("query", "")
    limit = arguments.get("limit", 10)

    contact_service = await get_service_client(api_token, ContactService)
    contacts = await contact_service.search_contacts(term=query, limit=limit)

    if not contacts:
        return create_mcp_response(f"No persons found matching '{query}'")

    result_text = f"Found {len(contacts)} persons matching '{query}':\n\n"
    for contact in contacts:
        result_text += f"• {contact.name} (ID: {contact.id})\n"
        if contact.email:
            result_text += f"  Email: {contact.email}\n"
        if contact.phone:
            result_text += f"  Phone: {contact.phone}\n"

    return create_mcp_response(result_text.strip())


async def handle_get_person(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_person tool."""
    from src.services.contact_service import ContactService

    person_id = arguments.get("id")
    if not person_id:
        return create_error_response("Person ID is required")

    contact_service = await get_service_client(api_token, ContactService)
    contact = await contact_service.get_contact(person_id)

    if not contact:
        return create_mcp_response(f"Person with ID {person_id} not found")

    contact_text = f"Person: {contact.name}\nID: {contact.id}"
    if contact.email:
        contact_text += f"\nEmail: {contact.email}"
    if contact.phone:
        contact_text += f"\nPhone: {contact.phone}"

    return create_mcp_response(contact_text)


async def handle_create_person(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle create_person tool."""
    from src.services.contact_service import ContactService

    name = arguments.get("name")
    if not name:
        return create_error_response("Person name is required")

    contact_service = await get_service_client(api_token, ContactService)
    contact = await contact_service.create_contact(
        name=name,
        email=arguments.get("email"),
        phone=arguments.get("phone"),
        organization_id=arguments.get("organization_id"),
    )

    contact_text = f"Created person: {contact.name}\nID: {contact.id}"
    if contact.email:
        contact_text += f"\nEmail: {contact.email}"
    if contact.phone:
        contact_text += f"\nPhone: {contact.phone}"

    return create_mcp_response(contact_text)


async def handle_search_organizations(
    api_token: str, arguments: dict
) -> Dict[str, Any]:
    """Handle search_organizations tool."""
    from src.services.company_service import CompanyService

    query = arguments.get("query", "")
    limit = arguments.get("limit", 10)

    company_service = await get_service_client(api_token, CompanyService)
    companies = await company_service.search_companies(term=query, limit=limit)

    if not companies:
        return create_mcp_response(f"No organizations found matching '{query}'")

    result_text = f"Found {len(companies)} organizations matching '{query}':\n\n"
    for company in companies:
        result_text += f"• {company.name} (ID: {company.id})\n"
        if company.address:
            result_text += f"  Address: {company.address}\n"
        if company.website:
            result_text += f"  Website: {company.website}\n"

    return create_mcp_response(result_text.strip())


async def handle_get_organization(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_organization tool."""
    from src.services.company_service import CompanyService

    organization_id = arguments.get("id")
    if not organization_id:
        return create_error_response("Organization ID is required")

    company_service = await get_service_client(api_token, CompanyService)
    company = await company_service.get_company(organization_id)

    if not company:
        return create_mcp_response(f"Organization with ID {organization_id} not found")

    company_text = f"Organization: {company.name}\nID: {company.id}"
    if company.address:
        company_text += f"\nAddress: {company.address}"
    if company.website:
        company_text += f"\nWebsite: {company.website}"

    return create_mcp_response(company_text)


async def handle_create_organization(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle create_organization tool."""
    from src.services.company_service import CompanyService

    name = arguments.get("name")
    if not name:
        return create_error_response("Organization name is required")

    company_service = await get_service_client(api_token, CompanyService)
    company = await company_service.create_company(
        name=name,
        address=arguments.get("address"),
        website=arguments.get("website"),
    )

    company_text = f"Created organization: {company.name}\nID: {company.id}"
    if company.address:
        company_text += f"\nAddress: {company.address}"
    if company.website:
        company_text += f"\nWebsite: {company.website}"

    return create_mcp_response(company_text)


async def handle_get_activities(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_activities tool."""
    from src.services.activity_service import ActivityService

    deal_id = arguments.get("deal_id")
    person_id = arguments.get("person_id")
    limit = arguments.get("limit", 10)

    activity_service = await get_service_client(api_token, ActivityService)
    activities = await activity_service.get_activities(
        deal_id=deal_id, person_id=person_id, limit=limit
    )

    if not activities:
        return create_mcp_response("No activities found")

    result_text = f"Found {len(activities)} activities:\n\n"
    for activity in activities:
        result_text += f"• {activity.subject} (ID: {activity.id})\n"
        result_text += f"  Type: {activity.type}\n"
        if activity.due_date:
            result_text += f"  Due: {activity.due_date}\n"

    return create_mcp_response(result_text.strip())


async def handle_create_activity(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle create_activity tool."""
    from src.services.activity_service import ActivityService

    subject = arguments.get("subject")
    activity_type = arguments.get("type")
    if not subject or not activity_type:
        return create_error_response("Subject and type are required")

    activity_service = await get_service_client(api_token, ActivityService)
    activity = await activity_service.create_activity(
        subject=subject,
        type=activity_type,
        deal_id=arguments.get("deal_id"),
        person_id=arguments.get("person_id"),
        due_date=arguments.get("due_date"),
        notes=arguments.get("notes"),
    )

    activity_text = f"Created activity: {activity.subject}\nID: {activity.id}"
    activity_text += f"\nType: {activity.type}"
    if activity.due_date:
        activity_text += f"\nDue: {activity.due_date}"

    return create_mcp_response(activity_text)


async def handle_get_products(api_token: str, arguments: dict) -> Dict[str, Any]:
    """Handle get_products tool."""
    from src.services.product_service import ProductService

    limit = arguments.get("limit", 10)

    product_service = await get_service_client(api_token, ProductService)
    products = await product_service.get_products(limit=limit)

    if not products:
        return create_mcp_response("No products found")

    result_text = f"Found {len(products)} products:\n\n"
    for product in products:
        result_text += f"• {product.name} (ID: {product.id})\n"
        if product.price:
            result_text += f"  Price: {product.price}\n"
        if product.description:
            result_text += f"  Description: {product.description}\n"

    return create_mcp_response(result_text.strip())


# === Main Tool Router ===


@app.post("/mcp/tools/call")
async def call_tool(
    tool_request: ToolCallRequest,
    http_request: Request,
    api_key: str = Depends(require_api_key_dependency),
):
    """Route tool calls to appropriate handlers."""

    # Log the API token being used (masked for security)
    if api_key:
        logger.info(
            f"[ENDPOINT_CALL_TOOL] STAGE 4 SUCCESS: API key injected into endpoint (masked: {api_key[:8]}...)"
        )
        logger.info(
            f"[ENDPOINT_CALL_TOOL] Processing tool request: {tool_request.name}"
        )
    else:
        logger.error(
            f"[ENDPOINT_CALL_TOOL] STAGE 4 FAILURE: API key is None after dependency injection!"
        )

    # Route to appropriate handler
    tool_handlers = {
        "search_deals": handle_search_deals,
        "get_deal": handle_get_deal,
        "get_pipelines": handle_get_pipelines,
        "get_pipeline_stages": handle_get_pipeline_stages,
        "create_deal": handle_create_deal,
        "update_deal": handle_update_deal,
        "search_persons": handle_search_persons,
        "get_person": handle_get_person,
        "create_person": handle_create_person,
        "search_organizations": handle_search_organizations,
        "get_organization": handle_get_organization,
        "create_organization": handle_create_organization,
        "get_activities": handle_get_activities,
        "create_activity": handle_create_activity,
        "get_products": handle_get_products,
    }

    handler = tool_handlers.get(tool_request.name)
    if not handler:
        raise HTTPException(
            status_code=404, detail=f"Tool '{tool_request.name}' is not supported"
        )

    return await handler(api_key, tool_request.arguments)


# === Exception Handlers ===


@app.exception_handler(PipedriveError)
async def pipedrive_exception_handler(request: Request, exc: PipedriveError):
    """Handle Pipedrive errors."""
    logger.error(f"Pipedrive error: {exc}")
    return JSONResponse(
        status_code=500, content={"error": str(exc), "type": "pipedrive_error"}
    )


@app.exception_handler(PipedriveValidationError)
async def validation_exception_handler(request: Request, exc: PipedriveValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422, content={"error": str(exc), "type": "validation_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general errors."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500, content={"error": str(exc), "type": "internal_error"}
    )


# === Server Startup ===

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
        reload=False,  # Fixed: No reload to avoid import string requirement
    )
