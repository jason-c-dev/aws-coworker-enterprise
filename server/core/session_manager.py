"""
Session lifecycle management.

Manages the mapping between session IDs and ClaudeSDKClient instances,
workspace directories, metadata, and artifact storage.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..api.schemas import (
    ArtifactSummary,
    SessionCreate,
    SessionDeleteResult,
    SessionDetail,
    SessionMetadata,
    SessionStatus,
    SessionSummary,
    SessionUpdate,
)
from .artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session lifecycle: create, get, update, delete.

    Each session has:
    - A workspace directory under WORKSPACE_BASE/{session_id}/
    - A session.json metadata file
    - A history.jsonl conversation log
    - An artifacts/ subdirectory
    - (When SDK is connected) A live ClaudeSDKClient instance
    """

    def __init__(self, workspace_base: Path, max_sessions: int = 10) -> None:
        self._workspace_base = workspace_base
        self._workspace_base.mkdir(parents=True, exist_ok=True)
        self._max_sessions = max_sessions
        # In-memory cache of session metadata
        self._sessions: dict[str, SessionMetadata] = {}
        # Artifact managers per session
        self._artifact_managers: dict[str, ArtifactManager] = {}
        # SDK clients will be stored here when SDK integration is built
        self._sdk_clients: dict[str, Any] = {}
        # Load existing sessions from disk
        self._load_existing_sessions()

    def _load_existing_sessions(self) -> None:
        """Load session metadata from existing workspace directories."""
        if not self._workspace_base.exists():
            return
        for session_dir in self._workspace_base.iterdir():
            if session_dir.is_dir():
                meta_path = session_dir / "session.json"
                if meta_path.exists():
                    try:
                        data = json.loads(meta_path.read_text(encoding="utf-8"))
                        meta = SessionMetadata(**data)
                        # Restored sessions start as idle
                        meta.status = SessionStatus.IDLE
                        self._sessions[meta.id] = meta
                        self._artifact_managers[meta.id] = ArtifactManager(session_dir)
                        logger.info(f"Restored session: {meta.id} ({meta.name})")
                    except Exception as e:
                        logger.warning(f"Failed to restore session from {session_dir}: {e}")

    def _workspace_path(self, session_id: str) -> Path:
        return self._workspace_base / session_id

    def _save_metadata(self, session_id: str) -> None:
        """Persist session metadata to disk."""
        meta = self._sessions.get(session_id)
        if meta is None:
            return
        path = self._workspace_path(session_id) / "session.json"
        path.write_text(
            json.dumps(meta.model_dump(), default=str, indent=2),
            encoding="utf-8",
        )

    def create(self, request: SessionCreate) -> SessionMetadata:
        """Create a new session with workspace directory."""
        meta = SessionMetadata(
            name=request.name or "New Session",
            profile=request.profile or "",
            region=request.region or "",
        )

        # Create workspace directory
        workspace = self._workspace_path(meta.id)
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "artifacts").mkdir(exist_ok=True)

        # Initialize empty history
        (workspace / "history.jsonl").touch()

        # Save metadata
        self._sessions[meta.id] = meta
        self._save_metadata(meta.id)

        # Create artifact manager
        self._artifact_managers[meta.id] = ArtifactManager(workspace)

        logger.info(f"Created session: {meta.id} ({meta.name})")
        return meta

    def get(self, session_id: str) -> SessionMetadata | None:
        """Get session metadata."""
        return self._sessions.get(session_id)

    def get_detail(self, session_id: str) -> SessionDetail | None:
        """Get full session details including artifact list."""
        meta = self._sessions.get(session_id)
        if meta is None:
            return None

        artifacts = self.get_artifact_manager(session_id)
        artifact_list = artifacts.list() if artifacts else []

        return SessionDetail(
            **meta.model_dump(),
            artifacts=artifact_list,
        )

    def list(self) -> list[SessionSummary]:
        """List all sessions as summaries."""
        summaries = []
        for meta in self._sessions.values():
            # Update artifact count
            am = self._artifact_managers.get(meta.id)
            if am:
                meta.artifactCount = am.count

            summaries.append(SessionSummary(
                id=meta.id,
                name=meta.name,
                description=meta.description,
                status=meta.status,
                profile=meta.profile,
                region=meta.region,
                created=meta.created,
                lastActivity=meta.lastActivity,
                artifactCount=meta.artifactCount,
            ))

        # Sort by last activity, most recent first
        summaries.sort(key=lambda s: s.lastActivity, reverse=True)
        return summaries

    def update(self, session_id: str, request: SessionUpdate) -> SessionMetadata | None:
        """Update session metadata (rename, update description)."""
        meta = self._sessions.get(session_id)
        if meta is None:
            return None

        if request.name is not None:
            meta.name = request.name
        if request.description is not None:
            meta.description = request.description
        if request.environment is not None:
            meta.environment = request.environment

        self._save_metadata(session_id)
        logger.info(f"Updated session: {session_id} → name='{meta.name}'")
        return meta

    def update_activity(self, session_id: str) -> None:
        """Touch the lastActivity timestamp."""
        meta = self._sessions.get(session_id)
        if meta:
            meta.lastActivity = datetime.now()
            meta.status = SessionStatus.ACTIVE
            self._save_metadata(session_id)

    def update_name_suggestion(self, session_id: str, name: str, description: str = "") -> None:
        """Update session name from model suggestion."""
        meta = self._sessions.get(session_id)
        if meta and meta.name == "New Session":
            # Only auto-update if user hasn't manually named it
            meta.name = name
            if description:
                meta.description = description
            self._save_metadata(session_id)
            logger.info(f"Auto-named session {session_id}: '{name}'")

    def delete(self, session_id: str) -> SessionDeleteResult | None:
        """Delete a session — cascading delete of workspace, artifacts, history."""
        meta = self._sessions.get(session_id)
        if meta is None:
            return None

        # Count artifacts before deletion
        am = self._artifact_managers.get(session_id)
        artifact_count = am.count if am else 0

        # Close SDK client if active
        client = self._sdk_clients.pop(session_id, None)
        # TODO: close client when SDK integration is built

        # Remove from caches
        self._sessions.pop(session_id, None)
        self._artifact_managers.pop(session_id, None)

        # Delete workspace directory entirely
        workspace = self._workspace_path(session_id)
        if workspace.exists():
            shutil.rmtree(workspace)

        logger.info(f"Deleted session: {session_id} ({artifact_count} artifacts)")
        return SessionDeleteResult(
            id=session_id,
            artifactsDeleted=artifact_count,
        )

    def get_artifact_manager(self, session_id: str) -> ArtifactManager | None:
        """Get the artifact manager for a session."""
        return self._artifact_managers.get(session_id)

    def append_history(self, session_id: str, entry: dict[str, Any]) -> None:
        """Append an entry to the session's conversation history."""
        workspace = self._workspace_path(session_id)
        history_path = workspace / "history.jsonl"
        if history_path.exists():
            with open(history_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Read the session's conversation history."""
        workspace = self._workspace_path(session_id)
        history_path = workspace / "history.jsonl"
        if not history_path.exists():
            return []

        entries = []
        for line in history_path.read_text(encoding="utf-8").strip().split("\n"):
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries
