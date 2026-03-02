"""
FastAPI application for Hackathon Email Gateway.
Main entry point with all API endpoints and frontend serving.
"""

import os
from datetime import datetime
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger("protopost")

from .models import EmailPayload, Provider, AppConfig, RoutingConfig
from .config_manager import config_manager
from .database import database_manager
from .router import routing_engine

import sys as _sys
import os as _os


def _resource_path(rel: str) -> str:
    """Resolve a bundled read-only asset path (PyInstaller-compatible)."""
    meipass = getattr(_sys, "_MEIPASS", None)
    if meipass:
        return _os.path.join(meipass, rel)
    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    return _os.path.join(root, rel)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_manager.initialize()
    try:
        await config_manager.load()
    except Exception:
        config_manager.save_sync(config_manager.get_default_config())
    yield
    database_manager.close()


# Initialize FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="ProtoPost",
    description="A local proxy server for routing and mocking outbound emails",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# Optional bearer auth — enabled only when AUTH_TOKEN env var is set.
# If not set, all requests pass through freely (local dev default).
# ---------------------------------------------------------------------------
_AUTH_TOKEN: str | None = os.getenv("AUTH_TOKEN")


async def require_auth(
    authorization: str | None = Header(default=None)
) -> None:
    """FastAPI dependency — validates Bearer token when AUTH_TOKEN is configured."""
    if not _AUTH_TOKEN:
        return  # Auth disabled — no env var set
    if authorization != f"Bearer {_AUTH_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Provide a valid Bearer token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# CORS - Allow all origins (local developer tool)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static assets
app.mount("/static", StaticFiles(directory=_resource_path("frontend")), name="static")


# Serve frontend dashboard at root
@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serve the dashboard HTML file."""
    return FileResponse(_resource_path("frontend/index.html"))


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    Returns server status and database connectivity.
    """
    try:
        # Test database connectivity
        database_manager.get_stats()
        db_connected = True
    except Exception:
        db_connected = False
    
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "db_connected": db_connected,
        "version": "1.0.0"
    }


# Email sending endpoint
@app.post("/api/send", dependencies=[Depends(require_auth)])
async def send_email(payload: EmailPayload):
    """
    Send an email through the gateway.
    Routes to configured providers based on routing mode.
    
    Request Body:
        - from: Sender email address
        - to: List of recipient email addresses
        - subject: Email subject
        - body_text: Plain text body (optional)
        - body_html: HTML body (optional)
        - reply_to: Reply-to address (optional)
    
    Returns:
        Success response with provider info and timing
    """
    try:
        result = await routing_engine.route(payload)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Routing Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error. Check server logs for details."}
        )


# Get email logs with pagination
@app.get("/api/logs", dependencies=[Depends(require_auth)])
async def get_logs(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip")
):
    """
    Retrieve email logs with pagination.
    
    Query Parameters:
        - limit: Maximum number of logs (1-500, default 100)
        - offset: Number of logs to skip (default 0)
    
    Returns:
        List of log entries ordered by timestamp (newest first)
    """
    try:
        logs = database_manager.get_logs(limit=limit, offset=offset)
        return {
            "logs": logs,
            "limit": limit,
            "offset": offset,
            "total": database_manager.get_total_count()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs: {str(e)}"
        )


# Get single log by ID
@app.get("/api/logs/{log_id}", dependencies=[Depends(require_auth)])
async def get_log_detail(log_id: str):
    """
    Retrieve detailed information for a single log entry.
    
    Path Parameters:
        - log_id: Unique log entry ID
    
    Returns:
        Complete log entry with all fields
    """
    try:
        log = database_manager.get_log_by_id(log_id)
        
        if not log:
            raise HTTPException(
                status_code=404,
                detail=f"Log entry not found: {log_id}"
            )
        
        return log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve log: {str(e)}"
        )


# Get aggregate statistics
@app.get("/api/stats", dependencies=[Depends(require_auth)])
async def get_stats():
    """
    Get aggregate statistics across all logs.
    
    Returns:
        Statistics including total sent, failed, sandbox, and average processing time
    """
    try:
        stats = database_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


# Get current configuration
@app.get("/api/config", dependencies=[Depends(require_auth)])
async def get_config():
    """
    Get current application configuration.
    
    Returns:
        Complete AppConfig including providers and routing settings
    """
    try:
        config = await config_manager.load()
        return config.model_dump(mode='json')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load configuration: {str(e)}"
        )


# Update entire configuration
@app.put("/api/config", dependencies=[Depends(require_auth)])
async def update_config(new_config: AppConfig):
    """
    Update the entire application configuration.
    
    Request Body:
        Complete AppConfig object with providers and routing settings
    
    Returns:
        Saved configuration
    """
    try:
        await config_manager.save(new_config)
        return new_config.model_dump(mode='json')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save configuration: {str(e)}"
        )


# Add a new provider
@app.post("/api/config/providers", dependencies=[Depends(require_auth)])
async def add_provider(provider: Provider):
    """
    Add a new email provider to the configuration.
    
    Request Body:
        Provider configuration with type-specific credentials
    
    Returns:
        Updated configuration
    """
    try:
        config = await config_manager.load()
        
        # Check for duplicate provider names
        if any(p.name == provider.name for p in config.providers):
            raise HTTPException(
                status_code=400,
                detail=f"A provider named '{provider.name}' already exists"
            )
        
        config.providers.append(provider)
        await config_manager.save(config)
        
        return {
            "message": "Provider added successfully",
            "provider": provider.model_dump(mode='json'),
            "config": config.model_dump(mode='json')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add provider: {str(e)}"
        )


# Update an existing provider
@app.put("/api/config/providers/{provider_id}", dependencies=[Depends(require_auth)])
async def update_provider(provider_id: str, updated_provider: Provider):
    """
    Update an existing provider by ID.
    
    Path Parameters:
        - provider_id: Unique provider ID
    
    Request Body:
        Updated provider configuration
    
    Returns:
        Updated configuration
    """
    try:
        config = await config_manager.load()
        
        # Find provider index
        provider_index = None
        for i, p in enumerate(config.providers):
            if p.id == provider_id:
                provider_index = i
                break
        
        if provider_index is None:
            raise HTTPException(
                status_code=404,
                detail=f"Provider not found: {provider_id}"
            )
        
        # Preserve the ID
        updated_provider.id = provider_id
        config.providers[provider_index] = updated_provider
        
        await config_manager.save(config)
        
        return {
            "message": "Provider updated successfully",
            "provider": updated_provider.model_dump(mode='json'),
            "config": config.model_dump(mode='json')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update provider: {str(e)}"
        )


# Delete a provider
@app.delete("/api/config/providers/{provider_id}", dependencies=[Depends(require_auth)])
async def delete_provider(provider_id: str):
    """
    Delete a provider by ID.
    
    Path Parameters:
        - provider_id: Unique provider ID
    
    Returns:
        Updated configuration
    """
    try:
        config = await config_manager.load()
        
        # Find and remove provider
        original_count = len(config.providers)
        config.providers = [p for p in config.providers if p.id != provider_id]
        
        if len(config.providers) == original_count:
            raise HTTPException(
                status_code=404,
                detail=f"Provider not found: {provider_id}"
            )
        
        await config_manager.save(config)
        
        return {
            "message": "Provider deleted successfully",
            "config": config.model_dump(mode='json')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete provider: {str(e)}"
        )


# Update routing configuration
@app.post("/api/config/routing", dependencies=[Depends(require_auth)])
async def update_routing(routing: RoutingConfig):
    """
    Update routing configuration (mode and sandbox).
    
    Request Body:
        - mode: "manual" or "smart"
        - sandbox: boolean
    
    Returns:
        Updated configuration
    """
    try:
        config = await config_manager.load()
        config.routing = routing
        
        await config_manager.save(config)
        
        return {
            "message": "Routing configuration updated successfully",
            "routing": routing.model_dump(mode='json'),
            "config": config.model_dump(mode='json')
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update routing configuration: {str(e)}"
        )
