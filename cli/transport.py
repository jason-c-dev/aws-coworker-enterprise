"""
Transport abstraction for ACW CLI.

Defines the interface that all transports must implement, plus the
HTTPTransport for Day 1 (local + EC2/ECS).

AgentCoreTransport (Part 4) will implement the same interface using
boto3's InvokeAgentRuntime API with SigV4 auth.

Architecture:
    ACWClient (session management, rendering, input)
        └── Transport (abstract)
              ├── HTTPTransport          ← Day 1 (local + EC2/ECS)
              └── AgentCoreTransport     ← Part 4
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass
class SessionInfo:
    """Represents a session on the server."""
    id: str
    profile: str = ""
    region: str = ""
    status: str = "active"
    created_at: str = ""


class Transport(ABC):
    """
    Abstract transport interface for the ACW CLI.

    All transports must implement these methods. The ACWClient calls
    them without knowing whether it's talking raw HTTP or going through
    the AWS InvokeAgentRuntime API.

    The contract:
        - create_session() → SessionInfo
        - send_message() → AsyncIterator of raw SSE event dicts
        - list_sessions() → list of SessionInfo
        - health_check() → bool
        - close() → cleanup
    """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the server/runtime is reachable and healthy."""
        ...

    @abstractmethod
    async def create_session(self, profile: str = "", region: str = "") -> SessionInfo:
        """Create a new session and return its info."""
        ...

    @abstractmethod
    async def list_sessions(self) -> list[SessionInfo]:
        """List available sessions. May not be supported by all transports."""
        ...

    @abstractmethod
    async def send_message(self, session_id: str, content: str) -> AsyncIterator[dict[str, Any]]:
        """
        Send a message and yield parsed SSE event dicts.

        Each dict has at minimum a 'type' key matching one of the 12 SSE
        event types: message, tool_use, tool_result, sub_agent_spawn,
        sub_agent_event, sub_agent_complete, permission_request,
        permission_grant, error, todo_update, session_info,
        execution_complete.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (HTTP client, connections, etc.)."""
        ...


class HTTPTransport(Transport):
    """
    HTTP/SSE transport for direct server communication.

    Used for:
        - Local development (no auth, localhost)
        - Remote EC2/ECS (API key auth)

    Auth behaviour:
        - If api_key is provided, sends Authorization: Bearer <key>
        - If api_key is None, no auth header (localhost trust model)
    """

    def __init__(self, base_url: str = "http://localhost:8080", api_key: str | None = None):
        import httpx
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(headers=headers)

    async def health_check(self) -> bool:
        """Check server health via /ping endpoint."""
        try:
            resp = await self._client.get(f"{self._base_url}/ping", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def create_session(self, profile: str = "", region: str = "") -> SessionInfo:
        """Create a new session via POST /api/sessions."""
        resp = await self._client.post(
            f"{self._base_url}/api/sessions",
            json={"profile": profile, "region": region},
        )
        resp.raise_for_status()
        data = resp.json()
        return SessionInfo(
            id=data["id"],
            profile=data.get("profile", profile),
            region=data.get("region", region),
            status=data.get("status", "active"),
            created_at=data.get("created_at", ""),
        )

    async def list_sessions(self) -> list[SessionInfo]:
        """List sessions via GET /api/sessions."""
        resp = await self._client.get(f"{self._base_url}/api/sessions")
        resp.raise_for_status()
        sessions = []
        for s in resp.json():
            sessions.append(SessionInfo(
                id=s["id"],
                profile=s.get("profile", ""),
                region=s.get("region", ""),
                status=s.get("status", "active"),
                created_at=s.get("created_at", ""),
            ))
        return sessions

    async def send_message(self, session_id: str, content: str) -> AsyncIterator[dict[str, Any]]:
        """
        Send a message via POST /api/sessions/{id}/messages/stream
        and yield parsed SSE event dicts.
        """
        url = f"{self._base_url}/api/sessions/{session_id}/messages/stream"

        async with self._client.stream(
            "POST",
            url,
            json={"content": content},
            timeout=300.0,
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise ConnectionError(
                    f"Server returned {response.status_code}: {body.decode()}"
                )

            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk

                # Parse SSE messages from buffer
                while "\n\n" in buffer:
                    msg, buffer = buffer.split("\n\n", 1)

                    # Extract data lines
                    data_line = None
                    for line in msg.strip().split("\n"):
                        if line.startswith("data: "):
                            data_line = line[6:]

                    if not data_line:
                        continue

                    try:
                        data = json.loads(data_line)
                    except json.JSONDecodeError:
                        continue

                    yield data

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


# ── Part 4 placeholder ──────────────────────────────────────────

class AgentCoreTransport(Transport):
    """
    AgentCore transport — Part 4 implementation.

    Will use boto3 to call InvokeAgentRuntime with SigV4 auth.
    The operator's ~/.aws/credentials provide the identity.
    AgentCore validates permissions at the platform level before
    forwarding to the container.

    Key unknowns to resolve in Part 4:
        1. Does InvokeAgentRuntime pass through our SSE stream
           verbatim, wrap it in an envelope, or buffer it?
        2. How does session lifecycle map to AgentCore's model?
        3. Does list_sessions() have an AgentCore equivalent?
    """

    def __init__(self, runtime_id: str, region: str = "us-east-1"):
        self._runtime_id = runtime_id
        self._region = region
        # boto3 client will be created here in Part 4

    async def health_check(self) -> bool:
        raise NotImplementedError("AgentCoreTransport is a Part 4 deliverable")

    async def create_session(self, profile: str = "", region: str = "") -> SessionInfo:
        raise NotImplementedError("AgentCoreTransport is a Part 4 deliverable")

    async def list_sessions(self) -> list[SessionInfo]:
        raise NotImplementedError("AgentCoreTransport is a Part 4 deliverable")

    async def send_message(self, session_id: str, content: str) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError("AgentCoreTransport is a Part 4 deliverable")
        # This yield is never reached but makes Python recognise this as an async generator
        yield  # type: ignore  # pragma: no cover

    async def close(self) -> None:
        pass
