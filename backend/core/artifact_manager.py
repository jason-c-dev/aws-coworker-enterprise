"""
Artifact manager — file storage per session.

Handles CRUD for session artifacts, type detection, and cascading deletes.
Artifacts are any files produced during or uploaded to a session.
"""

from __future__ import annotations

import mimetypes
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from ..api.schemas import ArtifactSource, ArtifactSummary, ArtifactDetail


class ArtifactManager:
    """Manages artifacts within a session's workspace directory."""

    def __init__(self, workspace_path: Path) -> None:
        self._workspace = workspace_path
        self._artifacts_dir = workspace_path / "artifacts"
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ArtifactSummary]:
        """List all artifacts in this session."""
        artifacts = []
        for path in sorted(self._artifacts_dir.iterdir()):
            if path.is_file() and not path.name.startswith("."):
                stat = path.stat()
                mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                # Read source from sidecar metadata if available
                source = self._read_source(path)
                artifacts.append(ArtifactSummary(
                    id=path.stem,
                    name=path.name,
                    type=mime_type,
                    size=stat.st_size,
                    source=source,
                    created=datetime.fromtimestamp(stat.st_ctime),
                ))
        return artifacts

    def get(self, artifact_id: str, session_id: str) -> ArtifactDetail | None:
        """Get artifact details by ID."""
        path = self._find_artifact(artifact_id)
        if path is None:
            return None

        stat = path.stat()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        source = self._read_source(path)

        return ArtifactDetail(
            id=path.stem,
            name=path.name,
            type=mime_type,
            size=stat.st_size,
            source=source,
            created=datetime.fromtimestamp(stat.st_ctime),
            sessionId=session_id,
            path=str(path.relative_to(self._workspace)),
        )

    def get_path(self, artifact_id: str) -> Path | None:
        """Get the file path for an artifact (for download)."""
        return self._find_artifact(artifact_id)

    def create(
        self,
        filename: str,
        content: bytes | str,
        source: ArtifactSource = ArtifactSource.USER_UPLOADED,
    ) -> ArtifactSummary:
        """Create a new artifact from content."""
        # Sanitize filename
        safe_name = self._sanitize_filename(filename)
        path = self._artifacts_dir / safe_name

        # Handle name collisions
        if path.exists():
            stem = path.stem
            suffix = path.suffix
            counter = 1
            while path.exists():
                path = self._artifacts_dir / f"{stem}-{counter}{suffix}"
                counter += 1

        # Write content
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_bytes(content)

        # Write source metadata sidecar
        self._write_source(path, source)

        stat = path.stat()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        return ArtifactSummary(
            id=path.stem,
            name=path.name,
            type=mime_type,
            size=stat.st_size,
            source=source,
            created=datetime.fromtimestamp(stat.st_ctime),
        )

    def create_from_upload(self, filename: str, file: BinaryIO) -> ArtifactSummary:
        """Create an artifact from an uploaded file."""
        content = file.read()
        return self.create(filename, content, ArtifactSource.USER_UPLOADED)

    def delete(self, artifact_id: str) -> bool:
        """Delete an artifact. Returns True if found and deleted."""
        path = self._find_artifact(artifact_id)
        if path is None:
            return False

        path.unlink()
        # Also remove sidecar metadata
        meta_path = path.with_suffix(path.suffix + ".meta")
        if meta_path.exists():
            meta_path.unlink()
        return True

    def delete_all(self) -> int:
        """Delete all artifacts. Returns count of deleted files."""
        count = 0
        for path in self._artifacts_dir.iterdir():
            if path.is_file():
                path.unlink()
                count += 1
        return count

    @property
    def count(self) -> int:
        """Count of artifacts (excluding metadata sidecars)."""
        return sum(
            1 for p in self._artifacts_dir.iterdir()
            if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".meta")
        )

    def _find_artifact(self, artifact_id: str) -> Path | None:
        """Find an artifact by ID (stem name). Returns first match."""
        for path in self._artifacts_dir.iterdir():
            if path.is_file() and path.stem == artifact_id and not path.name.endswith(".meta"):
                return path
        return None

    def _sanitize_filename(self, filename: str) -> str:
        """Remove dangerous characters from filename."""
        # Remove path separators and null bytes
        safe = filename.replace("/", "_").replace("\\", "_").replace("\0", "")
        # Remove leading dots (hidden files)
        safe = safe.lstrip(".")
        # Limit length
        if len(safe) > 255:
            safe = safe[:255]
        return safe or "unnamed"

    def _write_source(self, path: Path, source: ArtifactSource) -> None:
        """Write source metadata as a sidecar file."""
        meta_path = path.with_suffix(path.suffix + ".meta")
        meta_path.write_text(source.value, encoding="utf-8")

    def _read_source(self, path: Path) -> ArtifactSource:
        """Read source metadata from sidecar file."""
        meta_path = path.with_suffix(path.suffix + ".meta")
        if meta_path.exists():
            value = meta_path.read_text(encoding="utf-8").strip()
            try:
                return ArtifactSource(value)
            except ValueError:
                pass
        return ArtifactSource.USER_UPLOADED  # default
