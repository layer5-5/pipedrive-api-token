"""FastAPI application for Pipedrive MCP Server V2."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings
from .dependencies import get_dependencies
from .auth.middleware import AuthMiddleware
from .utils.errors import PipedriveError, PipedriveValidationError


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="json" if settings.log_format == "json" else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
    CORSMiddleware(
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    ),
)

# Add authentication middleware
app.add_middleware(AuthMiddleware())

# Include all routers
from .routers import mcp_router


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
        log_level=settings.log_level,
        reload=settings.environment == "development",
    )