"""
Session management and messaging endpoints.

Covers:
- Session CRUD (create, list, get, update, delete)
- Send messages (streaming and non-streaming)
- Conversation history
- Artifact management
- Permission grants
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from .schemas import (
    ArtifactDetail,
    ArtifactSummary,
    MessageRequest,
    MessageResponse,
    PermissionGrant,
    SessionCreate,
    SessionDeleteResult,
    SessionDetail,
    SessionMetadata,
    SessionSummary,
    SessionUpdate,
)

router = APIRouter(prefix="/api")


def _get_state():
    """Get app state — imported lazily to avoid circular imports."""
    from ..main import app_state
    return app_state


# ============================================================
# Session CRUD
# ============================================================

@router.post("/sessions", response_model=SessionMetadata)
async def create_session(request: SessionCreate) -> SessionMetadata:
    """Create a new session with workspace directory."""
    state = _get_state()
    return state["session_manager"].create(request)


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions() -> list[SessionSummary]:
    """List all sessions."""
    state = _get_state()
    return state["session_manager"].list()


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail:
    """Get full session details including artifact list."""
    state = _get_state()
    detail = state["session_manager"].get_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return detail


@router.patch("/sessions/{session_id}", response_model=SessionMetadata)
async def update_session(session_id: str, request: SessionUpdate) -> SessionMetadata:
    """Update session metadata (rename, update description)."""
    state = _get_state()
    meta = state["session_manager"].update(session_id, request)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return meta


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResult)
async def delete_session(session_id: str) -> SessionDeleteResult:
    """Delete session — cascading delete of all artifacts and workspace."""
    state = _get_state()

    # Cancel any pending permissions
    state["permission_handler"].cancel_all(session_id)

    # Close SDK client if active
    client = state.get("sdk_clients", {}).pop(session_id, None)
    if client:
        await client.close()

    result = state["session_manager"].delete(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return result


# ============================================================
# Messages
# ============================================================

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(session_id: str, request: MessageRequest) -> MessageResponse:
    """Send a message to a session (non-streaming)."""
    state = _get_state()
    session_mgr = state["session_manager"]

    meta = session_mgr.get(session_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session_mgr.update_activity(session_id)

    # Record user message in history
    message_id = f"msg-{uuid.uuid4().hex[:8]}"
    session_mgr.append_history(session_id, {
        "id": message_id,
        "role": "user",
        "content": request.content,
        "timestamp": datetime.now().isoformat(),
    })

    # Get or create SDK client
    sdk_clients = state.setdefault("sdk_clients", {})
    if session_id not in sdk_clients:
        from ..core.sdk_client import SDKClientWrapper
        from ..config import PROJECT_ROOT
        sdk_clients[session_id] = SDKClientWrapper(
            session_id=session_id,
            project_root=str(PROJECT_ROOT),
            profile=meta.profile,
            region=meta.region,
        )

    client = sdk_clients[session_id]

    # Collect all events (non-streaming)
    events = []
    full_content = ""
    async for sse_msg in client.send_message(request.content):
        # Parse the SSE message to extract event data
        import json
        for line in sse_msg.strip().split("\n"):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                events.append(data)
                if data.get("type") == "message" and not data.get("delta", True):
                    full_content = data.get("content", "")

    # Record assistant response in history
    response_id = f"msg-{uuid.uuid4().hex[:8]}"
    session_mgr.append_history(session_id, {
        "id": response_id,
        "role": "assistant",
        "content": full_content,
        "timestamp": datetime.now().isoformat(),
        "events": events,
    })

    return MessageResponse(
        sessionId=session_id,
        messageId=response_id,
        content=full_content,
        events=events,
    )


@router.post("/sessions/{session_id}/messages/stream")
async def stream_message(session_id: str, request: MessageRequest):
    """Send a message with SSE streaming — returns all execution events in real time."""
    state = _get_state()
    session_mgr = state["session_manager"]

    meta = session_mgr.get(session_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session_mgr.update_activity(session_id)

    # Record user message
    session_mgr.append_history(session_id, {
        "id": f"msg-{uuid.uuid4().hex[:8]}",
        "role": "user",
        "content": request.content,
        "timestamp": datetime.now().isoformat(),
    })

    # Get or create SDK client
    sdk_clients = state.setdefault("sdk_clients", {})
    if session_id not in sdk_clients:
        from ..core.sdk_client import SDKClientWrapper
        from ..config import PROJECT_ROOT
        sdk_clients[session_id] = SDKClientWrapper(
            session_id=session_id,
            project_root=str(PROJECT_ROOT),
            profile=meta.profile,
            region=meta.region,
        )

    client = sdk_clients[session_id]

    async def event_generator():
        import json as _json

        events: list[dict] = []
        full_content = ""

        async for sse_msg in client.send_message(request.content):
            # Forward every SSE chunk to the client immediately
            yield sse_msg

            # Also buffer events so we can persist the assistant response
            for line in sse_msg.strip().split("\n"):
                if line.startswith("data: "):
                    try:
                        data = _json.loads(line[6:])
                        events.append(data)
                        # Capture the final (non-delta) message content
                        if data.get("type") == "message" and not data.get("delta", True):
                            full_content = data.get("content", "")
                    except _json.JSONDecodeError:
                        pass

        # Persist the assistant response to history after streaming completes
        if full_content or events:
            response_id = f"msg-{uuid.uuid4().hex[:8]}"
            session_mgr.append_history(session_id, {
                "id": response_id,
                "role": "assistant",
                "content": full_content,
                "timestamp": datetime.now().isoformat(),
                "events": events,
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str) -> list[dict[str, Any]]:
    """Get conversation history with execution events."""
    state = _get_state()
    session_mgr = state["session_manager"]

    if session_mgr.get(session_id) is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session_mgr.get_history(session_id)


# ============================================================
# Artifacts
# ============================================================

@router.get("/sessions/{session_id}/artifacts", response_model=list[ArtifactSummary])
async def list_artifacts(session_id: str) -> list[ArtifactSummary]:
    """List all artifacts for a session."""
    state = _get_state()
    am = state["session_manager"].get_artifact_manager(session_id)
    if am is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return am.list()


@router.get("/sessions/{session_id}/artifacts/{artifact_id}")
async def get_artifact(session_id: str, artifact_id: str):
    """Get/download a specific artifact."""
    state = _get_state()
    am = state["session_manager"].get_artifact_manager(session_id)
    if am is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    path = am.get_path(artifact_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")

    return FileResponse(
        path=str(path),
        filename=path.name,
    )


@router.post("/sessions/{session_id}/artifacts", response_model=ArtifactSummary)
async def upload_artifact(
    session_id: str,
    file: UploadFile = File(...),
) -> ArtifactSummary:
    """Upload/create an artifact."""
    state = _get_state()
    am = state["session_manager"].get_artifact_manager(session_id)
    if am is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return am.create_from_upload(file.filename or "unnamed", file.file)


@router.delete("/sessions/{session_id}/artifacts/{artifact_id}")
async def delete_artifact(session_id: str, artifact_id: str) -> dict[str, str]:
    """Delete a specific artifact."""
    state = _get_state()
    am = state["session_manager"].get_artifact_manager(session_id)
    if am is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    if not am.delete(artifact_id):
        raise HTTPException(status_code=404, detail=f"Artifact not found: {artifact_id}")

    return {"status": "deleted", "id": artifact_id}


# ============================================================
# Permissions
# ============================================================

@router.post("/sessions/{session_id}/permissions/{permission_id}")
async def grant_permission(
    session_id: str,
    permission_id: str,
    request: PermissionGrant,
) -> dict[str, Any]:
    """Approve or deny a pending permission request."""
    state = _get_state()
    handler = state["permission_handler"]

    success = handler.grant(permission_id, request.approved)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Permission request not found or already resolved: {permission_id}",
        )

    return {
        "permissionId": permission_id,
        "approved": request.approved,
        "status": "resolved",
    }
