"""
AWS Coworker Web UI — FastAPI Application

Main application setup with all routers, CORS, and shared state.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("=" * 60)
    logger.info("AWS Coworker Web UI starting")
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
        "claude_config": config.CLAUDE_CONFIG_DIR,
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

    yield

    # Shutdown: close all SDK clients
    for session_id, client in app_state.get("sdk_clients", {}).items():
        try:
            await client.close()
        except Exception as e:
            logger.warning(f"Error closing SDK client for {session_id}: {e}")

    logger.info("AWS Coworker Web UI stopped")


# Create FastAPI application
app = FastAPI(
    title="AWS Coworker Web UI",
    description="Developer workbench for AWS Coworker — chat, resource management, and execution observability",
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

# Mount routers
app.include_router(agentcore.router)
app.include_router(sessions.router)
app.include_router(resources.router)
app.include_router(observability.router)
app.include_router(diagrams.router)

# Serve frontend static files if the build directory exists
frontend_dist = config.PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_dist}")


# Root redirect (when no frontend build exists)
@app.get("/")
async def root():
    return {
        "service": "AWS Coworker Web UI",
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
    }
