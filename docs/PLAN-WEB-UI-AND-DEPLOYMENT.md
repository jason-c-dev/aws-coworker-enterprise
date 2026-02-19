# Plan: AWS Coworker Web UI and Self-Deployment

**Status:** Draft — awaiting approval
**Created:** 2026-02-18
**Context:** During D-D test preparation, we discovered that Bedrock AgentCore requires a FastAPI HTTP wrapper around the Claude Agent SDK. This aligns with a pre-existing requirement: running AWS Coworker as a web service with a UI. Rather than blocking on AgentCore-specific infrastructure, we build the web wrapper first, deploy it to EC2 using AWS Coworker itself, and defer AgentCore deployment to Part 4.

---

## Part A: Blog Reorganization (Part 3)

### What stays unchanged

- **Sections 1–3** (profiles.yaml deletion, flow logs bug, trust-and-safety parallel) — no changes needed.
- **Section 4 D-G governance tests** (D-G1 through D-G4) — all governance patterns are deployment-target-agnostic. Classification, enforcement, WAR evaluation, failure guardrails — all validated and all still apply.
- **Section 6 Agent Teams** — "Why We Said Not Yet" — unchanged.

### What changes

1. **Introduction** — Remove the claim that we deployed to AgentCore in Part 3. Replace with: we validated the governance pipeline against the agent's own deployment, discovered what AgentCore requires (HTTP wrapper + Claude Agent SDK), and deployed the web UI to EC2 as the "deploy yourself" milestone. AgentCore becomes a Part 4 topic.

2. **Section 4 narrative intro** — The current intro mentions AgentCore as the deployment target. Update to explain that D-G tests validated the governance pipeline, then we discovered the AgentCore architecture requires a web wrapper — which led to the decision to build the web UI first and deploy to EC2.

3. **Add new subsection to Section 4** — "The AgentCore Discovery" — after D-G4, before Section 5. Covers:
   - What we learned about AgentCore's invocation model (HTTP protocol contract, `/invocations` + `/ping`)
   - The AWS sample repo that demonstrates Claude Agent SDK on AgentCore
   - Why this means we need a FastAPI wrapper
   - The strategic decision: build the web UI (already planned) first, deploy to EC2, defer AgentCore to Part 4
   - Nothing we built needs undoing — governance patterns are universal

4. **Section 5** — Replace the "Self-Extending System" placeholder with the web UI build and EC2 deployment story (to be written after we build it). This becomes the actual "deploy yourself" moment — AWS Coworker deploys its own web interface to AWS.

5. **What We Learned** — Add lessons from the AgentCore discovery and the web UI pivot. Update the self-knowledge discussion to include the wrapper as another layer of self-knowledge.

6. **What's Next** — Part 4 becomes: AgentCore deployment (the wrapper is already built, now package it for AgentCore), the self-extending system experiment, and possibly the "Developer's New Job" essay.

### What does NOT need undoing

- D-G test results — governance patterns are target-agnostic
- CLI playbook fix (bedrock-agentcore-control namespace) — correct regardless
- Failure guardrails — needed for any deployment scenario
- Deployment manifest (config/deployment.md) — still describes AWS Coworker's runtime needs
- MVA baselines — apply to EC2 deployment too

---

## Part B: Web UI Architecture

### Overview

Two startup modes for AWS Coworker:

| Mode | How it runs | Use case |
|------|-------------|----------|
| **CLI (current)** | `./acw` on local machine | Local AWS management, development, testing |
| **Web UI** | FastAPI + React, deployed to AWS | Team access, persistent sessions, production use |

The web UI is not just a chat wrapper — it's a **developer workbench** that exposes AWS Coworker's internals (commands, skills, agents, config) as browsable and editable resources. The streaming protocol is **fully transparent**: every tool call, sub-agent spawn, error, and log entry flows to the client. The UI decides what to surface versus collapse, the backend hides nothing.

### Components

#### 1. Backend: FastAPI Wrapper

**Purpose:** Translate HTTP requests into Claude Agent SDK sessions and expose AWS Coworker's resource files as REST APIs.

##### 1a. Chat & Session Endpoints (AgentCore Protocol)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/invocations` | POST | Unified API — routes requests to session/message handlers |
| `/ping` | GET | Health check — returns "Healthy" |
| `/api/sessions` | POST | Create new session (optional: name, profile, region) |
| `/api/sessions` | GET | List all sessions (name, status, created, last activity, artifact count) |
| `/api/sessions/{id}` | GET | Get session details including metadata and artifact list |
| `/api/sessions/{id}` | PATCH | Update session metadata (rename, update description) |
| `/api/sessions/{id}` | DELETE | Delete session — cascading delete of all artifacts and workspace |
| `/api/sessions/{id}/messages` | POST | Send message to session |
| `/api/sessions/{id}/messages/stream` | POST | Send message with SSE streaming |
| `/api/sessions/{id}/history` | GET | Conversation history with execution events |

**Session artifact endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sessions/{id}/artifacts` | GET | List all artifacts for a session (name, type, size, created) |
| `/api/sessions/{id}/artifacts/{artifactId}` | GET | Get/download a specific artifact |
| `/api/sessions/{id}/artifacts` | POST | Upload/create an artifact (any file type) |
| `/api/sessions/{id}/artifacts/{artifactId}` | DELETE | Delete a specific artifact |

##### 1b. Resource Management Endpoints (NEW)

**Commands API** — CRUD for `.claude/commands/*.md` files:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/commands` | GET | List all commands with parsed YAML frontmatter (name, description, agent, skills, tools, arguments) |
| `/api/commands/{name}` | GET | Get single command with full markdown content |
| `/api/commands/{name}` | PATCH | Update command (metadata + body) |
| `/api/commands` | POST | Create new command |
| `/api/commands/{name}` | DELETE | Delete command |

**Skills API** — CRUD for `skills/` hierarchy:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/skills` | GET | List all skills as hierarchy (categories → skills → sub-files) |
| `/api/skills/{id}` | GET | Get skill with parsed frontmatter + content. ID supports nested paths (e.g., `aws-cli-playbook/commands/s3`) |
| `/api/skills/{id}` | PATCH | Update skill |
| `/api/skills` | POST | Create new skill |
| `/api/skills/{id}` | DELETE | Delete skill |

**Agents API** — CRUD for `.claude/agents/*.md` files:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agents` | GET | List all agent definitions |
| `/api/agents/{id}` | GET | Get agent with full content |
| `/api/agents/{id}` | PATCH | Update agent |
| `/api/agents` | POST | Create new agent |
| `/api/agents/{id}` | DELETE | Delete agent |

**Config API** — Read/update configuration files:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/config` | GET | Get all config sections |
| `/api/config/{section}` | GET | Get specific section (orchestration, deployment, environments) |
| `/api/config/{section}` | PATCH | Update config section |

All resource endpoints read/write markdown files on disk via a `SafeFileManager` class with path traversal protection. Responses include both the parsed YAML frontmatter (as structured JSON) and the raw markdown body.

##### 1c. Observability Endpoints (NEW)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sessions/{id}/trace` | GET | Full execution trace for a session (tree of all events) |
| `/api/sessions/{id}/logs` | GET | Filtered log entries for a session (by level, source, keyword) |

##### 1d. Streaming Event Protocol (SSE)

The streaming endpoint (`/api/sessions/{id}/messages/stream`) emits Server-Sent Events. Every execution event becomes a typed message — the backend hides nothing from the client.

| Event Type | When Emitted | Key Fields |
|---|---|---|
| `message` | Claude produces text | `content`, `delta` (boolean — chunk vs complete) |
| `tool_use` | Claude calls a tool | `tool`, `input`, `status` (started/completed) |
| `tool_result` | Tool returns | `toolUseId`, `output`, `exitCode`, `error` |
| `sub_agent_spawn` | Task tool creates sub-agent | `agentId`, `agentName`, `model`, `task` |
| `sub_agent_event` | Sub-agent calls a tool (nested) | `agentId`, `eventType`, `event` (nested object) |
| `sub_agent_complete` | Sub-agent finishes | `agentId`, `status`, `result`, `duration` |
| `permission_request` | Claude needs approval | `action`, `description`, `blastRadius`, `awaitingResponse` |
| `permission_grant` | User approves/denies | `permissionId`, `approved` |
| `error` | Error occurs | `severity`, `source`, `message`, `recoverable` |
| `todo_update` | Todo list changes | `todos` (full list with statuses) |
| `session_info` | Profile/region announced or session metadata updated | `profile`, `region`, `environment`, `suggestedName`, `suggestedDescription` |
| `execution_complete` | Stream ends | `eventCount`, `duration`, `agentsSpawned`, `errors`, `summary` |

Sub-agent events nest within the parent stream. The event tree looks like:

```
Session Message
├── tool_use: Bash (aws s3 ls)
│   └── tool_result: [output, exit 0]
├── tool_use: Task (spawn sub-agent)
│   ├── sub_agent_spawn: aws-coworker-planner (haiku)
│   │   ├── sub_agent_event: tool_use → Bash (aws sts get-caller-identity)
│   │   ├── sub_agent_event: tool_result → [output]
│   │   ├── sub_agent_event: tool_use → Bash (aws s3api list-buckets)
│   │   ├── sub_agent_event: tool_result → [output]
│   │   └── sub_agent_complete: success, "Found 3 buckets"
│   └── tool_result: [aggregated results]
├── error: Access Denied (recoverable)
├── permission_request: Create S3 bucket — awaiting approval
└── message: "Found 3 buckets..."
```

##### 1e. Permission Flow

When the SDK session triggers a `can_use_tool` callback for a mutation:
1. Backend emits `permission_request` SSE event with action description and blast radius
2. Backend pauses the SDK session (awaiting response)
3. Frontend renders a permission modal with approve/deny buttons
4. User clicks approve → frontend POSTs to `/api/sessions/{id}/permissions/{permissionId}`
5. Backend receives grant, resumes SDK session
6. Backend emits `permission_grant` SSE event

##### 1f. File Operations Module

New `backend/file_ops/` module for reading and writing markdown files:

**`markdown.py`** — `MarkdownFile` class:
- Parses YAML frontmatter from `---` delimiters
- Extracts markdown body
- Serializes back to `---\nYAML\n---\n\nbody` format
- Handles the format used by all commands, skills, and agents

**`safe_manager.py`** — `SafeFileManager`:
- Resolves file IDs to absolute paths within allowed base directories
- Prevents `..` traversal: normalizes path, validates it stays within base
- Base paths: `commands` → `.claude/commands/`, `agents` → `.claude/agents/`, `skills` → `skills/`, `config` → `config/`
- All reads and writes go through this class

**`validators.py`** — Schema validation per file type:
- Commands: must have `description`, `agent`, `tools` in frontmatter
- Skills: must have `name`, `category` in frontmatter
- Agents: must have identity section in body
- Returns structured validation results (valid/invalid + specific errors)

##### 1g. Session Lifecycle and Artifacts

**Sessions are first-class entities.** Each session has its own metadata, conversation history, SDK client instance, workspace directory, and artifact storage.

**Session metadata** — stored as a `session.json` file in the session's workspace directory:
- `id` — UUID, generated on creation
- `name` — human-readable name. If the user provides one at creation, use it. Otherwise, the model generates a name from the first message (e.g., "S3 Bucket Audit" from "What S3 buckets do I have?"). As the conversation evolves, the model can update the name to be more reflective of what actually happened (e.g., "S3 Audit → VPC Remediation" if the scope shifted). The name update is a suggestion — the user can rename at any time via PATCH.
- `description` — optional longer description, also model-generated and user-editable. Summarizes what the session accomplished or is working on.
- `profile` — AWS profile in use
- `region` — AWS region
- `environment` — classification (sandbox, development, staging, production)
- `status` — `active`, `idle`, `closed`
- `created` — timestamp
- `lastActivity` — timestamp of last message
- `artifactCount` — number of artifacts

**Session workspace** — each session gets a directory:
```
workspaces/
├── {session-id}/
│   ├── session.json          # Session metadata (name, description, profile, etc.)
│   ├── history.jsonl         # Conversation history (messages + events)
│   └── artifacts/            # Session artifacts
│       ├── vpc-topology.svg  # Diagram generated during session
│       ├── deployment-plan.md # Plan document
│       ├── Dockerfile        # Container artifact
│       └── ...               # Any file type
```

**Artifacts** — any file produced during or uploaded to a session:
- Diagrams (SVG, PNG from Mermaid/React Flow/Python diagrams)
- Plans, reports, documents (markdown, docx, pdf)
- Code files (Dockerfile, scripts, configs)
- Container images (references/manifests, not the image bytes themselves)
- Exported traces (JSON)
- Any other file type — the system is type-agnostic

Artifacts are created by:
1. The model during execution (e.g., generates a diagram, writes a plan)
2. The user uploading a file via the artifacts POST endpoint
3. The system capturing outputs (e.g., exported execution trace)

**Session deletion** — cascading: deleting a session removes its workspace directory, all artifacts, conversation history, and closes the SDK client. The API returns a confirmation with a count of what was deleted.

**Session naming flow:**
1. User creates session → optionally provides a name
2. If no name provided → first message is sent → model generates a name from the prompt → backend emits a `session_info` event with the suggested name → backend saves it
3. As conversation continues → model may suggest an updated name if the scope has shifted → emitted as `session_info` event with `suggestedName` field
4. User can rename at any time via `PATCH /api/sessions/{id}` with `{ "name": "...", "description": "..." }`

**SDK client mapping:**
- Map session IDs to Claude Agent SDK `ClaudeSDKClient` instances
- Active sessions maintain a live SDK client (conversation context preserved, ~0.1s per follow-up)
- Idle sessions (no activity for configurable timeout) have their SDK client suspended — can be resumed but costs ~12s startup
- The SDK session has access to all AWS Coworker files (skills, commands, agents, CLAUDE.md) plus its own workspace/artifacts directory

**Claude Agent SDK integration:**
- Import the SDK directly (not subprocess) — see `docs/RESEARCH-SDK-VS-SUBPROCESS.md` for rationale
- Use `ClaudeSDKClient` for session reuse (~0.1s per follow-up vs ~12s per subprocess call)
- Configure tools: Read, Write, Edit, Bash, Glob, Grep, Task, TodoWrite
- Load CLAUDE.md via `setting_sources=["project"]`
- Permission callbacks via `can_use_tool` — feeds into the SSE permission flow
- Skills, commands, and agents are files on disk — the SDK reads them the same way Claude Code does

**Key design decisions:**
- The FastAPI wrapper is thin — session management, HTTP translation, streaming, file CRUD
- All intelligence stays in the Claude Agent SDK + our skills/commands/agents
- The wrapper does NOT duplicate any governance logic — it delegates everything to the SDK session
- Resource management (commands/skills/agents/config) is pure file I/O — read/parse/validate/write markdown files
- Implement the AgentCore protocol contract (`/invocations` + `/ping` on port 8080) from day one, so the same container works on EC2 now and AgentCore later

#### 2. Frontend: Developer Workbench

**Purpose:** Browser-based developer workbench for interacting with AWS Coworker and managing its internals.

This is more than a chat interface. It's a multi-panel workbench with these views:

##### 2a. Layout

**Header** — Always visible: session name (editable inline) + profile indicator (`Profile: dev-admin | Region: us-east-1 | Environment: development`), session switcher dropdown, theme toggle

**Left Sidebar** — View switcher: Chat, Commands, Skills, Agents, Config, Trace, Infrastructure, Artifacts

**Main Panel** — Dynamic content based on selected view

##### 2b. Session Manager

The session manager is accessible from the header dropdown and as the landing view when no session is active:

- **Session list**: All sessions showing name, description, status badge (active/idle/closed), last activity timestamp, artifact count, profile/region
- **Create session**: Button opens a form with optional name, profile, region. If name is blank, model generates one from the first message.
- **Session card**: Click to open/resume. Inline rename (click session name → editable text field). Description shown as subtitle, also editable.
- **Delete session**: Button with confirmation modal — shows artifact count and warns about cascading deletion
- **Session switcher** (header dropdown): Quick-switch between active sessions without going to the full session list
- **Auto-naming**: When the model suggests a name or updated name (via `session_info` event with `suggestedName`), the UI shows a subtle notification: "Session renamed to 'S3 Bucket Audit'" with an undo option
- **Artifact badge**: Each session card shows an artifact count pill. Click navigates to that session's Artifacts view.

##### 2c. Chat Panel (Primary View)

- Natural language input + message history
- SSE streaming for real-time responses
- Inline event summary badges per message: "3 tool uses · 1 sub-agent · 0 errors"
- Click badge to expand → shows execution trace inline (see Execution Trace Viewer below)
- Permission approval buttons appear inline when `permission_request` events arrive
- Environment/profile indicator (which AWS profile and region are active)

##### 2c. Command Browser

- **List view**: All commands, searchable/filterable, showing name + description + agent
- **Detail view**: Parsed frontmatter displayed as structured card (agent, skills, tools, arguments) + rendered markdown body
- **Edit mode**: Side-by-side editor — YAML frontmatter editor with schema hints on left, markdown editor with syntax highlighting on right
- **Execute button**: Sends command to active session with argument form pre-populated from frontmatter
- **Create button**: New command wizard using same editor pattern

##### 2d. Skill Browser

- **Tree view**: Hierarchical display of skill categories → skills → sub-files (e.g., `aws/aws-cli-playbook/commands/s3.md`)
- **Detail view**: Same pattern as commands — frontmatter card + rendered markdown body
- **Edit mode**: Same side-by-side editor
- **Create button**: New skill with category selection

##### 2e. Agent Browser

- **List view**: All agents showing name + identity summary + allowed tools
- **Detail view**: Full agent definition rendered
- **Edit mode**: Same editor pattern
- **Create button**: New agent definition

##### 2f. Config Browser

- **Tabbed sections**: Orchestration, Deployment, Environments
- **Viewer**: Syntax-highlighted markdown with parsed values
- **Edit mode**: Same editor pattern
- **Validate button**: Checks config against schema

##### 2g. Execution Trace Viewer

Chrome DevTools-style expandable tree of all events for a message:

```
[▼] Message: "Discovering S3 buckets..."
    [▼] Tool Use: Bash → aws s3 ls [2ms] ✓
        Input: { "command": "..." }
        Output: (2 lines)
    [▼] Task → Sub-agent: aws-coworker-planner (haiku) [100ms]
        [▼] Bash → aws sts get-caller-identity [5ms] ✓
        [▼] Bash → aws s3api list-buckets [50ms] ✓
        Result: Found 3 buckets ✓
    [!] Error: Access Denied (recoverable)
    [?] Permission Request: Create S3 bucket — awaiting approval
```

- Expandable/collapsible at every level
- Tool inputs shown as formatted JSON
- Tool outputs scrollable with copy button
- Sub-agent events visually nested (indented, different background)
- Errors highlighted (red sidebar)
- Duration and status badges on each node
- Filter: by log level, source, keyword
- Download: export full trace as JSON

##### 2i. Artifacts View

Each session's artifacts are browsable as a dedicated view:

- **Grid/list toggle**: Grid shows thumbnail previews (for images, SVGs, diagrams), list shows name + type + size + created timestamp
- **File type icons**: Lucide icons mapped by extension — `FileImage` for SVG/PNG, `FileText` for markdown/txt, `FileCode` for Dockerfile/scripts, `FileSpreadsheet` for CSV/xlsx, `File` as default
- **Preview panel**: Click an artifact to preview. SVGs and images render inline. Markdown renders as HTML. Code files get syntax highlighting. Binary files show metadata only.
- **Download button**: Download any artifact to the user's local machine
- **Delete button**: Delete individual artifacts with confirmation
- **Upload button**: Upload files from the user's machine into the session's artifact store
- **Auto-created artifacts**: When the model generates diagrams, plans, or exports during a session, they appear here automatically
- **Artifact source badge**: Shows how the artifact was created — "model-generated", "user-uploaded", "system-exported"

##### 2j. Modals

- **Permission Approval**: Action description, blast radius warning, approve/deny buttons
- **Error Detail**: Error message, stack trace (collapsible), retry button
- **File Conflict**: When saving an edited file that changed on disk — shows diff, offers overwrite/discard/merge
- **Confirmation**: For destructive operations (delete command, delete skill, delete session)
- **Delete Session**: Shows session name, artifact count, warns about cascading deletion of all artifacts and history

**Technology:**
- React with TypeScript + Tailwind CSS
- No heavy dependencies — keep it lightweight
- Communicate with backend via REST API + SSE
- Vite for build tooling
- Lucide React for icons

**Nice-to-have (not MVP):**
- Cognito authentication (add when deploying for team use)
- S3 workspace persistence (add when deploying to AgentCore)
- GitHub OAuth (add when code repo access is needed)

##### 2i. Visual Design

**Design language:** AWS Console-inspired. The target audience lives in the AWS Console daily — the workbench should feel familiar while being cleaner and more modern.

**Color palette:**

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| Sidebar/Header background | `#232F3E` (AWS navy) | `#1A1A2E` | Persistent navigation |
| Content background | `#FFFFFF` | `#0F172A` (slate-900) | Main panel |
| Surface/Cards | `#F8FAFC` (slate-50) | `#1E293B` (slate-800) | Cards, panels, editors |
| Border | `#E2E8F0` (slate-200) | `#334155` (slate-700) | Dividers, card borders |
| Primary accent | `#FF9900` (AWS orange) | `#FF9900` | Active states, primary buttons, progress |
| Text primary | `#0F172A` (slate-900) | `#F1F5F9` (slate-100) | Body text |
| Text secondary | `#64748B` (slate-500) | `#94A3B8` (slate-400) | Labels, metadata |
| Success | `#16A34A` (green-600) | `#22C55E` (green-500) | Status dots, exit code 0 |
| Error | `#DC2626` (red-600) | `#EF4444` (red-500) | Error highlights, failed operations |
| Warning | `#D97706` (amber-600) | `#F59E0B` (amber-500) | Advisory enforcement, warnings |
| Info | `#2563EB` (blue-600) | `#3B82F6` (blue-500) | In-progress states, links |

**Typography:**
- UI text: Inter (or system font stack as fallback) — closest open alternative to Amazon Ember
- Code/markdown/trace: JetBrains Mono (or Fira Code as fallback) — monospace for tool outputs, editors, execution trace
- Base size: 14px for body, 13px for code, 12px for metadata/badges

**Layout patterns:**
- Dark navy sidebar (`#232F3E`) with icon + label navigation items, subtle highlight on active view, count badges per section
- Top header bar: session profile/region indicator on left, theme toggle (sun/moon Lucide icon) + session switcher on right
- Breadcrumbs at top of content area (e.g., "Skills > aws-cli-playbook > commands > s3.md")
- Content area uses cards with subtle borders and rounded corners — similar to AWS Console resource detail pages
- Collapsed session info card at bottom of sidebar showing current profile and region

**Key component styling:**
- **Execution trace** — Indentation lines (like a file tree) with colored status dots: green (success), red (error), amber (warning), blue (in-progress). Each tool call block has a clickable header that expands input/output.
- **Permission requests** — Inline banner in chat stream with orange left border (AWS warning pattern), action description, approve (filled orange) + deny (outlined) buttons. Not a modal — inline is less disruptive for developer workflow.
- **Markdown editors** — Split-pane: YAML frontmatter renders as a structured form at the top, markdown body in a CodeMirror editor below with syntax highlighting, live preview panel on right
- **Resource lists** — Table layout with sortable columns, search/filter bar, hover highlighting, click to navigate to detail view
- **Badges** — Small rounded pills: tool count (blue), sub-agent count (purple), error count (red), duration (gray)

**Dark/light mode:**
- Toggle in header using sun/moon Lucide icons
- CSS custom properties for all color tokens — instant theme switch, no flash
- Tailwind `dark:` variant classes throughout
- Default: follow system preference on first load, persist user choice in localStorage

**Icons:** Lucide React throughout. Consistent line weight, clean at small sizes. Key icon mappings:
- Chat: `MessageSquare`
- Commands: `Terminal`
- Skills: `BookOpen`
- Agents: `Bot`
- Config: `Settings`
- Trace: `Activity`
- Expand/collapse: `ChevronRight` / `ChevronDown`
- Success: `CheckCircle`
- Error: `XCircle`
- Warning: `AlertTriangle`
- Edit: `Pencil`
- Create: `Plus`
- Delete: `Trash2`
- Copy: `Copy`
- Download: `Download`
- Theme toggle: `Sun` / `Moon`

##### 2j. Diagram Generation

The workbench includes diagram generation for visualizing AWS infrastructure discovered during sessions.

**Three diagram engines, each for different purposes:**

| Engine | Use Case | Rendering | Interactive? |
|--------|----------|-----------|-------------|
| **Mermaid** | Flowcharts, sequence diagrams, dependency graphs | In-browser (mermaid.js) | No (static SVG) |
| **React Flow** | AWS infrastructure topology, resource relationships | In-browser (react-flow) | Yes (drag, zoom, click) |
| **Python `diagrams`** | Exportable architecture diagrams with official AWS icons | Backend renders SVG/PNG | No (static image) |

**Mermaid** — for inline diagrams in chat and documentation:
- Claude generates Mermaid syntax from execution context (deployment steps, permission flows, agent delegation chains)
- Renders inline in the chat panel and execution trace viewer
- Used for: deployment sequence diagrams, agent orchestration flows, governance decision trees
- Library: `mermaid` (CDN or npm)

**React Flow** — for the interactive infrastructure diagram view:
- New sidebar view: "Infrastructure" (added to Chat, Commands, Skills, Agents, Config, Trace)
- Custom node components styled as AWS services (with service-specific Lucide icons or small AWS SVGs)
- Discovery output feeds directly into React Flow's node/edge data model
- Nodes are clickable → opens resource detail panel
- Auto-layout via dagre or ELK algorithms
- Updates live when discovery runs again
- Used for: VPC topology, resource dependency graphs, security group relationships, IAM role chains
- Library: `@xyflow/react` (React Flow v12)

**Python `diagrams`** — for exportable static architecture diagrams:
- Backend endpoint: `POST /api/diagrams/generate` — accepts discovery data, returns SVG/PNG
- Uses official AWS architecture icons (looks like a Solutions Architect diagram)
- Used for: blog posts, documentation, Well-Architected reviews, export to PNG/SVG
- Library: `diagrams` (mingrammer/diagrams) + Graphviz on backend
- Optional: Claude generates the Python code from discovery data, backend executes and returns rendered image

**Diagram data flow:**
```
Discovery (aws s3 ls, describe-vpcs, etc.)
    → Structured resource data (JSON)
        → Mermaid syntax (for inline flowcharts)
        → React Flow nodes/edges (for interactive view)
        → Python diagrams code (for exportable architecture diagrams)
```

#### 3. Container Packaging

**Dockerfile:**
- ARM64 base image (required by AgentCore, works fine on EC2 Graviton too)
- Python 3.12+ with UV package manager
- Claude Agent SDK dependencies
- FastAPI + Uvicorn
- Node.js build for React frontend (serve static files from FastAPI)
- Copy AWS Coworker files (skills, commands, agents, config, CLAUDE.md)
- Expose port 8080

**Key environment variables:**
- `CLAUDE_CODE_USE_BEDROCK=1` — use IAM roles for model access
- `AWS_REGION` — target region
- `ALLOWED_TOOLS` — which tools the SDK session can use
- `WORKSPACE_BASE_PATH` — where session workspaces live

#### 4. Local Development Mode

**For running on your laptop:**
```bash
# Option 1: CLI mode (current, unchanged)
./acw

# Option 2: Web UI mode (new)
./acw --server
# or
docker-compose up
```

The `--server` flag (or docker-compose) starts the FastAPI server locally. You open `http://localhost:8080` in your browser. The backend uses your local AWS credentials (no `CLAUDE_CODE_USE_BEDROCK` needed locally — that's only for deployed environments).

### Project Structure

```
aws-coworker-enterprise/
├── backend/
│   ├── main.py                     # FastAPI app initialization
│   ├── server.py                   # Entry point (arg parsing, uvicorn)
│   ├── config.py                   # Environment config
│   ├── api/
│   │   ├── __init__.py
│   │   ├── agentcore.py            # /ping, /invocations
│   │   ├── sessions.py             # Session CRUD + message endpoints
│   │   ├── resources.py            # Commands/Skills/Agents/Config CRUD
│   │   ├── observability.py        # Trace/logs endpoints
│   │   └── schemas.py              # Pydantic request/response models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session_manager.py      # Session lifecycle (ClaudeSDKClient pool, workspace dirs)
│   │   ├── artifact_manager.py     # Artifact CRUD, file storage, cascading deletes
│   │   ├── sdk_client.py           # Claude Agent SDK wrapper
│   │   ├── event_stream.py         # SSE event types, serialization, streaming
│   │   └── permission_handler.py   # Permission request/grant async flow
│   ├── file_ops/
│   │   ├── __init__.py
│   │   ├── markdown.py             # MarkdownFile class (YAML frontmatter parser)
│   │   ├── safe_manager.py         # SafeFileManager (path-safe file I/O)
│   │   └── validators.py           # Schema validation per file type
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.tsx                 # Root component with sidebar + main panel
│   │   ├── components/
│   │   │   ├── ChatPanel/          # Chat interface + streaming + event badges
│   │   │   ├── CommandBrowser/     # List, detail, editor for commands
│   │   │   ├── SkillBrowser/       # Tree, detail, editor for skills
│   │   │   ├── AgentBrowser/       # List, detail, editor for agents
│   │   │   ├── ConfigBrowser/      # Tabbed config viewer/editor
│   │   │   ├── ExecutionTrace/     # DevTools-style tree trace viewer
│   │   │   ├── InfrastructureDiagram/ # React Flow interactive AWS topology
│   │   │   ├── ArtifactBrowser/   # Grid/list view, preview, upload, download
│   │   │   ├── SessionManager/    # Session list, create, rename, delete, switcher
│   │   │   ├── Common/            # Header, Sidebar, ViewToggle, ProfileIndicator, ThemeToggle
│   │   │   └── Modals/             # Permission, Error, FileConflict, Confirmation
│   │   ├── hooks/
│   │   │   ├── useSSE.ts           # SSE with typed event parsing
│   │   │   ├── useResources.ts     # CRUD hooks for commands/skills/agents/config
│   │   │   └── useSession.ts       # Session state management
│   │   ├── services/
│   │   │   ├── api.ts              # REST + SSE client
│   │   │   ├── resources.ts        # Resource API calls
│   │   │   └── events.ts           # Event type parsing + tree construction
│   │   └── types/
│   │       ├── event.ts            # SSE event type definitions (12 types)
│   │       └── resource.ts         # Command/Skill/Agent/Config type defs
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── Dockerfile                       # ARM64 production build
└── docker-compose.yml               # Local development
```

---

## Part C: EC2 Deployment (The "Deploy Yourself" Moment)

### Architecture

AWS Coworker deploys itself to a single EC2 instance in a development/test environment. Well-Architected review applies.

**Target infrastructure:**

| Component | Service | Notes |
|-----------|---------|-------|
| Compute | EC2 t4g.micro (ARM64 Graviton) | Matches AgentCore's ARM64 requirement |
| Container | Docker on EC2 | Single container, same image as local |
| Networking | VPC with public subnet | Dev/test — ALB not required for single instance |
| Security | Security group (HTTPS/443 only) | Plus SSH for management if needed |
| IAM | Instance profile with Bedrock access | Scoped to required models only |
| DNS | Optional — direct IP or Route 53 | Dev/test doesn't need custom domain |
| TLS | Let's Encrypt or ACM | HTTPS even in dev |

**What the WAR should flag:**
- Single instance (no HA) — ACCEPTABLE at dev tier
- Public subnet — ACCEPTABLE at dev tier with warning about staging/prod
- No ALB — ACCEPTABLE at dev tier
- IAM instance profile with Bedrock model access — should be scoped
- `CLAUDE_CODE_USE_BEDROCK=1` in container env — from deployment manifest
- Governance tags on all resources

### Deployment flow

1. User: "Deploy AWS Coworker web UI to my AWS account. This is a development environment."
2. AWS Coworker plans the deployment (profile classification, discovery, WAR evaluation)
3. Enforcement gate (warn at dev tier) — present gaps, proceed
4. User approves
5. AWS Coworker executes: create VPC/subnet (or use existing), create security group, create IAM role, build and push Docker image to ECR, launch EC2 instance with user data that pulls and runs the container
6. Verify: health check on `/ping`, test `/invocations`

### New command: `/aws-coworker-deploy-web-ui`

This is the "batteries included" command — a new slash command that orchestrates the full deployment of AWS Coworker's web interface.

---

## Part D: Documentation Updates

### Files to create or update

| File | Action | What changes |
|------|--------|-------------|
| `README.md` | Update | Add web UI section, two startup modes |
| `docs/GETTING-STARTED.md` | Update | Add web UI quick start alongside CLI |
| `docs/USER-GUIDE.md` | Update | Add web UI usage, deployment guide |
| `config/deployment.md` | Update | Add web UI deployment requirements |
| `.claude/commands/aws-coworker-deploy-web-ui.md` | Create | New deployment command |
| `skills/aws/aws-cli-playbook/commands/ec2.md` | Verify | Ensure EC2 playbook covers user data, instance profiles |
| `backend/` | Create | FastAPI wrapper (new directory) |
| `frontend/` | Create | React web UI (new directory) |
| `Dockerfile` | Create | Container packaging |
| `docker-compose.yml` | Create | Local development |
| `docs/LESSONS-LEARNED-PART-3.md` | Update | Reorganize as described in Part A |

### Getting Started additions

Two paths:

**Path 1: CLI (existing)**
```bash
git clone <repo>
cd aws-coworker
./acw
```

**Path 2: Web UI (new)**
```bash
git clone <repo>
cd aws-coworker
docker-compose up
# Open http://localhost:8080
```

**Path 3: Deploy to AWS (new)**
```bash
./acw
> Deploy AWS Coworker web UI to my AWS account. This is a development environment.
# AWS Coworker plans and deploys itself
```

---

## Part E: Implementation Sequence

### Phase 1: Blog reorganization
- Update Part 3 narrative (intro, Section 4, Section 5 placeholder, What's Next)
- Commit and push

### Phase 2: Backend (FastAPI wrapper)
- Set up `backend/` directory structure (api/, core/, file_ops/)
- Implement core: server.py, session lifecycle management (workspace dirs, metadata, SDK client pool, idle timeout)
- Implement artifact manager: file storage per session, cascading deletes, type detection
- Implement session endpoints: `/api/sessions` CRUD with naming/rename, `/api/sessions/{id}/artifacts` CRUD
- Implement chat endpoints: `/invocations`, `/ping`, `/api/sessions/{id}/messages`
- Implement SSE streaming with full event protocol (12 event types)
- Implement permission flow (can_use_tool → SSE permission_request → POST grant → resume)
- Implement file_ops module: markdown parser, SafeFileManager, validators
- Implement resource endpoints: `/api/commands`, `/api/skills`, `/api/agents`, `/api/config` (full CRUD)
- Implement observability: `/api/sessions/{id}/trace`, `/api/sessions/{id}/logs`
- Implement diagram endpoint: `POST /api/diagrams/generate` (Python `diagrams` library for exportable architecture SVGs)
- Test locally with curl/httpie

### Phase 3: Frontend (Developer Workbench)
- Set up `frontend/` directory (Vite + React + TypeScript + Tailwind)
- Implement visual design system: AWS Console-inspired color palette, dark/light mode toggle, CSS custom properties, Inter + JetBrains Mono typography
- Build layout: dark navy sidebar with Lucide icons + header with profile indicator and theme toggle + breadcrumbs + dynamic main panel
- Build Chat Panel: message list, input, SSE streaming, inline event badges, inline permission approval banners
- Build Command Browser: list, detail view, YAML+markdown editor, execute button
- Build Skill Browser: tree view, detail view, editor, create button
- Build Agent Browser: list, detail, editor
- Build Config Browser: tabbed sections, viewer, editor, validate
- Build Execution Trace Viewer: expandable tree with colored status dots, tool use nodes, sub-agent nodes, error highlighting
- Build Infrastructure Diagram view: React Flow with custom AWS-styled nodes, auto-layout, clickable nodes
- Integrate Mermaid for inline diagrams in chat (flowcharts, sequence diagrams)
- Build Modals: permission approval, error detail, file conflict, confirmation
- Build Session Manager: session list with names/descriptions/artifact counts, create, rename (inline edit), delete with cascade confirmation, switcher dropdown
- Build Artifact Browser: grid/list toggle, file type icons, preview panel, upload, download, delete
- Implement auto-naming: display model-suggested names from `session_info` events, subtle notification with undo
- Build and serve static files from FastAPI

### Phase 4: Container packaging
- Dockerfile (ARM64)
- docker-compose.yml for local dev
- Test full stack locally

### Phase 5: Deployment command
- Create `/aws-coworker-deploy-web-ui` command
- Create deployment skill if needed
- Update deployment manifest

### Phase 6: Self-deployment test
- Use AWS Coworker (CLI) to deploy its own web UI to EC2
- Document the conversation for the blog
- Write Section 5 of Part 3

### Phase 7: Documentation
- Update README, Getting Started, User Guide
- Write blog Section 5 narrative

### Phase 8 (Future — Part 4): AgentCore deployment
- The container already implements the AgentCore protocol contract
- Package for AgentCore (ECR push, create-agent-runtime)
- Add AgentCore-specific features (memory, MCP gateway, A2A)
- The "inception moment" completes

---

## Open Questions

1. **Authentication for web UI** — Do we need Cognito for the dev deployment, or is security group restriction sufficient for dev/test? Recommendation: security group (IP restriction) for dev, Cognito for staging/prod.

Summary:

* Security group and IAM user needed as login for web UI, with limited access to prevent unauthorized access
* Cognito should be used for staging and production
* Adding a CLI capability for Cognito is deferred for now
* Minimum viable architecture should be created to ensure appropriate blocking and remediation of unauthorized access

2. **Claude Agent SDK vs Claude Code subprocess** — The AWS sample uses the SDK directly. Should we also support running Claude Code CLI as a subprocess for users who prefer the CLI's full feature set? Recommendation: SDK first, subprocess as future option.

Summary:
During the meeting, it was discussed that the CLI full feature set includes capabilities such as commands, skills, and subagents. The Claude Agent SDK was suggested as an option for development due to its creation for these purposes. However, concerns were raised about the delta between the Claude Agent SDK and the Claude Code subprocess solution in terms of support for sub processes needed for certain projects, including AWS Coworker. The team agreed to research and clarify the differences before making a decision on which platform to use.

Action items:
- ~~Research and clarify the differences between the Claude Agent SDK and the Claude Code subprocess solution.~~ **DONE** — see `docs/RESEARCH-SDK-VS-SUBPROCESS.md`
- ~~Report back to the team with a recommendation on which platform to use based on the findings.~~ **DONE** — Recommendation: **Claude Agent SDK with `ClaudeSDKClient`**. Skills/commands/agents are files on disk and work unchanged. SDK gives us session reuse (~0.1s per follow-up vs ~12s per subprocess call), permission callbacks for the approval UI, native streaming, and is what the AWS sample project uses.

3. **Model access** — The deployed instance needs Bedrock model access (Opus for orchestrator, Haiku/Sonnet for sub-agents). Should the deployment command verify model access before deploying? Recommendation: yes, as a pre-flight check.

Meeting Summary:

* The team discussed the need for bedrock access from within AWS when deploying anthropic API.
* Claude was given permission to have direct API access to the anthropic API on a laptop, but this should be reviewed and changed once deployed in AWS.
* The team agreed that measures should be taken to ensure everything stays within AWS once deployed.

4. **Workspace persistence** — Where do session workspaces live on the EC2 instance? EBS volume? S3 sync? Recommendation: EBS for dev, S3 sync for prod.

Meeting Summary:

Action Items: None explicitly discussed.

Summary: The meeting discussed the storage of supporting files for development and testing purposes. It was agreed that EBS volumes on EC2 were sufficient, but an S3 sync would be needed for production and staging environments. The minimal viable architecture delta needs to be updated to reflect this change so that the agent can block and remediate as necessary.

5. **Cost** — t4g.micro is ~$6/month. Bedrock model invocations are the real cost. Should we add cost estimation to the deployment plan? Recommendation: yes, include estimated monthly cost.

Action items: None

Summary: Discussed adding a cost to deployment plan. Estimated monthly cost will be provided for low use, medium use, and high use in terms of token usage. It was agreed that this cost may be acceptable as long as it is reasonable and does not exceed the costs of running the system on AWS.