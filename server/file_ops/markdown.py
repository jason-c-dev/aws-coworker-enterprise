"""
Markdown file parser with YAML frontmatter support.

Handles the format used by all AWS Coworker commands, skills, and agents:
    ---
    key: value
    list:
      - item1
      - item2
    ---

    # Markdown Body
    Content here...
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MarkdownFile:
    """Represents a parsed markdown file with optional YAML frontmatter."""

    metadata: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    file_path: str | None = None
    is_dirty: bool = False
    last_saved: datetime | None = None

    @classmethod
    def parse(cls, content: str, file_path: str | None = None) -> "MarkdownFile":
        """Parse a markdown file with optional YAML frontmatter."""
        metadata = {}
        body = content

        stripped = content.strip()
        if stripped.startswith("---"):
            # Find the closing --- delimiter
            # Skip the first --- and find the next one
            rest = stripped[3:]
            end_idx = rest.find("\n---")
            if end_idx != -1:
                yaml_str = rest[:end_idx]
                # Body starts after the closing ---\n
                after_close = rest[end_idx + 4:]  # skip \n---
                # Skip leading newlines after frontmatter
                body = after_close.lstrip("\n")

                try:
                    parsed = yaml.safe_load(yaml_str)
                    if isinstance(parsed, dict):
                        metadata = parsed
                except yaml.YAMLError:
                    # If YAML parsing fails, treat entire content as body
                    body = content

        return cls(
            metadata=metadata,
            body=body,
            file_path=file_path,
            last_saved=datetime.now(),
        )

    def to_string(self) -> str:
        """Serialize back to markdown with YAML frontmatter."""
        if not self.metadata:
            return self.body

        yaml_str = yaml.dump(
            self.metadata,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        return f"---\n{yaml_str}---\n\n{self.body}"

    def update(self, metadata: dict[str, Any] | None = None, body: str | None = None) -> None:
        """Update metadata and/or body, marking the file as dirty."""
        if metadata is not None:
            self.metadata = metadata
        if body is not None:
            self.body = body
        self.is_dirty = True
