# Web UI — Reference Implementation

This is a reference implementation demonstrating how to consume the [ACW Server](../server/) API. It serves as a developer workbench for interacting with AWS Coworker — browsing commands, skills, agents, config, and chatting with the system through a browser.

**This is optional.** The ACW Server runs standalone and can be consumed directly via `curl`, Bedrock Agent Core, or any HTTP client. This UI is one possible consumer.

## Quick Start

```bash
# Prerequisite: the ACW Server must be running
# See server/README.md for setup instructions

cd web-ui
npm install
npm run build
cd ..

# Start the server (auto-detects web-ui/dist/ and serves it)
source server/.venv/bin/activate
python -m server

# Open http://localhost:8080 in your browser
```

## Development Mode

For hot-reload during UI development:

```bash
# Terminal 1: ACW Server with auto-reload
source server/.venv/bin/activate
python -m server.server --reload

# Terminal 2: Vite dev server (proxies /api/ to the ACW Server)
cd web-ui
npm run dev
# Opens at http://localhost:5173
```

The Vite dev server proxies `/api/`, `/ping`, and `/invocations` to `http://localhost:8080`, so both the server and UI can hot-reload independently.

## Technology

- React 18 with TypeScript
- Tailwind CSS (dark/light mode, AWS Console-inspired design)
- Vite 6 for build tooling
- Lucide React for icons
- Mermaid for inline diagram rendering
- React Flow (@xyflow/react) for interactive infrastructure diagrams

## What It Demonstrates

The web UI shows how to consume every part of the ACW Server API:

| Feature | API Endpoints Used |
|---------|-------------------|
| Session management | `POST/GET/PATCH/DELETE /api/sessions` |
| Chat with streaming | `POST /api/sessions/{id}/messages/stream` (SSE) |
| Permission approval | `POST /api/sessions/{id}/permissions/{permissionId}` |
| Command browsing and editing | `GET/PATCH /api/commands` |
| Skill browsing and editing | `GET/PATCH /api/skills` |
| Agent browsing and editing | `GET/PATCH /api/agents` |
| Config browsing and editing | `GET/PATCH /api/config` |
| Execution trace viewing | `GET /api/sessions/{id}/trace` |
| Artifact management | `GET/POST/DELETE /api/sessions/{id}/artifacts` |
| Diagram generation | `POST /api/diagrams/generate` |

## Directory Structure

```
web-ui/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── src/
│   ├── main.tsx                  # Entry point, theme detection
│   ├── index.css                 # Tailwind directives, custom properties
│   ├── App.tsx                   # Root component, view routing, error boundary
│   ├── types/
│   │   ├── event.ts              # SSE event type definitions (12 types)
│   │   └── resource.ts           # Resource type definitions
│   ├── hooks/
│   │   ├── useSession.ts         # Session state management
│   │   ├── useSSE.ts             # SSE streaming with typed events
│   │   └── useResources.ts       # CRUD hooks for resources
│   ├── services/
│   │   └── api.ts                # REST + SSE client for ACW Server
│   └── components/
│       ├── Common/               # Sidebar, Header, ThemeToggle, ResourceEditor
│       ├── SessionManager/       # Session list, create, delete
│       ├── ChatPanel/            # Chat, streaming, event badges, permissions
│       ├── CommandBrowser/       # Command list, detail, editor
│       ├── SkillBrowser/         # Skill tree, detail, editor
│       ├── AgentBrowser/         # Agent list, detail, editor
│       ├── ConfigBrowser/        # Tabbed config viewer/editor
│       ├── ExecutionTrace/       # DevTools-style trace viewer
│       ├── InfrastructureDiagram/ # React Flow interactive topology
│       └── ArtifactBrowser/      # Grid/list view, preview, upload
└── dist/                          # Build output (gitignored)
```

## Building Your Own Consumer

If you want to build a different UI or integration, the key patterns to follow are:

1. **REST for CRUD**: Standard fetch/axios calls to `/api/*` endpoints
2. **SSE for streaming**: Use `fetch()` with `ReadableStream` to parse `text/event-stream` responses from `/api/sessions/{id}/messages/stream`
3. **Permission flow**: Watch for `permission_request` events in the SSE stream, then `POST` to `/api/sessions/{id}/permissions/{permissionId}` with `{ "approved": true/false }`
4. **Event types**: See `src/types/event.ts` for the 12 SSE event type definitions

The `src/services/api.ts` file is a good starting point — it's a self-contained REST + SSE client with no UI dependencies.
