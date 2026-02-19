"""
ACW Server — FastAPI Application

The ACW Server wraps AWS Coworker via the Claude Code SDK, exposing
a REST + SSE API for session management, resource browsing, and execution
observability. It runs standalone — the web UI is an optional reference
implementation that consumes this API.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .api import agentcore, sessions, resources, observability, diagrams
from .core.session_manager import SessionManager
from .core.permission_handler import PermissionHandler
from .file_ops.safe_manager import SafeFileManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Shared application state — accessible from route handlers
app_state: dict[str, Any] = {}

# Detect web UI build at import time (optional reference implementation)
webui_dist = config.PROJECT_ROOT / "web-ui" / "dist"
WEBUI_AVAILABLE = webui_dist.exists()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("=" * 60)
    logger.info("ACW Server starting")
    logger.info(f"Project root: {config.PROJECT_ROOT}")
    logger.info(f"Workspace base: {config.WORKSPACE_BASE}")
    logger.info(f"Bedrock mode: {config.CLAUDE_CODE_USE_BEDROCK}")
    logger.info("=" * 60)

    # Initialize file manager with resource base paths
    file_manager = SafeFileManager({
        "commands": config.COMMANDS_DIR,
        "agents": config.AGENTS_DIR,
        "skills": config.SKILLS_DIR,
        "config": config.CONFIG_DIR,
    })

    # Initialize session manager
    session_manager = SessionManager(
        workspace_base=config.WORKSPACE_BASE,
        max_sessions=config.MAX_SESSIONS,
    )

    # Initialize permission handler
    permission_handler = PermissionHandler()

    # Populate shared state
    app_state["file_manager"] = file_manager
    app_state["session_manager"] = session_manager
    app_state["permission_handler"] = permission_handler
    app_state["sdk_clients"] = {}

    logger.info("Application state initialized")

    # Log discovered resources
    for category in ("commands", "agents", "skills"):
        files = file_manager.list_files(category)
        logger.info(f"Found {len(files)} {category}: {[f['name'] for f in files]}")

    if WEBUI_AVAILABLE:
        logger.info(f"Serving web UI from {webui_dist}")
    else:
        logger.info("No web UI build found — API-only mode")

    yield

    # Shutdown: close all SDK clients
    for session_id, client in app_state.get("sdk_clients", {}).items():
        try:
            await client.close()
        except Exception as e:
            logger.warning(f"Error closing SDK client for {session_id}: {e}")

    logger.info("ACW Server stopped")


# Create FastAPI application
app = FastAPI(
    title="ACW Server",
    description="AWS Coworker Server — REST + SSE API for session management, resource browsing, and execution observability",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — permissive for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(agentcore.router)
app.include_router(sessions.router)
app.include_router(resources.router)
app.include_router(observability.router)
app.include_router(diagrams.router)

# Serve web UI static assets (CSS, JS, images) from /assets/ if available
if WEBUI_AVAILABLE:
    assets_dir = webui_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")


@app.get("/")
async def root():
    """Serve web UI index.html (if available) or API info."""
    if WEBUI_AVAILABLE:
        return FileResponse(str(webui_dist / "index.html"))
    return JSONResponse({
        "service": "ACW Server",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/ping",
            "sessions": "/api/sessions",
            "commands": "/api/commands",
            "skills": "/api/skills",
            "agents": "/api/agents",
            "config": "/api/config",
            "diagrams": "/api/diagrams/generate",
        },
    })


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """
    SPA catch-all: serve index.html for any non-API, non-asset path.
    Only active when the web UI reference implementation is bundled.
    """
    if WEBUI_AVAILABLE:
        # Check if it's a real static file first
        static_file = webui_dist / full_path
        if static_file.is_file() and webui_dist in static_file.resolve().parents:
            return FileResponse(str(static_file))
        # Otherwise serve index.html for SPA routing
        return FileResponse(str(webui_dist / "index.html"))
    return JSONResponse({"error": "Not found"}, status_code=404)
