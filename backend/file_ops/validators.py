"""
Schema validation for AWS Coworker resource files.

Each resource type (command, skill, agent, config) has required and optional
fields in its YAML frontmatter. This module validates parsed MarkdownFile
objects against these schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .markdown import MarkdownFile


@dataclass
class ValidationResult:
    """Result of validating a resource file."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_command(md: MarkdownFile) -> ValidationResult:
    """Validate a command file's frontmatter and structure."""
    errors = []
    warnings = []

    meta = md.metadata

    # Required fields
    if not meta.get("description"):
        errors.append("Missing required field: description")

    # Agent field — required, must be a string
    agent = meta.get("agent")
    if not agent:
        errors.append("Missing required field: agent")
    elif not isinstance(agent, str):
        errors.append("Field 'agent' must be a string")

    # Tools field — required, must be a list
    tools = meta.get("tools")
    if not tools:
        errors.append("Missing required field: tools")
    elif not isinstance(tools, list):
        errors.append("Field 'tools' must be a list")

    # Skills field — optional but should be a list if present
    skills = meta.get("skills")
    if skills is not None and not isinstance(skills, list):
        warnings.append("Field 'skills' should be a list")

    # Arguments field — optional but should be a list of dicts if present
    arguments = meta.get("arguments")
    if arguments is not None:
        if not isinstance(arguments, list):
            warnings.append("Field 'arguments' should be a list")
        else:
            for i, arg in enumerate(arguments):
                if not isinstance(arg, dict):
                    warnings.append(f"Argument {i} should be a dict")
                elif not arg.get("name"):
                    warnings.append(f"Argument {i} missing 'name'")

    # Body should not be empty
    if not md.body.strip():
        warnings.append("Command body is empty — should contain workflow instructions")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_skill(md: MarkdownFile) -> ValidationResult:
    """Validate a skill file's frontmatter and structure."""
    errors = []
    warnings = []

    meta = md.metadata

    # Required fields
    if not meta.get("name"):
        errors.append("Missing required field: name")

    if not meta.get("category"):
        errors.append("Missing required field: category")
    elif meta["category"] not in ("aws", "org", "core", "meta"):
        warnings.append(
            f"Unexpected category '{meta['category']}' — expected one of: aws, org, core, meta"
        )

    # Optional but recommended
    if not meta.get("description"):
        warnings.append("Missing recommended field: description")

    if not meta.get("version"):
        warnings.append("Missing recommended field: version")

    # Agents field — optional, should be list
    agents = meta.get("agents")
    if agents is not None and not isinstance(agents, list):
        warnings.append("Field 'agents' should be a list")

    # Body should contain meaningful content
    if not md.body.strip():
        warnings.append("Skill body is empty — should contain guidance content")
    elif len(md.body.strip()) < 100:
        warnings.append("Skill body seems very short — skills typically contain detailed guidance")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_agent(md: MarkdownFile) -> ValidationResult:
    """Validate an agent definition file."""
    errors = []
    warnings = []

    body = md.body.strip()

    # Agent files may not have frontmatter — that's okay
    # But the body must contain an Identity section
    if not body:
        errors.append("Agent body is empty — must contain agent definition")
    else:
        body_lower = body.lower()
        if "## identity" not in body_lower and "# identity" not in body_lower:
            warnings.append("Missing '## Identity' section — agent definitions should have one")

        if "## purpose" not in body_lower and "# purpose" not in body_lower:
            warnings.append("Missing '## Purpose' section — agent definitions should have one")

        if "allowed tools" not in body_lower and "## tools" not in body_lower:
            warnings.append("Missing tools section — agent definitions should specify allowed tools")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_config(md: MarkdownFile) -> ValidationResult:
    """Validate a configuration file."""
    errors = []
    warnings = []

    if not md.body.strip() and not md.metadata:
        errors.append("Config file is empty")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# Validator registry
VALIDATORS = {
    "commands": validate_command,
    "skills": validate_skill,
    "agents": validate_agent,
    "config": validate_config,
}


def validate(category: str, md: MarkdownFile) -> ValidationResult:
    """Validate a resource file based on its category."""
    validator = VALIDATORS.get(category)
    if validator is None:
        return ValidationResult(valid=True, warnings=[f"No validator for category: {category}"])
    return validator(md)
