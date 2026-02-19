"""
Permission request/grant handler.

Manages the async flow when the SDK session needs user approval:
1. SDK triggers can_use_tool callback for a mutation
2. Server creates a pending permission request
3. SSE emits permission_request event to client
4. Client shows approval UI (or auto-approves via API)
5. User approves/denies via REST endpoint
6. Server resolves the pending request
7. SDK session resumes
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class PendingPermission:
    """A permission request awaiting user response."""
    id: str
    session_id: str
    action: str
    description: str
    blast_radius: str
    created: datetime
    future: asyncio.Future  # Resolved when user responds

    def to_event_data(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "description": self.description,
            "blastRadius": self.blast_radius,
            "awaitingResponse": True,
        }


class PermissionHandler:
    """Manages pending permission requests across sessions."""

    def __init__(self) -> None:
        self._pending: dict[str, PendingPermission] = {}

    async def request_permission(
        self,
        session_id: str,
        action: str,
        description: str,
        blast_radius: str = "",
    ) -> bool:
        """
        Create a permission request and wait for user response.

        This is called from the SDK's can_use_tool callback.
        It blocks (awaits) until the user responds via the REST endpoint.

        Returns True if approved, False if denied.
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        permission = PendingPermission(
            id=f"perm-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            action=action,
            description=description,
            blast_radius=blast_radius,
            created=datetime.now(),
            future=future,
        )

        self._pending[permission.id] = permission

        try:
            # Wait for user response (with timeout)
            approved = await asyncio.wait_for(future, timeout=300)  # 5 min timeout
            return approved
        except asyncio.TimeoutError:
            return False  # Deny on timeout
        finally:
            self._pending.pop(permission.id, None)

    def grant(self, permission_id: str, approved: bool) -> bool:
        """
        Resolve a pending permission request.

        Called from the REST endpoint when the user clicks approve/deny.
        Returns True if the permission was found and resolved.
        """
        permission = self._pending.get(permission_id)
        if permission is None:
            return False

        if not permission.future.done():
            permission.future.set_result(approved)
        return True

    def get_pending(self, session_id: str) -> list[PendingPermission]:
        """Get all pending permissions for a session."""
        return [
            p for p in self._pending.values()
            if p.session_id == session_id
        ]

    def get_pending_by_id(self, permission_id: str) -> PendingPermission | None:
        """Get a specific pending permission."""
        return self._pending.get(permission_id)

    def cancel_all(self, session_id: str) -> int:
        """Cancel all pending permissions for a session. Returns count cancelled."""
        to_cancel = [
            pid for pid, p in self._pending.items()
            if p.session_id == session_id
        ]
        for pid in to_cancel:
            p = self._pending.pop(pid)
            if not p.future.done():
                p.future.set_result(False)
        return len(to_cancel)
