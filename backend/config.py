"""
AWS Coworker Web UI — Configuration

Loads environment config and provides project path constants.
"""

import os
from pathlib import Path

# Project root: the aws-coworker-enterprise directory
# When running locally: backend/../
# When running in container: /opt/aws-coworker
PROJECT_ROOT = Path(os.getenv(
    "AWS_COWORKER_ROOT",
    Path(__file__).parent.parent.resolve()
))

# Resource paths (relative to project root)
COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SKILLS_DIR = PROJECT_ROOT / "skills"
CONFIG_DIR = PROJECT_ROOT / "config"
CLAUDE_CONFIG_DIR = PROJECT_ROOT / ".claude" / "config"

# Session workspace base
WORKSPACE_BASE = Path(os.getenv(
    "WORKSPACE_BASE_PATH",
    PROJECT_ROOT / "workspaces"
))

# Server config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Claude SDK config
CLAUDE_CODE_USE_BEDROCK = os.getenv("CLAUDE_CODE_USE_BEDROCK", "0") == "1"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "")

# Session config
SESSION_IDLE_TIMEOUT_SECONDS = int(os.getenv("SESSION_IDLE_TIMEOUT", "3600"))  # 1 hour
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "10"))

# Allowed tools for SDK sessions
ALLOWED_TOOLS = os.getenv(
    "ALLOWED_TOOLS",
    "Read,Write,Edit,Bash,Glob,Grep,Task,TodoWrite"
).split(",")
