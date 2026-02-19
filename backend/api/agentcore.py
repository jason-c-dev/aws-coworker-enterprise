"""
AgentCore protocol endpoints: /ping and /invocations.

These implement the Bedrock AgentCore container contract:
- GET /ping → health check
- POST /invocations → unified API entry point
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .schemas import HealthResponse, InvocationRequest, InvocationResponse

router = APIRouter()


@router.get("/ping")
async def ping() -> HealthResponse:
    """Health check — AgentCore liveness probe."""
    return HealthResponse(status="Healthy")


@router.post("/invocations")
async def invocations(request: InvocationRequest) -> InvocationResponse:
    """
    Unified API endpoint — AgentCore protocol contract.

    Routes requests to the appropriate session/message handler.
    For streaming, clients should use /api/sessions/{id}/messages/stream instead.
    """
    from ..main import app_state

    session_mgr = app_state["session_manager"]

    # Get or create session
    if request.sessionId:
        meta = session_mgr.get(request.sessionId)
        if meta is None:
            from .schemas import SessionCreate
            meta = session_mgr.create(SessionCreate(name=None))
    else:
        from .schemas import SessionCreate
        meta = session_mgr.create(SessionCreate(name=None))

    # TODO: Route through SDK client for real responses
    # For now, return a placeholder
    return InvocationResponse(
        sessionId=meta.id,
        messageId="msg-placeholder",
        content=f"[Mock] Received: {request.input}",
    )
