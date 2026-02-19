"""
Safe file manager with path traversal protection.

All file reads and writes for resource management (commands, skills, agents, config)
go through this class. It resolves file IDs to absolute paths within allowed base
directories and prevents directory traversal attacks.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .markdown import MarkdownFile


class PathSecurityError(Exception):
    """Raised when a file path escapes its allowed base directory."""
    pass


class FileNotFoundError(Exception):
    """Raised when a requested file does not exist."""
    pass


class SafeFileManager:
    """
    Path-safe file I/O for AWS Coworker resource files.

    Each resource category has a base directory. File IDs are resolved
    relative to these bases, with traversal protection.
    """

    def __init__(self, base_paths: dict[str, Path]) -> None:
        """
        Args:
            base_paths: Mapping of category name to base directory path.
                        e.g., {"commands": Path("/repo/.claude/commands"), ...}
        """
        self._base_paths = {
            k: v.resolve() for k, v in base_paths.items()
        }

    def _resolve_path(self, category: str, file_id: str, must_exist: bool = True) -> Path:
        """
        Safely resolve a file ID to an absolute path within a category's base directory.

        Args:
            category: Resource category (commands, skills, agents, config)
            file_id: File identifier, may contain forward slashes for nested paths.
                     Extension .md is appended if not present.
            must_exist: If True, raises FileNotFoundError when file doesn't exist.

        Returns:
            Resolved absolute Path.

        Raises:
            PathSecurityError: If the resolved path escapes the base directory.
            FileNotFoundError: If must_exist is True and the file doesn't exist.
            ValueError: If the category is unknown.
        """
        base = self._base_paths.get(category)
        if base is None:
            raise ValueError(f"Unknown resource category: {category}")

        # Normalize: remove leading/trailing slashes, reject suspicious patterns
        clean_id = file_id.strip("/")
        if ".." in clean_id or clean_id.startswith("/"):
            raise PathSecurityError(f"Path traversal attempt detected: {file_id}")

        # Append .md extension if not present
        if not clean_id.endswith(".md"):
            clean_id += ".md"

        # Resolve full path
        full_path = (base / clean_id).resolve()

        # Verify it stays within the base directory
        try:
            full_path.relative_to(base)
        except ValueError:
            raise PathSecurityError(
                f"Path '{file_id}' resolves outside base directory for category '{category}'"
            )

        if must_exist and not full_path.exists():
            raise FileNotFoundError(f"File not found: {category}/{file_id}")

        return full_path

    def read(self, category: str, file_id: str) -> MarkdownFile:
        """Read and parse a markdown file from a resource category."""
        path = self._resolve_path(category, file_id)
        content = path.read_text(encoding="utf-8")
        return MarkdownFile.parse(content, file_path=str(path))

    def read_raw(self, category: str, file_path_str: str) -> str:
        """Read a raw file (non-markdown, e.g. YAML) from a resource category.

        Unlike read(), this does not parse frontmatter. Returns raw text content.
        file_path_str should be the relative path including extension.
        """
        base = self._base_paths.get(category)
        if base is None:
            raise ValueError(f"Unknown resource category: {category}")

        clean_path = file_path_str.strip("/")
        if ".." in clean_path or clean_path.startswith("/"):
            raise PathSecurityError(f"Path traversal attempt detected: {file_path_str}")

        full_path = (base / clean_path).resolve()

        try:
            full_path.relative_to(base)
        except ValueError:
            raise PathSecurityError(
                f"Path '{file_path_str}' resolves outside base directory for category '{category}'"
            )

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {category}/{file_path_str}")

        return full_path.read_text(encoding="utf-8")

    def write(self, category: str, file_id: str, markdown: MarkdownFile) -> Path:
        """Write a markdown file to a resource category."""
        path = self._resolve_path(category, file_id, must_exist=False)

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(markdown.to_string(), encoding="utf-8")
        markdown.file_path = str(path)
        markdown.is_dirty = False
        return path

    def delete(self, category: str, file_id: str) -> Path:
        """Delete a file from a resource category."""
        path = self._resolve_path(category, file_id)
        path.unlink()
        return path

    def list_files(self, category: str, pattern: str = "*.md") -> list[dict[str, Any]]:
        """
        List all files in a resource category.

        Returns list of dicts with: name, path (relative to base), size, modified.
        """
        base = self._base_paths.get(category)
        if base is None:
            raise ValueError(f"Unknown resource category: {category}")

        if not base.exists():
            return []

        files = []
        for path in sorted(base.rglob(pattern)):
            if path.is_file():
                rel_path = path.relative_to(base)
                stat = path.stat()
                files.append({
                    "name": path.stem,
                    "path": str(rel_path),
                    "fullPath": str(path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
        return files

    def list_tree(self, category: str) -> list[dict[str, Any]]:
        """
        List files as a hierarchical tree structure.
        Used primarily for the skills browser which has nested directories.

        Returns a nested list of dicts with: name, type (file/directory), children, path.
        """
        base = self._base_paths.get(category)
        if base is None:
            raise ValueError(f"Unknown resource category: {category}")

        if not base.exists():
            return []

        return self._build_tree(base, base)

    def _build_tree(self, directory: Path, base: Path) -> list[dict[str, Any]]:
        """Recursively build a tree structure from a directory."""
        items = []
        for entry in sorted(directory.iterdir()):
            rel_path = entry.relative_to(base)
            if entry.is_dir():
                children = self._build_tree(entry, base)
                if children:  # Only include non-empty directories
                    items.append({
                        "name": entry.name,
                        "type": "directory",
                        "path": str(rel_path),
                        "children": children,
                    })
            elif entry.is_file() and entry.suffix == ".md":
                stat = entry.stat()
                items.append({
                    "name": entry.stem,
                    "type": "file",
                    "path": str(rel_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
        return items
