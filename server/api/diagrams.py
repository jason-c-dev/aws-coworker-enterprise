"""
Diagram generation endpoints.

Supports three engines:
  - Mermaid: Returns mermaid syntax for client-side rendering
  - Python diagrams: Generates PNG/SVG using the `diagrams` library
  - React Flow: Returns node/edge JSON for interactive rendering
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from .schemas import DiagramRequest, DiagramResponse

router = APIRouter(prefix="/api")


def _get_state():
    from ..main import app_state
    return app_state


# ── Mermaid helpers ─────────────────────────────────────────────

def _generate_architecture_mermaid(resources: dict[str, Any]) -> str:
    """Generate a Mermaid architecture diagram from discovered resources."""
    lines = ["graph TB"]

    # VPCs
    vpcs = resources.get("vpcs", [])
    for i, vpc in enumerate(vpcs):
        vid = f"vpc{i}"
        name = vpc.get("name", vpc.get("id", f"VPC-{i}"))
        lines.append(f'    {vid}["{name}"]')

    # EC2 instances
    instances = resources.get("instances", [])
    for i, inst in enumerate(instances):
        iid = f"ec2_{i}"
        name = inst.get("name", inst.get("id", f"EC2-{i}"))
        lines.append(f'    {iid}["{name}"]')
        vpc_idx = inst.get("vpc_index", 0)
        if vpc_idx < len(vpcs):
            lines.append(f"    vpc{vpc_idx} --> {iid}")

    # S3 buckets
    buckets = resources.get("buckets", [])
    for i, bucket in enumerate(buckets):
        bid = f"s3_{i}"
        name = bucket.get("name", f"S3-{i}")
        lines.append(f'    {bid}[("{name}")]')

    # Lambda functions
    functions = resources.get("functions", [])
    for i, fn in enumerate(functions):
        fid = f"lambda_{i}"
        name = fn.get("name", f"Lambda-{i}")
        lines.append(f'    {fid}{{{{"{name}"}}}}')

    # RDS databases
    databases = resources.get("databases", [])
    for i, db in enumerate(databases):
        did = f"rds_{i}"
        name = db.get("name", f"RDS-{i}")
        lines.append(f'    {did}[("{name}")]')
        vpc_idx = db.get("vpc_index", 0)
        if vpc_idx < len(vpcs):
            lines.append(f"    vpc{vpc_idx} --> {did}")

    # Connections
    for conn in resources.get("connections", []):
        src = conn.get("from", "")
        dst = conn.get("to", "")
        label = conn.get("label", "")
        if src and dst:
            if label:
                lines.append(f"    {src} -->|{label}| {dst}")
            else:
                lines.append(f"    {src} --> {dst}")

    # Style classes
    lines.append("")
    lines.append("    classDef vpc fill:#FF9900,stroke:#232F3E,color:#fff")
    lines.append("    classDef ec2 fill:#ED7100,stroke:#232F3E,color:#fff")
    lines.append("    classDef s3 fill:#3F8624,stroke:#232F3E,color:#fff")
    lines.append("    classDef lambda fill:#D45B07,stroke:#232F3E,color:#fff")
    lines.append("    classDef rds fill:#2E73B8,stroke:#232F3E,color:#fff")

    # Apply styles
    if vpcs:
        lines.append(f"    class {','.join(f'vpc{i}' for i in range(len(vpcs)))} vpc")
    if instances:
        lines.append(f"    class {','.join(f'ec2_{i}' for i in range(len(instances)))} ec2")
    if buckets:
        lines.append(f"    class {','.join(f's3_{i}' for i in range(len(buckets)))} s3")
    if functions:
        lines.append(f"    class {','.join(f'lambda_{i}' for i in range(len(functions)))} lambda")
    if databases:
        lines.append(f"    class {','.join(f'rds_{i}' for i in range(len(databases)))} rds")

    return "\n".join(lines)


def _generate_flowchart_mermaid(resources: dict[str, Any]) -> str:
    """Generate a Mermaid flowchart from deployment/workflow steps."""
    lines = ["flowchart TD"]

    steps = resources.get("steps", [])
    for i, step in enumerate(steps):
        sid = f"step{i}"
        name = step.get("name", f"Step {i+1}")
        shape = step.get("shape", "rect")

        if shape == "diamond":
            lines.append(f'    {sid}{{{{{name}}}}}')
        elif shape == "rounded":
            lines.append(f'    {sid}("{name}")')
        elif shape == "stadium":
            lines.append(f'    {sid}(["{name}"])')
        else:
            lines.append(f'    {sid}["{name}"]')

        if i > 0:
            prev = f"step{i-1}"
            label = step.get("from_label", "")
            if label:
                lines.append(f"    {prev} -->|{label}| {sid}")
            else:
                lines.append(f"    {prev} --> {sid}")

    return "\n".join(lines)


def _generate_sequence_mermaid(resources: dict[str, Any]) -> str:
    """Generate a Mermaid sequence diagram."""
    lines = ["sequenceDiagram"]

    participants = resources.get("participants", [])
    for p in participants:
        lines.append(f"    participant {p}")

    interactions = resources.get("interactions", [])
    for ix in interactions:
        src = ix.get("from", "")
        dst = ix.get("to", "")
        msg = ix.get("message", "")
        arrow = ix.get("arrow", "->>")
        lines.append(f"    {src}{arrow}{dst}: {msg}")

    return "\n".join(lines)


# ── React Flow helpers ──────────────────────────────────────────

def _generate_reactflow_nodes(resources: dict[str, Any]) -> dict[str, Any]:
    """Generate React Flow nodes and edges from resources."""
    nodes = []
    edges = []
    y_offset = 0

    for i, vpc in enumerate(resources.get("vpcs", [])):
        nodes.append({
            "id": f"vpc{i}",
            "type": "group",
            "data": {"label": vpc.get("name", f"VPC-{i}")},
            "position": {"x": 0, "y": y_offset},
            "style": {"width": 600, "height": 300, "backgroundColor": "rgba(255,153,0,0.1)"},
        })
        y_offset += 350

    x_offset = 50
    for i, inst in enumerate(resources.get("instances", [])):
        parent_vpc = inst.get("vpc_index", 0)
        nodes.append({
            "id": f"ec2_{i}",
            "data": {"label": inst.get("name", f"EC2-{i}"), "type": "ec2"},
            "position": {"x": x_offset, "y": 50},
            "parentNode": f"vpc{parent_vpc}" if parent_vpc < len(resources.get("vpcs", [])) else None,
        })
        x_offset += 200

    for i, bucket in enumerate(resources.get("buckets", [])):
        nodes.append({
            "id": f"s3_{i}",
            "data": {"label": bucket.get("name", f"S3-{i}"), "type": "s3"},
            "position": {"x": 50 + i * 200, "y": y_offset},
        })

    for conn in resources.get("connections", []):
        edges.append({
            "id": f"e-{conn.get('from')}-{conn.get('to')}",
            "source": conn.get("from", ""),
            "target": conn.get("to", ""),
            "label": conn.get("label", ""),
            "animated": conn.get("animated", False),
        })

    return {"nodes": nodes, "edges": edges}


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/diagrams/generate")
async def generate_diagram(request: DiagramRequest) -> DiagramResponse:
    """
    Generate a diagram from resource discovery data.

    Supports three diagram types:
      - architecture: Infrastructure topology (default)
      - flowchart: Deployment/workflow steps
      - sequence: Service interaction sequence

    And two formats:
      - mermaid: Returns Mermaid syntax for client-side rendering (default)
      - reactflow: Returns React Flow nodes/edges JSON

    For Mermaid output the client renders using mermaid.js.
    For React Flow output the client renders using @xyflow/react.
    """
    diagram_type = request.type
    resources = request.resources
    fmt = request.format

    if fmt == "reactflow":
        flow_data = _generate_reactflow_nodes(resources)
        return DiagramResponse(
            type=diagram_type,
            format="reactflow",
            content=json.dumps(flow_data),
        )

    # Mermaid output (default or svg)
    generators = {
        "architecture": _generate_architecture_mermaid,
        "flowchart": _generate_flowchart_mermaid,
        "sequence": _generate_sequence_mermaid,
    }

    generator = generators.get(diagram_type)
    if generator is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown diagram type: {diagram_type}. Supported: {list(generators.keys())}",
        )

    mermaid_content = generator(resources)

    return DiagramResponse(
        type=diagram_type,
        format="mermaid",
        content=mermaid_content,
    )


@router.post("/sessions/{session_id}/diagrams")
async def generate_and_save_diagram(session_id: str, request: DiagramRequest) -> DiagramResponse:
    """
    Generate a diagram and save it as a session artifact.
    """
    state = _get_state()
    session_mgr = state["session_manager"]

    session = session_mgr.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Generate the diagram
    result = await generate_diagram(request)

    # Save as artifact
    from ..core.artifact_manager import ArtifactManager
    artifact_mgr = ArtifactManager(session_mgr._session_workspace(session_id))

    ext = "mmd" if result.format == "mermaid" else "json"
    filename = f"diagram-{request.type}-{uuid.uuid4().hex[:8]}.{ext}"

    artifact = artifact_mgr.create(
        name=filename,
        content=result.content.encode("utf-8"),
        source="system-exported",
    )

    result.artifactId = artifact["id"]
    return result
