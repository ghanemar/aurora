"""Aurora FastAPI application entry point.

This module creates and configures the FastAPI application with:
- CORS middleware for frontend integration
- Authentication router
- Health check endpoint
- API versioning
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth
from src.api.routers import (
    agreements,
    commissions,
    partner_wallets,
    partners,
    periods,
    validators,
)
from src.config.settings import settings

# Get settings
settings = settings

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Chain Validator P&L & Partner Commissions Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth.router, prefix=settings.api_v1_prefix)

# Include business routers
app.include_router(validators.router, prefix=settings.api_v1_prefix)
app.include_router(partners.router, prefix=settings.api_v1_prefix)
app.include_router(partner_wallets.router, prefix=settings.api_v1_prefix)
app.include_router(agreements.router, prefix=settings.api_v1_prefix)
app.include_router(commissions.router, prefix=settings.api_v1_prefix)
app.include_router(periods.router, prefix=settings.api_v1_prefix)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status message
    """
    return {"status": "ok", "version": settings.app_version}


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        Dictionary with API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }
