"""
Resource management endpoints — CRUD for Commands, Skills, Agents, Config.

All resources are markdown files on disk. The API parses YAML frontmatter,
validates against schemas, and reads/writes through SafeFileManager.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .schemas import (
    AgentSummary,
    CommandSummary,
    ConfigSection,
    ResourceCreate,
    ResourceDetail,
    ResourceUpdate,
    SkillTreeNode,
    ValidationResponse,
)
from ..file_ops.markdown import MarkdownFile
from ..file_ops import safe_manager as sfm
from ..file_ops.validators import validate

router = APIRouter(prefix="/api")


def _get_file_manager():
    """Get the SafeFileManager from app state."""
    from ..main import app_state
    return app_state["file_manager"]


# ============================================================
# Commands
# ============================================================

@router.get("/commands", response_model=list[CommandSummary])
async def list_commands() -> list[CommandSummary]:
    """List all commands with parsed YAML frontmatter."""
    fm = _get_file_manager()
    files = fm.list_files("commands")
    commands = []
    for f in files:
        try:
            md = fm.read("commands", f["name"])
            meta = md.metadata
            commands.append(CommandSummary(
                name=f["name"],
                description=meta.get("description", ""),
                agent=meta.get("agent", ""),
                skills=meta.get("skills", []) or [],
                tools=meta.get("tools", []) or [],
                arguments=meta.get("arguments", []) or [],
            ))
        except Exception:
            # Skip files that can't be parsed
            commands.append(CommandSummary(
                name=f["name"],
                description="(parse error)",
                agent="",
            ))
    return commands


@router.get("/commands/{name}", response_model=ResourceDetail)
async def get_command(name: str) -> ResourceDetail:
    """Get a single command with full markdown content."""
    fm = _get_file_manager()
    try:
        md = fm.read("commands", name)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command not found: {name}")

    return ResourceDetail(
        id=name,
        name=name,
        category="commands",
        metadata=md.metadata,
        content=md.body,
    )


@router.patch("/commands/{name}", response_model=ResourceDetail)
async def update_command(name: str, request: ResourceUpdate) -> ResourceDetail:
    """Update a command (metadata and/or body)."""
    fm = _get_file_manager()
    try:
        md = fm.read("commands", name)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command not found: {name}")

    md.update(metadata=request.metadata, body=request.content)
    fm.write("commands", name, md)

    return ResourceDetail(
        id=name,
        name=name,
        category="commands",
        metadata=md.metadata,
        content=md.body,
    )


@router.post("/commands", response_model=ResourceDetail, status_code=201)
async def create_command(request: ResourceCreate) -> ResourceDetail:
    """Create a new command."""
    fm = _get_file_manager()

    # Check if already exists
    try:
        fm.read("commands", request.id)
        raise HTTPException(status_code=409, detail=f"Command already exists: {request.id}")
    except sfm.FileNotFoundError:
        pass

    md = MarkdownFile(metadata=request.metadata, body=request.content)

    # Validate
    result = validate("commands", md)
    if not result.valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})

    fm.write("commands", request.id, md)

    return ResourceDetail(
        id=request.id,
        name=request.id,
        category="commands",
        metadata=md.metadata,
        content=md.body,
    )


@router.delete("/commands/{name}")
async def delete_command(name: str) -> dict[str, str]:
    """Delete a command."""
    fm = _get_file_manager()
    try:
        fm.delete("commands", name)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command not found: {name}")
    return {"status": "deleted", "id": name}


# ============================================================
# Skills
# ============================================================

@router.get("/skills")
async def list_skills() -> list[SkillTreeNode]:
    """List all skills as a hierarchical tree."""
    fm = _get_file_manager()
    tree_data = fm.list_tree("skills")

    def convert_tree(items: list[dict]) -> list[SkillTreeNode]:
        nodes = []
        for item in items:
            children = None
            if item.get("children"):
                children = convert_tree(item["children"])
            nodes.append(SkillTreeNode(
                name=item["name"],
                type=item["type"],
                path=item["path"],
                size=item.get("size"),
                modified=item.get("modified"),
                children=children,
            ))
        return nodes

    return convert_tree(tree_data)


@router.get("/skills/{skill_id:path}", response_model=ResourceDetail)
async def get_skill(skill_id: str) -> ResourceDetail:
    """Get a skill with parsed frontmatter + content. Supports nested paths."""
    fm = _get_file_manager()
    try:
        md = fm.read("skills", skill_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    except sfm.PathSecurityError:
        raise HTTPException(status_code=400, detail="Invalid skill path")

    return ResourceDetail(
        id=skill_id,
        name=skill_id.split("/")[-1],
        category="skills",
        metadata=md.metadata,
        content=md.body,
    )


@router.patch("/skills/{skill_id:path}", response_model=ResourceDetail)
async def update_skill(skill_id: str, request: ResourceUpdate) -> ResourceDetail:
    """Update a skill."""
    fm = _get_file_manager()
    try:
        md = fm.read("skills", skill_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    except sfm.PathSecurityError:
        raise HTTPException(status_code=400, detail="Invalid skill path")

    md.update(metadata=request.metadata, body=request.content)
    fm.write("skills", skill_id, md)

    return ResourceDetail(
        id=skill_id,
        name=skill_id.split("/")[-1],
        category="skills",
        metadata=md.metadata,
        content=md.body,
    )


@router.post("/skills", response_model=ResourceDetail, status_code=201)
async def create_skill(request: ResourceCreate) -> ResourceDetail:
    """Create a new skill."""
    fm = _get_file_manager()

    try:
        fm.read("skills", request.id)
        raise HTTPException(status_code=409, detail=f"Skill already exists: {request.id}")
    except sfm.FileNotFoundError:
        pass

    md = MarkdownFile(metadata=request.metadata, body=request.content)
    result = validate("skills", md)
    if not result.valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})

    fm.write("skills", request.id, md)

    return ResourceDetail(
        id=request.id,
        name=request.id.split("/")[-1],
        category="skills",
        metadata=md.metadata,
        content=md.body,
    )


@router.delete("/skills/{skill_id:path}")
async def delete_skill(skill_id: str) -> dict[str, str]:
    """Delete a skill."""
    fm = _get_file_manager()
    try:
        fm.delete("skills", skill_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {"status": "deleted", "id": skill_id}


# ============================================================
# Agents
# ============================================================

@router.get("/agents", response_model=list[AgentSummary])
async def list_agents() -> list[AgentSummary]:
    """List all agent definitions."""
    fm = _get_file_manager()
    files = fm.list_files("agents")
    agents = []
    for f in files:
        try:
            md = fm.read("agents", f["name"])
            # Extract first line after # heading as summary
            agents.append(AgentSummary(
                id=f["name"],
                name=f["name"],
                content=md.body[:200] + "..." if len(md.body) > 200 else md.body,
            ))
        except Exception:
            agents.append(AgentSummary(
                id=f["name"],
                name=f["name"],
                content="(parse error)",
            ))
    return agents


@router.get("/agents/{agent_id}", response_model=ResourceDetail)
async def get_agent(agent_id: str) -> ResourceDetail:
    """Get an agent with full content."""
    fm = _get_file_manager()
    try:
        md = fm.read("agents", agent_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return ResourceDetail(
        id=agent_id,
        name=agent_id,
        category="agents",
        metadata=md.metadata,
        content=md.body,
    )


@router.patch("/agents/{agent_id}", response_model=ResourceDetail)
async def update_agent(agent_id: str, request: ResourceUpdate) -> ResourceDetail:
    """Update an agent definition."""
    fm = _get_file_manager()
    try:
        md = fm.read("agents", agent_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    md.update(metadata=request.metadata, body=request.content)
    fm.write("agents", agent_id, md)

    return ResourceDetail(
        id=agent_id,
        name=agent_id,
        category="agents",
        metadata=md.metadata,
        content=md.body,
    )


@router.post("/agents", response_model=ResourceDetail, status_code=201)
async def create_agent(request: ResourceCreate) -> ResourceDetail:
    """Create a new agent definition."""
    fm = _get_file_manager()

    try:
        fm.read("agents", request.id)
        raise HTTPException(status_code=409, detail=f"Agent already exists: {request.id}")
    except sfm.FileNotFoundError:
        pass

    md = MarkdownFile(metadata=request.metadata, body=request.content)
    result = validate("agents", md)
    if not result.valid:
        raise HTTPException(status_code=422, detail={"errors": result.errors})

    fm.write("agents", request.id, md)

    return ResourceDetail(
        id=request.id,
        name=request.id,
        category="agents",
        metadata=md.metadata,
        content=md.body,
    )


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str) -> dict[str, str]:
    """Delete an agent."""
    fm = _get_file_manager()
    try:
        fm.delete("agents", agent_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"status": "deleted", "id": agent_id}


# ============================================================
# Config
# ============================================================

@router.get("/config")
async def list_config() -> list[ConfigSection]:
    """Get all config sections."""
    fm = _get_file_manager()

    sections = []
    # Main config files
    for f in fm.list_files("config"):
        try:
            md = fm.read("config", f["name"])
            sections.append(ConfigSection(
                section=f["name"],
                metadata=md.metadata,
                content=md.body,
            ))
        except Exception:
            sections.append(ConfigSection(section=f["name"]))

    # Claude config (orchestration-config.md etc.)
    for f in fm.list_files("claude_config"):
        try:
            md = fm.read("claude_config", f["name"])
            sections.append(ConfigSection(
                section=f"claude/{f['name']}",
                metadata=md.metadata,
                content=md.body,
            ))
        except Exception:
            sections.append(ConfigSection(section=f"claude/{f['name']}"))

    return sections


@router.get("/config/{section:path}", response_model=ConfigSection)
async def get_config(section: str) -> ConfigSection:
    """Get a specific config section."""
    fm = _get_file_manager()

    # Route claude/ prefixed sections to claude_config
    category = "config"
    file_id = section
    if section.startswith("claude/"):
        category = "claude_config"
        file_id = section[7:]  # strip "claude/"

    try:
        md = fm.read(category, file_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Config not found: {section}")

    return ConfigSection(
        section=section,
        metadata=md.metadata,
        content=md.body,
    )


@router.patch("/config/{section:path}", response_model=ConfigSection)
async def update_config(section: str, request: ResourceUpdate) -> ConfigSection:
    """Update a config section."""
    fm = _get_file_manager()

    category = "config"
    file_id = section
    if section.startswith("claude/"):
        category = "claude_config"
        file_id = section[7:]

    try:
        md = fm.read(category, file_id)
    except sfm.FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Config not found: {section}")

    md.update(metadata=request.metadata, body=request.content)
    fm.write(category, file_id, md)

    return ConfigSection(
        section=section,
        metadata=md.metadata,
        content=md.body,
    )
