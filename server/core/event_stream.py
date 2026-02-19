"""
SSE event types and streaming support.

Defines the 12 event types that flow from server to client.
Every execution event is typed and serializable — the server hides nothing.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator

from ..api.schemas import EventType


def _now() -> str:
    return datetime.now().isoformat()


def _id() -> str:
    return str(uuid.uuid4())[:8]


def event(event_type: EventType, **data: Any) -> dict[str, Any]:
    """Create a typed execution event."""
    return {
        "id": f"evt-{_id()}",
        "type": event_type.value,
        "timestamp": _now(),
        **data,
    }


def message_event(content: str, delta: bool = True) -> dict[str, Any]:
    """Claude produces text."""
    return event(EventType.MESSAGE, content=content, delta=delta)


def tool_use_event(tool: str, input_data: dict[str, Any], status: str = "started") -> dict[str, Any]:
    """Claude calls a tool."""
    return event(EventType.TOOL_USE, tool=tool, input=input_data, status=status)


def tool_result_event(
    tool_use_id: str,
    tool: str,
    output: str,
    exit_code: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Tool returns a result."""
    return event(
        EventType.TOOL_RESULT,
        toolUseId=tool_use_id,
        tool=tool,
        output=output,
        exitCode=exit_code,
        error=error,
    )


def sub_agent_spawn_event(
    agent_id: str,
    agent_name: str,
    model: str,
    task: str,
) -> dict[str, Any]:
    """Task tool creates a sub-agent."""
    return event(
        EventType.SUB_AGENT_SPAWN,
        agentId=agent_id,
        agentName=agent_name,
        model=model,
        task=task,
    )


def sub_agent_event(
    agent_id: str,
    event_type: str,
    nested_event: dict[str, Any],
) -> dict[str, Any]:
    """Sub-agent calls a tool (nested event)."""
    return event(
        EventType.SUB_AGENT_EVENT,
        agentId=agent_id,
        eventType=event_type,
        event=nested_event,
    )


def sub_agent_complete_event(
    agent_id: str,
    status: str,
    result: dict[str, Any] | None = None,
    duration: int = 0,
) -> dict[str, Any]:
    """Sub-agent finishes."""
    return event(
        EventType.SUB_AGENT_COMPLETE,
        agentId=agent_id,
        status=status,
        result=result or {},
        duration=duration,
    )


def permission_request_event(
    action: str,
    description: str,
    blast_radius: str = "",
) -> dict[str, Any]:
    """Claude needs approval for a mutation."""
    return event(
        EventType.PERMISSION_REQUEST,
        action=action,
        description=description,
        blastRadius=blast_radius,
        awaitingResponse=True,
    )


def permission_grant_event(permission_id: str, approved: bool) -> dict[str, Any]:
    """User approves or denies a permission request."""
    return event(
        EventType.PERMISSION_GRANT,
        permissionId=permission_id,
        approved=approved,
    )


def error_event(
    severity: str,
    source: str,
    message: str,
    recoverable: bool = True,
    related_tool_use_id: str | None = None,
) -> dict[str, Any]:
    """Error occurred during execution."""
    return event(
        EventType.ERROR,
        severity=severity,
        source=source,
        message=message,
        recoverable=recoverable,
        relatedToolUseId=related_tool_use_id,
    )


def todo_update_event(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """Todo list changed."""
    return event(EventType.TODO_UPDATE, todos=todos)


def session_info_event(
    profile: str = "",
    region: str = "",
    environment: str = "",
    suggested_name: str | None = None,
    suggested_description: str | None = None,
) -> dict[str, Any]:
    """Profile/region announced or session metadata updated."""
    data: dict[str, Any] = {}
    if profile:
        data["profile"] = profile
    if region:
        data["region"] = region
    if environment:
        data["environment"] = environment
    if suggested_name:
        data["suggestedName"] = suggested_name
    if suggested_description:
        data["suggestedDescription"] = suggested_description
    return event(EventType.SESSION_INFO, **data)


def execution_complete_event(
    event_count: int = 0,
    duration: int = 0,
    agents_spawned: int = 0,
    errors: int = 0,
    summary: str = "",
) -> dict[str, Any]:
    """Stream ends — execution summary."""
    return event(
        EventType.EXECUTION_COMPLETE,
        eventCount=event_count,
        duration=duration,
        agentsSpawned=agents_spawned,
        errors=errors,
        summary=summary,
    )


def format_sse(event_data: dict[str, Any]) -> str:
    """Format an event as an SSE message string."""
    event_type = event_data.get("type", "message")
    data_json = json.dumps(event_data)
    return f"event: {event_type}\ndata: {data_json}\n\n"
