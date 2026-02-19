"""
Pydantic models for all API request/response schemas.

Organized by domain: sessions, artifacts, resources, events, diagrams.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


# ============================================================
# Enums
# ============================================================

class SessionStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"


class ArtifactSource(str, Enum):
    MODEL_GENERATED = "model-generated"
    USER_UPLOADED = "user-uploaded"
    SYSTEM_EXPORTED = "system-exported"


class EventType(str, Enum):
    MESSAGE = "message"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    SUB_AGENT_SPAWN = "sub_agent_spawn"
    SUB_AGENT_EVENT = "sub_agent_event"
    SUB_AGENT_COMPLETE = "sub_agent_complete"
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_GRANT = "permission_grant"
    ERROR = "error"
    TODO_UPDATE = "todo_update"
    SESSION_INFO = "session_info"
    EXECUTION_COMPLETE = "execution_complete"


# ============================================================
# Sessions
# ============================================================

class SessionCreate(BaseModel):
    """Request to create a new session."""
    name: Optional[str] = None  # Auto-generated if not provided
    profile: Optional[str] = None
    region: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request to update session metadata."""
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None


class SessionMetadata(BaseModel):
    """Session metadata — stored as session.json in workspace."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Session"
    description: str = ""
    profile: str = ""
    region: str = ""
    environment: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    created: datetime = Field(default_factory=datetime.now)
    lastActivity: datetime = Field(default_factory=datetime.now)
    artifactCount: int = 0


class SessionSummary(BaseModel):
    """Session summary for list views."""
    id: str
    name: str
    description: str
    status: SessionStatus
    profile: str
    region: str
    environment: str = ""
    created: datetime
    lastActivity: datetime
    artifactCount: int


class SessionDetail(SessionMetadata):
    """Full session details including artifact list."""
    artifacts: list["ArtifactSummary"] = []


class SessionDeleteResult(BaseModel):
    """Result of deleting a session."""
    id: str
    artifactsDeleted: int
    status: str = "deleted"


# ============================================================
# Artifacts
# ============================================================

class ArtifactSummary(BaseModel):
    """Artifact summary for list views."""
    id: str
    name: str
    type: str  # MIME type or extension
    size: int  # bytes
    source: ArtifactSource
    created: datetime


class ArtifactDetail(ArtifactSummary):
    """Full artifact details."""
    sessionId: str
    path: str  # relative path within session workspace


# ============================================================
# Messages
# ============================================================

class MessageRequest(BaseModel):
    """Request to send a message to a session."""
    content: str


class MessageResponse(BaseModel):
    """Response from a non-streaming message."""
    sessionId: str
    messageId: str
    content: str
    events: list["ExecutionEvent"] = []
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# Events (SSE stream types)
# ============================================================

class ExecutionEvent(BaseModel):
    """Base event in the execution stream."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: dict[str, Any] = {}


class PermissionGrant(BaseModel):
    """User's response to a permission request."""
    approved: bool


# ============================================================
# Resources (Commands, Skills, Agents, Config)
# ============================================================

class ResourceMetadata(BaseModel):
    """Parsed YAML frontmatter from a resource file."""
    raw: dict[str, Any] = {}  # Full frontmatter dict


class ResourceDetail(BaseModel):
    """Full resource file — metadata + body."""
    id: str
    name: str
    category: str
    metadata: dict[str, Any] = {}
    content: str = ""  # Markdown body
    editable: bool = True
    isDirty: bool = False


class ResourceUpdate(BaseModel):
    """Request to update a resource file."""
    metadata: Optional[dict[str, Any]] = None
    content: Optional[str] = None


class ResourceCreate(BaseModel):
    """Request to create a new resource file."""
    id: str  # File name (without .md)
    metadata: dict[str, Any] = {}
    content: str = ""


class CommandSummary(BaseModel):
    """Command summary for list views."""
    name: str
    description: str
    agent: str
    skills: list[str] = []
    tools: list[str] = []
    arguments: list[dict[str, Any]] = []


class SkillTreeNode(BaseModel):
    """Node in the skill hierarchy tree."""
    name: str
    type: str  # "file" or "directory"
    path: str
    size: Optional[int] = None
    modified: Optional[float] = None
    children: Optional[list["SkillTreeNode"]] = None


class AgentSummary(BaseModel):
    """Agent summary for list views."""
    id: str
    name: str
    content: str  # Full body (agents may not have structured frontmatter)


class ValidationResponse(BaseModel):
    """Result of validating a resource file."""
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []


# ============================================================
# Config
# ============================================================

class ConfigSection(BaseModel):
    """A configuration section."""
    section: str
    metadata: dict[str, Any] = {}
    content: str = ""
    fileType: str = "markdown"  # "markdown" or "yaml"


# ============================================================
# Diagrams
# ============================================================

class DiagramRequest(BaseModel):
    """Request to generate a diagram."""
    type: str = "architecture"  # architecture, flowchart, sequence
    resources: dict[str, Any] = {}  # Discovery data
    format: str = "svg"  # svg, png


class DiagramResponse(BaseModel):
    """Generated diagram response."""
    type: str
    format: str
    content: str  # SVG string or base64 PNG
    artifactId: Optional[str] = None  # If saved as artifact


# ============================================================
# AgentCore Protocol
# ============================================================

class InvocationRequest(BaseModel):
    """AgentCore /invocations request."""
    sessionId: Optional[str] = None
    action: str = "chat"
    input: str = ""
    streaming: bool = True


class InvocationResponse(BaseModel):
    """AgentCore /invocations response (non-streaming)."""
    sessionId: str
    messageId: str
    content: str
    events: list[dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "Healthy"


# Rebuild forward refs for self-referencing models
SkillTreeNode.model_rebuild()
SessionDetail.model_rebuild()
