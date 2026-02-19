"""
Observability endpoints — execution traces and logs.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api")


def _get_state():
    from ..main import app_state
    return app_state


@router.get("/sessions/{session_id}/trace")
async def get_session_trace(session_id: str) -> dict[str, Any]:
    """
    Get full execution trace for a session.

    Returns a tree of all events across all messages, organized by message.
    """
    state = _get_state()
    session_mgr = state["session_manager"]

    if session_mgr.get(session_id) is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    history = session_mgr.get_history(session_id)

    # Build trace tree from history
    trace_messages = []
    for entry in history:
        trace_messages.append({
            "id": entry.get("id", ""),
            "role": entry.get("role", ""),
            "content": entry.get("content", "")[:200],  # Truncate for overview
            "timestamp": entry.get("timestamp", ""),
            "events": entry.get("events", []),
            "eventCount": len(entry.get("events", [])),
        })

    return {
        "sessionId": session_id,
        "messageCount": len(trace_messages),
        "messages": trace_messages,
    }


@router.get("/sessions/{session_id}/logs")
async def get_session_logs(
    session_id: str,
    level: str = Query(default=None, description="Filter by level: error, warning, info"),
    source: str = Query(default=None, description="Filter by source: Bash, Read, etc."),
    keyword: str = Query(default=None, description="Filter by keyword in message"),
) -> dict[str, Any]:
    """
    Get filtered log entries for a session.

    Extracts error, warning, and info events from the session's execution history.
    """
    state = _get_state()
    session_mgr = state["session_manager"]

    if session_mgr.get(session_id) is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    history = session_mgr.get_history(session_id)

    # Extract log-worthy events from history
    logs = []
    for entry in history:
        for evt in entry.get("events", []):
            evt_type = evt.get("type", "")

            # Map event types to log entries
            log_entry = None

            if evt_type == "error":
                log_entry = {
                    "timestamp": evt.get("timestamp", ""),
                    "level": evt.get("severity", "error"),
                    "source": evt.get("source", "unknown"),
                    "message": evt.get("message", ""),
                }
            elif evt_type == "tool_result" and evt.get("error"):
                log_entry = {
                    "timestamp": evt.get("timestamp", ""),
                    "level": "error",
                    "source": evt.get("tool", "unknown"),
                    "message": evt.get("error", ""),
                }
            elif evt_type == "tool_result" and evt.get("exitCode", 0) != 0:
                log_entry = {
                    "timestamp": evt.get("timestamp", ""),
                    "level": "warning",
                    "source": evt.get("tool", "unknown"),
                    "message": f"Exit code {evt.get('exitCode')}: {evt.get('output', '')[:200]}",
                }
            elif evt_type == "sub_agent_complete" and evt.get("status") != "success":
                log_entry = {
                    "timestamp": evt.get("timestamp", ""),
                    "level": "warning",
                    "source": evt.get("agentId", "sub-agent"),
                    "message": f"Sub-agent completed with status: {evt.get('status')}",
                }

            if log_entry is None:
                continue

            # Apply filters
            if level and log_entry["level"] != level:
                continue
            if source and source.lower() not in log_entry["source"].lower():
                continue
            if keyword and keyword.lower() not in log_entry["message"].lower():
                continue

            logs.append(log_entry)

    return {
        "sessionId": session_id,
        "count": len(logs),
        "logs": logs,
    }
