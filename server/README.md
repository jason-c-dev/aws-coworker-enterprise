# ACW Server

The ACW Server wraps AWS Coworker via the Claude Code SDK, exposing a REST + SSE API for session management, resource browsing, and execution observability.

It is the primary deployment artifact for AWS Coworker beyond a laptop. The server runs standalone — no UI is required. The [web-ui/](../web-ui/) directory contains an optional reference implementation that consumes this API.

## Quick Start

```bash
cd aws-coworker-enterprise

# Create a virtual environment
python3 -m venv server/.venv
source server/.venv/bin/activate

# Install dependencies
pip install -r server/requirements.txt

# Start the server
python -m server
```

The server starts on `http://localhost:8080`. Test it:

```bash
curl http://localhost:8080/ping          # Health check
curl http://localhost:8080/api/sessions  # List sessions
curl http://localhost:8080/api/commands  # List commands
open http://localhost:8080/docs          # OpenAPI / Swagger UI
```

## API-Only vs With Web UI

The server auto-detects whether the web UI has been built. If `web-ui/dist/` exists, the server serves the UI at the root path (`/`). If not, `GET /` returns a JSON summary of available API endpoints.

To run with the web UI:

```bash
# Build the web UI first
cd web-ui && npm install && npm run build && cd ..

# Start the server (auto-detects web-ui/dist/)
source server/.venv/bin/activate
python -m server
```

Then open `http://localhost:8080` in your browser.

## Development Mode

For hot-reload during development:

```bash
# Terminal 1: Server with auto-reload
source server/.venv/bin/activate
python -m server.server --reload

# Terminal 2: Web UI dev server (optional — proxies API to server)
cd web-ui && npm run dev
# Opens at http://localhost:5173 with hot module replacement
```

## Configuration

All configuration is via environment variables with sensible defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Bind port |
| `AWS_COWORKER_ROOT` | Parent of `server/` | Path to AWS Coworker project root |
| `WORKSPACE_BASE_PATH` | `server/workspaces/` | Where session data lives |
| `CLAUDE_CODE_USE_BEDROCK` | `0` | Set to `1` for Bedrock inference (deployed environments) |
| `AWS_REGION` | `us-east-1` | Target AWS region |
| `AWS_PROFILE` | (empty) | AWS CLI profile |
| `MAX_SESSIONS` | `10` | Maximum concurrent sessions |
| `SESSION_IDLE_TIMEOUT` | `3600` | Seconds before idle session cleanup |
| `ALLOWED_TOOLS` | `Read,Write,Edit,...` | Tools the SDK session can use |

## API Endpoints

The full API is documented at `/docs` (Swagger UI) and `/openapi.json` when the server is running.

Key endpoint groups:

| Group | Prefix | Purpose |
|-------|--------|---------|
| AgentCore | `/ping`, `/invocations` | Health check + unified invocation (Agent Core protocol) |
| Sessions | `/api/sessions` | Session CRUD, messaging, history |
| Resources | `/api/commands`, `/api/skills`, `/api/agents`, `/api/config` | Browse and edit AWS Coworker internals |
| Observability | `/api/sessions/{id}/trace`, `/api/sessions/{id}/logs` | Execution traces and filtered logs |
| Diagrams | `/api/diagrams/generate` | Infrastructure diagram generation |

## Streaming (SSE)

`POST /api/sessions/{id}/messages/stream` emits Server-Sent Events with 12 typed event types: `message`, `tool_use`, `tool_result`, `sub_agent_spawn`, `sub_agent_event`, `sub_agent_complete`, `permission_request`, `permission_grant`, `error`, `todo_update`, `session_info`, `execution_complete`.

Any HTTP client that supports SSE can consume the stream — curl, EventSource, fetch with ReadableStream, etc.

## Directory Structure

```
server/
├── __init__.py
├── __main__.py              # python -m server entry point
├── main.py                  # FastAPI app, lifespan, static file serving
├── server.py                # CLI entry point (arg parsing, uvicorn)
├── config.py                # Environment config and path constants
├── requirements.txt
├── api/
│   ├── agentcore.py         # /ping, /invocations
│   ├── sessions.py          # Session CRUD + message streaming
│   ├── resources.py         # Commands/Skills/Agents/Config CRUD
│   ├── observability.py     # Trace and log endpoints
│   ├── diagrams.py          # Diagram generation
│   └── schemas.py           # Pydantic request/response models
├── core/
│   ├── session_manager.py   # Session lifecycle, SDK client pool
│   ├── artifact_manager.py  # Artifact CRUD, file storage
│   ├── sdk_client.py        # Claude Agent SDK wrapper
│   ├── event_stream.py      # SSE event types, serialization
│   └── permission_handler.py # Permission request/grant flow
├── file_ops/
│   ├── markdown.py          # YAML frontmatter parser
│   ├── safe_manager.py      # Path-safe file I/O
│   └── validators.py        # Schema validation per file type
└── workspaces/              # Session data (gitignored)
    └── {session-id}/
        ├── session.json     # Session metadata
        ├── history.jsonl    # Conversation history
        └── artifacts/       # Session artifacts
```

## Deployment

The server implements the Bedrock Agent Core protocol contract (`/invocations` + `/ping` on port 8080) from day one, so the same container works on EC2 now and Agent Core later.

For containerised deployment, override `WORKSPACE_BASE_PATH` to point at persistent storage (EBS volume, EFS mount, or S3-backed path).

See `docs/PLAN-DETACHABLE-CLI-PIVOT.md` for full deployment architecture.
