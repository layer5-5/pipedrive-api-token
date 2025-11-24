"""
MCP tool definitions and handlers for Pipedrive.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


# Tool definitions following MCP protocol
PIPEDRIVE_TOOLS = [
    {
        "name": "get_deals",
        "description": "List deals from Pipedrive with optional filters for status, stage, and pipeline",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "won", "lost", "deleted", "all_not_deleted"],
                    "description": "Deal status filter",
                },
                "stage_id": {"type": "integer", "description": "Filter by stage ID"},
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                },
                "start": {
                    "type": "integer",
                    "description": "Pagination start",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_deal",
        "description": "Get detailed information about a specific deal by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "Pipedrive deal ID"}
            },
            "required": ["deal_id"],
        },
    },
    {
        "name": "create_deal",
        "description": "Create a new deal in Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Deal title/name"},
                "value": {"type": "number", "description": "Deal value/amount"},
                "currency": {
                    "type": "string",
                    "description": "Currency code (e.g., USD, EUR)",
                    "default": "USD",
                },
                "person_id": {
                    "type": "integer",
                    "description": "Associated person/contact ID",
                },
                "org_id": {
                    "type": "integer",
                    "description": "Associated organization ID",
                },
                "stage_id": {"type": "integer", "description": "Pipeline stage ID"},
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
                "deal_id": {"type": "integer", "description": "Deal ID to update"},
                "title": {"type": "string", "description": "Deal title"},
                "value": {"type": "number", "description": "Deal value"},
                "status": {"type": "string", "description": "Deal status"},
                "stage_id": {"type": "integer", "description": "Stage ID"},
            },
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_deal_activities",
        "description": "Get all activities (calls, emails, meetings) for a specific deal",
        "inputSchema": {
            "type": "object",
            "properties": {"deal_id": {"type": "integer", "description": "Deal ID"}},
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_deal_notes",
        "description": "Get all notes for a specific deal",
        "inputSchema": {
            "type": "object",
            "properties": {"deal_id": {"type": "integer", "description": "Deal ID"}},
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_persons",
        "description": "List contacts/persons from Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_id": {"type": "integer", "description": "Filter ID to apply"},
                "start": {
                    "type": "integer",
                    "description": "Pagination start",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_person",
        "description": "Get detailed information about a specific person/contact",
        "inputSchema": {
            "type": "object",
            "properties": {
                "person_id": {"type": "integer", "description": "Person ID"}
            },
            "required": ["person_id"],
        },
    },
    {
        "name": "create_person",
        "description": "Create a new contact/person in Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Person name"},
                "email": {"type": "string", "description": "Email address"},
                "phone": {"type": "string", "description": "Phone number"},
                "org_id": {
                    "type": "integer",
                    "description": "Associated organization ID",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_person",
        "description": "Update an existing person/contact",
        "inputSchema": {
            "type": "object",
            "properties": {
                "person_id": {"type": "integer", "description": "Person ID to update"},
                "name": {"type": "string", "description": "Person name"},
                "email": {"type": "string", "description": "Email address"},
                "phone": {"type": "string", "description": "Phone number"},
            },
            "required": ["person_id"],
        },
    },
    {
        "name": "get_organizations",
        "description": "List organizations/companies from Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_id": {"type": "integer", "description": "Filter ID to apply"},
                "start": {
                    "type": "integer",
                    "description": "Pagination start",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_organization",
        "description": "Get detailed information about a specific organization/company",
        "inputSchema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "integer", "description": "Organization ID"}
            },
            "required": ["org_id"],
        },
    },
    {
        "name": "create_organization",
        "description": "Create a new organization/company in Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Organization name"},
                "address": {"type": "string", "description": "Address"},
                "owner_id": {"type": "integer", "description": "Owner user ID"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_activities",
        "description": "List activities (calls, meetings, emails) from Pipedrive",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Activity type filter"},
                "done": {
                    "type": "integer",
                    "enum": [0, 1],
                    "description": "Filter by done status (0=not done, 1=done)",
                },
                "start": {"type": "integer", "default": 0},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "create_activity",
        "description": "Create a new activity (call, meeting, email, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Activity subject/title"},
                "type": {
                    "type": "string",
                    "description": "Activity type (call, meeting, email, etc.)",
                },
                "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)"},
                "due_time": {"type": "string", "description": "Due time (HH:MM)"},
                "deal_id": {"type": "integer", "description": "Associated deal ID"},
                "person_id": {"type": "integer", "description": "Associated person ID"},
            },
            "required": ["subject", "type"],
        },
    },
    {
        "name": "get_users",
        "description": "List all users/team members in the Pipedrive account",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_user",
        "description": "Get detailed information about a specific user",
        "inputSchema": {
            "type": "object",
            "properties": {"user_id": {"type": "integer", "description": "User ID"}},
            "required": ["user_id"],
        },
    },
    # Enhanced Deal Tools
    {
        "name": "get_enhanced_deal",
        "description": "Get detailed information about a specific deal with business intelligence (products, stage history, time metrics)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "Pipedrive deal ID"}
            },
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_enhanced_deals",
        "description": "List deals from Pipedrive with enhanced business intelligence and advanced filtering (date ranges, time metrics)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "won", "lost", "deleted", "all_not_deleted"],
                    "description": "Deal status filter",
                },
                "stage_id": {"type": "integer", "description": "Filter by stage ID"},
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                },
                "expected_close_date_start": {
                    "type": "string",
                    "description": "Filter deals with expected close date from this date (YYYY-MM-DD)",
                },
                "expected_close_date_end": {
                    "type": "string",
                    "description": "Filter deals with expected close date until this date (YYYY-MM-DD)",
                },
                "created_date_start": {
                    "type": "string",
                    "description": "Filter deals created from this date (YYYY-MM-DD)",
                },
                "created_date_end": {
                    "type": "string",
                    "description": "Filter deals created until this date (YYYY-MM-DD)",
                },
                "start": {
                    "type": "integer",
                    "description": "Pagination start",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "create_enhanced_deal",
        "description": "Create a new deal in Pipedrive with enhanced business fields (expected close date, probability, lead source)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Deal title/name"},
                "value": {"type": "number", "description": "Deal value/amount"},
                "currency": {
                    "type": "string",
                    "description": "Currency code (e.g., USD, EUR)",
                    "default": "USD",
                },
                "person_id": {
                    "type": "integer",
                    "description": "Associated person/contact ID",
                },
                "org_id": {
                    "type": "integer",
                    "description": "Associated organization ID",
                },
                "stage_id": {"type": "integer", "description": "Pipeline stage ID"},
                "expected_close_date": {
                    "type": "string",
                    "description": "Expected close date (YYYY-MM-DD)",
                },
                "probability": {
                    "type": "integer",
                    "description": "Win probability (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                },
                "lead_source": {
                    "type": "string",
                    "description": "Source of the lead (e.g., website, referral, cold_call)",
                },
                "next_activity_date": {
                    "type": "string",
                    "description": "Date of next planned activity (YYYY-MM-DD)",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "update_enhanced_deal",
        "description": "Update an existing deal with enhanced business fields",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "Deal ID to update"},
                "title": {"type": "string", "description": "Deal title"},
                "value": {"type": "number", "description": "Deal value"},
                "status": {"type": "string", "description": "Deal status"},
                "stage_id": {"type": "integer", "description": "Stage ID"},
                "expected_close_date": {
                    "type": "string",
                    "description": "Expected close date (YYYY-MM-DD)",
                },
                "actual_close_date": {
                    "type": "string",
                    "description": "Actual close date (YYYY-MM-DD)",
                },
                "lost_reason": {
                    "type": "string",
                    "description": "Reason for losing the deal",
                },
                "probability": {
                    "type": "integer",
                    "description": "Win probability (0-100)",
                    "minimum": 0,
                    "maximum": 100,
                },
                "lead_source": {"type": "string", "description": "Source of the lead"},
            },
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_deal_products",
        "description": "Get all products associated with a specific deal",
        "inputSchema": {
            "type": "object",
            "properties": {"deal_id": {"type": "integer", "description": "Deal ID"}},
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_deal_stage_history",
        "description": "Get the complete stage change history for a specific deal",
        "inputSchema": {
            "type": "object",
            "properties": {"deal_id": {"type": "integer", "description": "Deal ID"}},
            "required": ["deal_id"],
        },
    },
    {
        "name": "add_deal_product",
        "description": "Add a product to an existing deal",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "Deal ID"},
                "product_id": {"type": "integer", "description": "Product ID"},
                "quantity": {
                    "type": "integer",
                    "description": "Product quantity",
                    "default": 1,
                },
                "discount_percentage": {
                    "type": "number",
                    "description": "Discount percentage",
                    "default": 0,
                },
                "item_price": {
                    "type": "number",
                    "description": "Override product price",
                },
            },
            "required": ["deal_id", "product_id"],
        },
    },
    # Product Management Tools
    {
        "name": "get_products",
        "description": "List all products from the product catalog",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "integer",
                    "description": "Pagination start",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_product",
        "description": "Get detailed information about a specific product",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "Product ID"}
            },
            "required": ["product_id"],
        },
    },
    # Analytics Tools
    {
        "name": "calculate_deal_analytics",
        "description": "Calculate comprehensive deal analytics (conversion rates, average deal size, sales cycle)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["open", "won", "lost", "all"],
                    "description": "Filter deals by status for analytics",
                    "default": "all",
                },
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                },
                "date_range_start": {
                    "type": "string",
                    "description": "Start date for analysis (YYYY-MM-DD)",
                },
                "date_range_end": {
                    "type": "string",
                    "description": "End date for analysis (YYYY-MM-DD)",
                },
            },
        },
    },
    {
        "name": "calculate_stage_analytics",
        "description": "Calculate analytics for each pipeline stage (deal counts, conversion rates, time in stage). Can be used for counting number of deals for all stages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                }
            },
        },
    },
    {
        "name": "calculate_deal_velocity",
        "description": "Calculate deal velocity metrics (average sales cycle, fastest/slowest deals)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["won", "lost", "all"],
                    "description": "Filter deals by status for velocity calculation",
                    "default": "won",
                },
                "date_range_start": {
                    "type": "string",
                    "description": "Start date for velocity analysis (YYYY-MM-DD)",
                },
                "date_range_end": {
                    "type": "string",
                    "description": "End date for velocity analysis (YYYY-MM-DD)",
                },
            },
        },
    },
    {
        "name": "calculate_pipeline_health",
        "description": "Calculate overall pipeline health score with recommendations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                }
            },
        },
    },
    {
        "name": "forecast_revenue",
        "description": "Forecast revenue based on current pipeline with multiple scenarios",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to forecast",
                    "default": 90,
                },
                "pipeline_id": {
                    "type": "integer",
                    "description": "Filter by pipeline ID",
                },
                "probability_threshold": {
                    "type": "integer",
                    "description": "Minimum probability to include in forecast",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "get_deal_time_in_stages",
        "description": "Get detailed time analysis for how long deals spend in each pipeline stage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "Deal ID to analyze"}
            },
            "required": ["deal_id"],
        },
    },
]


def format_mcp_response(data: Any, is_error: bool = False) -> Dict[str, Any]:
    """
    Format response in MCP protocol format.

    Args:
        data: Response data (dict, list, or primitive)
        is_error: Whether this is an error response

    Returns:
        MCP-formatted response dict
    """
    import json

    # Convert data to readable string
    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=2)
    else:
        text = str(data)

    response: Dict[str, Any] = {"content": [{"type": "text", "text": text}]}

    if is_error:
        response["isError"] = True  # type: ignore

    return response
