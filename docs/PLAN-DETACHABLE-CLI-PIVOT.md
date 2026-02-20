# Plan: Detachable CLI Pivot — Remote CLI as Primary Interface

**Status:** Draft — awaiting approval
**Created:** 2026-02-20
**Context:** During REPL client development, we discovered that (a) the Claude Code CLI cannot be pointed at a remote endpoint, and (b) our REPL client already provides a CLI-quality experience over HTTP/SSE. This means the detachable CLI — not the web UI — is the natural primary interface for remote AWS Coworker. The web UI is parked for future work.

---

## The Insight

The Claude Agent SDK is the official decoupling layer between "Claude Code the product" and "Claude Code the engine." The pattern is:

```
Custom CLI client → HTTP/SSE → Container running SDK → Claude Code engine
```

Our REPL client (`tools/repl_client.py`) already demonstrates this: it connects to the ACW Server over HTTP, streams SSE events, and renders them with CLI-quality formatting (spinners, tables, markdown, sub-agent traces). It looks and feels like Claude Code — but the engine is remote.

This is the key innovation: **a detachable CLI that can connect to AWS Coworker running anywhere** — a laptop, an EC2 instance, an ECS container, or AgentCore.

---

## What Changes

### 1. `acw` Becomes a Multi-Mode Entry Point

The existing `acw` launcher is a bash script that shows a banner and launches Claude Code locally. It becomes a multi-mode entry point:

| Mode | Command | What Happens |
|------|---------|-------------|
| **Local CLI** | `acw` (no args, or `acw --local`) | Same as today — banner + `claude` in project dir. No server involved. |
| **Start Server** | `acw server` (or `acw serve`) | Starts the ACW Server (FastAPI + SDK). No client. Headless. |
| **Remote CLI** | `acw connect [url]` | Starts the REPL client, connects to a running ACW Server. |
| **Local Full Stack** | `acw server --with-cli` | Starts server + REPL client together. Dev convenience. |

**Default behavior:** `acw` with no arguments still launches the local Claude Code CLI, exactly as today. The server and remote CLI are opt-in.

### 2. The REPL Client Becomes a First-Class Component

`tools/repl_client.py` moves from a developer tool to a core component:

| Current | After Pivot |
|---------|-------------|
| `tools/repl_client.py` | `cli/acw_client.py` (or similar) |
| Developer testing tool | Primary remote interface |
| Manual startup: `python tools/repl_client.py` | Integrated: `acw connect` |
| Hardcoded to localhost:8000 | Configurable endpoint |

The REPL client already has:
- Async SSE streaming with typed event parsing
- Animated spinner (braille frames, async-safe)
- Box-drawn table rendering from markdown
- Markdown-to-ANSI conversion (bold, code, headings)
- Model name formatting (haiku → Haiku 4.5)
- Clean tool output (strips metadata, unescapes)
- Sub-agent spawn/complete rendering
- Skill loading messages
- Permission request/grant flow (TODO — needs implementation)

What it still needs:
- Configurable server URL (not hardcoded)
- Session management (create, resume, list, switch)
- Connection health/retry logic
- `acw` integration (launched by the bash script)
- Permission approval UX (inline prompt for mutations)
- Multi-line input support
- History/readline support

### 3. Three-Layer Architecture Becomes Four Layers

The existing architecture is:

```
CLI (core) ← Server (wraps) ← Web UI (consumes)
```

The pivot adds the detachable CLI as a **peer** of the Web UI — both consume the server API:

```
CLI (core) ← Server (wraps) ← Detachable CLI (primary consumer)
                              ← Web UI (optional, future)
```

Tenet 10 becomes: **CLI-First, Server-Wraps, Clients-Consume**

The dependency rule is unchanged: clients consume only the server API. The detachable CLI and web UI never read CLI files directly or bypass the server.

### 4. Web UI is Parked

The web UI (`web-ui/`) remains in the repository as a future deliverable. It is not deleted, not deprecated — just deprioritized. The server API it would consume is the same API the detachable CLI consumes.

When we return to the web UI, nothing needs to change in the server — it's already transport-agnostic. The web UI was always documented as "optional reference implementation," so parking it is consistent with existing docs.

### 5. Container Packaging Simplifies

The Dockerfile currently has a multi-stage build: first stage builds the React web UI, second stage is the Python server. With the web UI parked:

| Current | After Pivot |
|---------|-------------|
| Stage 1: Build React app | Removed (or optional) |
| Stage 2: Python + Node.js + web UI dist | Python + Node.js only |
| Container serves: API + static web UI | Container serves: API only |
| Client: Browser | Client: `acw connect` from anywhere |

The container becomes smaller and simpler. The detachable CLI runs on the operator's machine, not in the container.

---

## Clarifying Questions

Before finalizing this plan, these questions need answers:

### Q1: `acw` Script Language

The current `acw` is a 20-line bash script. Adding server/connect/mode-switching logic means it needs to do more. Options:

- **Option A:** Keep bash, add subcommand routing (bash case/switch). Simple, no dependencies.
- **Option B:** Rewrite in Python. Can import the REPL client directly. More maintainable for complex logic.
- **Option C:** Bash wrapper that delegates to Python for server/connect modes. Best of both worlds.

**Recommendation:** Option C — `acw` stays bash for local mode (unchanged), delegates to Python for `server` and `connect` subcommands.

**Answer from Jason:** Agreed - option C

### Q2: CLI Directory Location

Where does the detachable CLI code live?

- **Option A:** `cli/` at project root (peer of `server/`, `web-ui/`)
- **Option B:** `tools/` (current location, just promote it)
- **Option C:** Inside `server/` (since it's tightly coupled to the server API)

**Recommendation:** Option A — `cli/` at root. It's a peer of `server/` and `web-ui/`, consistent with the layered architecture. The dependency is: `cli/` → `server/` API (HTTP), never the reverse.

**Answer from Jason:** Agreed - option A

### Q3: Server Default Port

The server currently defaults to port 8080 (AgentCore requirement). The REPL client currently connects to 8000. Should we:

- **Option A:** Standardize on 8080 everywhere (AgentCore-compatible, one port to remember)
- **Option B:** Use 8000 for local dev, 8080 for deployed (two ports, context-dependent)

**Recommendation:** Option A — 8080 everywhere. AgentCore requires it, and having one port reduces confusion.

**Answer from Jason:** What about option C - defaults to 8080 but you can set with --port param?

**Resolution:** Agreed — Option C. Default to 8080 (AgentCore-compatible), but both `acw server --port 9000` and `acw connect http://host:9000` support custom ports. The server also respects a `PORT` env var (already implemented in server config). This gives us: one default to remember, full flexibility when needed.

### Q4: Session Persistence in CLI

When the user runs `acw connect`, should sessions persist across CLI restarts?

- **Option A:** Yes — sessions live on the server. `acw connect --resume` or `acw connect --session <id>` picks up where you left off.
- **Option B:** No — each `acw connect` creates a fresh session. Simpler.

**Recommendation:** Option A — sessions already persist on the server (that's how the server works). The CLI should expose this. `acw connect` creates a new session, `acw connect --resume` lists and resumes existing sessions.

**Answer from Jason:** Agreed - Option A is a MUST

### Q5: Blog Part 3 — Web UI vs Detachable CLI

The blog roadmap (Section 5 of Part 3) says "Build the FastAPI wrapper + React frontend." With the pivot:

- **Option A:** Part 3 Section 5 becomes "Build the FastAPI server + Detachable CLI" instead. Same narrative arc (deploy yourself), different client.
- **Option B:** Part 3 Section 5 covers both server + CLI, mentions web UI as future. Broader scope.

**Recommendation:** Option A — the detachable CLI is actually a *better* story for the blog. It's more novel ("we built a remote CLI for an AI agent") and more practical for the target audience (infrastructure engineers prefer CLI over web UI).

**Answer from Jason:** Agreed - Option A


### Q6: Client Authentication (raised by Jason)

When `acw connect` talks to a remote server, how do we authenticate the client? Without auth, anyone who can reach the server endpoint can send commands to your AWS account.

**Option A: API Key (shared secret)**
- Server generates a random API key on startup (or reads from env var `ACW_API_KEY`)
- CLI passes it as `Authorization: Bearer <key>` header on every request
- Simple, no external dependencies, works everywhere
- Downsides: key must be distributed out-of-band, no identity granularity (one key = full access), rotation requires server restart

**Option B: AWS IAM (SigV4 signing)**
- Client signs requests using local AWS credentials (same `~/.aws/credentials` already on the operator's machine)
- Server validates the signature using STS `GetCallerIdentity` or a custom authorizer
- No new secrets to manage — reuses existing AWS identity
- Provides identity: server knows *who* is connecting (IAM principal ARN)
- Downsides: more complex implementation, requires both sides to have AWS access, adds latency per request for validation

**Option C: Mutual TLS (mTLS)**
- Client presents a certificate, server validates it
- Strong cryptographic identity, no shared secrets
- Downsides: certificate management overhead (generate, distribute, rotate), complex setup for a dev tool

**Option D: No auth for local, API key for remote**
- `acw server` on localhost (127.0.0.1) requires no auth — same trust model as Claude Code locally
- `acw server --bind 0.0.0.0` (network-accessible) requires `ACW_API_KEY` to be set and refuses to start without it
- `acw connect` passes the key from `--api-key` flag or `ACW_API_KEY` env var
- Progressive security: zero friction for local dev, mandatory auth for exposed endpoints

**Recommendation:** Option D with a path to Option B.

**Answer from Jason:** Agreed - Option D -> Option B (will this work for Agent Core?)

**Answer: Yes — and AgentCore actually makes Option B unnecessary for that deployment target.** Here's why:

AgentCore handles authentication at the platform level *before* the request ever reaches your container. The flow is:

```
Client (aws bedrock-agentcore invoke-agent-runtime)
  → SigV4-signed with caller's IAM credentials
    → AgentCore validates bedrock-agentcore:InvokeAgentRuntime permission
      → Request forwarded to container (already authenticated)
        → /invocations receives pre-authenticated request
```

The container **never sees or validates** the caller's identity. By the time a request hits `/invocations`, AWS has already confirmed the caller has permission. Our `server/api/agentcore.py` has no auth logic — and that's correct.

This means the auth progression is:

| Deployment | Auth Mechanism | Who Handles It |
|------------|---------------|---------------|
| **Local** (`acw server` on 127.0.0.1) | None needed | Localhost trust |
| **Remote EC2/ECS** (`acw server --bind 0.0.0.0`) | API Key (Option D) | Our server middleware |
| **AgentCore** | IAM SigV4 via `InvokeAgentRuntime` | **AgentCore platform** — not us |

So the path is:
- **Day 1 (now):** Option D — no auth local, API key remote. We implement this.
- **Day 2 (EC2/ECS deployment):** Option D still works. Security group + API key.
- **Day 3 (AgentCore):** Option B is **free** — AgentCore's platform does it for us. Our container doesn't need to change at all. Clients just switch from `acw connect https://ec2:8080 --api-key X` to `aws bedrock-agentcore invoke-agent-runtime --agent-runtime-id Y`.

The only gap: when deployed to AgentCore, operators can't use `acw connect` directly (AgentCore doesn't expose raw HTTP — it uses the `InvokeAgentRuntime` API). We'd need either:
- A thin `acw connect --agentcore <runtime-id>` mode that wraps the `InvokeAgentRuntime` API call
- Or operators use the AWS CLI / SDK to invoke directly

This is a Part 4 concern, not a Day 1 blocker.

**Rationale:**
- **Day 1:** Option D gives us the right security posture with minimal friction. Local dev has zero overhead. Remote requires a shared secret — good enough for single-operator use.
- **Day 2 (EC2/ECS):** Option D still applies. API key + security group.
- **Day 3 (AgentCore):** Platform-managed IAM auth. Zero changes to our container.
- Option C (mTLS) is overkill for our use case. Option A alone doesn't handle the local/remote distinction.

**Implementation sketch for Option D:**
```
# Local (no auth needed)
acw server                          # Binds to 127.0.0.1:8080, no auth
acw connect                         # Connects to localhost:8080, no key needed

# Remote EC2/ECS (API key required)
export ACW_API_KEY=$(openssl rand -hex 32)
acw server --bind 0.0.0.0          # Requires ACW_API_KEY, refuses without it
acw connect https://remote:8080 --api-key $ACW_API_KEY

# AgentCore (platform auth — no changes to container)
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-id abc123 \
  --payload '{"message": "List my S3 buckets"}'
# Future: acw connect --agentcore abc123  (Part 4)
```

### Q6a: CLI Transport Abstraction (AgentCore Detail)

The container doesn't need auth changes for AgentCore — but the **CLI client does**. The CLI needs to handle three fundamentally different ways of talking to the server, and it needs to be clear at implementation time which pieces change per deployment target.

**The problem:** AgentCore doesn't expose raw HTTP. You can't `curl http://agentcore-endpoint:8080/api/sessions`. Instead, you call the AWS API (`InvokeAgentRuntime`), which is SigV4-signed, and AgentCore forwards the pre-authenticated payload to the container's `/invocations`. This means the CLI can't just swap a URL and an auth header — it's a different protocol.

**The solution:** The CLI client needs a **transport layer** that abstracts the connection target.

```
acw connect
  └── ACWClient (session management, rendering, input)
        └── Transport (abstract)
              ├── HTTPTransport          ← Day 1 (local + EC2/ECS)
              │   • Base URL: http(s)://host:port
              │   • Auth: None (local) or Bearer API key (remote)
              │   • Sessions: POST /api/sessions, POST /api/sessions/{id}/messages/stream
              │   • Streaming: Native SSE (EventSource / aiohttp)
              │
              └── AgentCoreTransport     ← Part 4
                  • Target: agent-runtime-id + region
                  • Auth: SigV4 via boto3 (uses ~/.aws/credentials)
                  • Sessions: Mapped to InvokeAgentRuntime payload
                  • Streaming: InvokeAgentRuntime response stream → parse into same event types
```

**What each transport must implement:**

| Method | HTTPTransport | AgentCoreTransport |
|--------|--------------|-------------------|
| `create_session()` | `POST /api/sessions` | Implicit — AgentCore may create on first invoke, or we map to a session concept in the payload |
| `send_message(session_id, text)` | `POST /api/sessions/{id}/messages/stream` (SSE) | `invoke-agent-runtime --payload {session_id, message}` (streaming response) |
| `list_sessions()` | `GET /api/sessions` | May not be supported — AgentCore sessions are runtime-managed |
| `resume_session(session_id)` | `POST /api/sessions/{id}/messages/stream` (same endpoint) | `invoke-agent-runtime --payload {session_id, message}` with prior session reference |
| `auth_headers()` | `Authorization: Bearer <key>` or empty | SigV4 signature (boto3 handles automatically) |

**What stays the same across transports:**
- The SSE event types (12 types) — both transports parse into the same event model
- The rendering layer (spinners, tables, markdown, sub-agent traces)
- Session management UX (create, resume, list)
- Permission approval flow (inline Y/N prompt)

**What changes per transport:**
- How HTTP requests are made (raw HTTP vs boto3 API call)
- How auth is applied (header vs SigV4)
- How streaming responses are consumed (SSE stream vs InvokeAgentRuntime response stream)
- Session lifecycle semantics (our server's sessions vs AgentCore's session model)

**Day 1 implementation:** Build `HTTPTransport` only. Define the `Transport` abstract interface so `AgentCoreTransport` can slot in cleanly in Part 4. The interface is small — roughly 4-5 methods. Getting it right now saves the head-scratching later.

**AgentCore streaming detail (Part 4 concern, documenting now):**

AgentCore's `InvokeAgentRuntime` returns a streaming response. The question is: does it pass through our SSE stream verbatim, or does it wrap/transform it? Options:

1. **Pass-through:** AgentCore forwards the raw HTTP response from `/invocations` including SSE headers. Our CLI just reads the SSE stream as normal. This is the ideal case — `AgentCoreTransport` is thin.

2. **Wrapped:** AgentCore wraps the response in its own envelope (like Bedrock's `InvokeModelWithResponseStream` does with content blocks). The CLI needs to unwrap the AgentCore envelope and extract our SSE events. More work but well-precedented.

3. **Buffered:** AgentCore waits for the full response before returning. This would break streaming. Unlikely given AgentCore is designed for interactive agents, but needs verification.

**Action for Part 4:** Test which streaming model AgentCore uses before implementing `AgentCoreTransport`. This determines how much adaptation logic the transport needs.

**CLI invocation patterns across all three deployment modes:**

```bash
# ─── Day 1: Local development ───────────────────────────────
acw server                                    # Start server on 127.0.0.1:8080
acw connect                                   # Connect (no auth, localhost)

# ─── Day 2: Remote EC2/ECS ──────────────────────────────────
# On the server:
ACW_API_KEY=<secret> acw server --bind 0.0.0.0 --port 8080

# On the operator's laptop:
acw connect https://ec2-host:8080 --api-key <secret>
acw connect https://ec2-host:8080 --resume    # Resume existing session

# ─── Part 4: AgentCore ──────────────────────────────────────
# Container deployed to AgentCore (no changes to container)
# On the operator's laptop:
acw connect --agentcore --runtime-id abc-123 --region us-east-1

# Under the hood:
#   CLI creates AgentCoreTransport
#   AgentCoreTransport uses boto3:
#     client = boto3.client('bedrock-agentcore', region_name='us-east-1')
#     response = client.invoke_agent_runtime(
#         agentRuntimeId='abc-123',
#         payload=json.dumps({"session_id": "...", "message": "List S3 buckets"})
#     )
#   Response stream parsed into same 12 SSE event types
#   Rendering layer is identical — operator sees same spinners, tables, traces
```

---

## Documentation Impact Analysis

### Files That Need Updating

| File | Impact | What Changes |
|------|--------|-------------|
| **`README.md`** | Medium | Add "Remote Usage" section with `acw server` and `acw connect`. Update directory structure to show `cli/`. Keep existing content — local mode is unchanged. |
| **`CLAUDE.md`** | None | No changes. CLAUDE.md governs AWS interactions, which are identical regardless of whether the user is local or remote. The safety model doesn't know or care about the transport layer. |
| **`docs/DESIGN.md`** | Small | Update Tenet 10 wording from "UI-Consumes" to "Clients-Consume". Update the three-layer table to show Detachable CLI as a consumer alongside Web UI. Add brief note in Section 5 directory structure. |
| **`docs/PLAN-WEB-UI-AND-DEPLOYMENT.md`** | Medium | Part B: Add Detachable CLI as a consumer alongside Web UI. Note that Web UI is parked. Part C (EC2 deployment) unchanged — same container. Part D: Update doc changes table. Part E: Adjust phases (Phase 3 becomes CLI, not Web UI). |
| **`docs/BLOG-SERIES-ROADMAP.md`** | Medium | Part 3 Section 5: Change from "Web UI build" to "ACW Server + Detachable CLI build + EC2 deployment". The narrative arc is identical — "deploy yourself" — but the client is CLI not browser. |
| **`docs/RESEARCH-SDK-VS-SUBPROCESS.md`** | Small | Update the "Migration Path" section at the bottom. Currently says `./acw --server` starts FastAPI. Should match actual subcommand (`acw server`). |
| **`server/README.md`** | Small | Update "With Web UI" section to mention the detachable CLI as the primary consumer. Web UI section becomes secondary/optional. |
| **`web-ui/README.md`** | Small | Add a note at the top: "Status: Parked — the Detachable CLI is the current primary remote interface. This web UI remains a future deliverable." |
| **`config/deployment.md`** | None | Deployment manifest describes the container's application requirements. The container is the same regardless of whether the client is CLI or browser. |
| **`Dockerfile`** | Medium | Remove the web UI build stage (or make it optional with multi-stage build arg). The container becomes API-only. |
| **`docker-compose.yml`** | Small | Remove web UI service if present. Add note about using `acw connect` to interact with the containerized server. |

### Files That Do NOT Change

| File | Why No Change |
|------|--------------|
| `CLAUDE.md` | Safety model is transport-agnostic |
| `.claude/agents/*.md` | Agent definitions are the same |
| `.claude/commands/*.md` | Commands are the same |
| `skills/**` | Skills are files on disk, unchanged |
| `config/orchestration-config.md` | Orchestration thresholds are transport-agnostic |
| `config/environments/` | Environment classification is the same |
| `CLAUDE-DEVELOPMENT.md` | Development context for maintainers — unaffected by client layer changes |
| `server/core/sdk_client.py` | SDK client is the same — it doesn't know about the client |
| `server/core/session_manager.py` | Session management is the same |
| `server/core/event_stream.py` | SSE events are the same |
| `server/api/sessions.py` | Session endpoints are the same |
| `server/api/agentcore.py` | AgentCore protocol is the same |

This is the beauty of the architecture: **the core and the server are completely unaffected.** The pivot only adds a new consumer (detachable CLI) and parks an existing one (web UI).

---

## Implementation Phases (Updated)

The existing PLAN-WEB-UI-AND-DEPLOYMENT.md has 8 phases. Here's how they change:

| Phase | Current Plan | After Pivot | Change |
|-------|-------------|-------------|--------|
| 1 | Blog reorg | Blog reorg | No change |
| 2 | ACW Server (REST + SSE API) | ACW Server (REST + SSE API) | No change — server is the same |
| 3 | Web UI (React frontend) | **Detachable CLI** | Web UI → CLI. Build `cli/`, integrate into `acw`, polish REPL client |
| 4 | Container packaging | Container packaging | Simplified — no web UI build stage |
| 5 | Deployment command | Deployment command | `/aws-coworker-deploy` (not `-web-ui` suffix) |
| 6 | Self-deployment test | Self-deployment test | Same — deploy to EC2, capture for blog |
| 7 | Documentation | Documentation | Broader — covers CLI setup too |
| 8 | AgentCore (future) | AgentCore (future) | No change |

### Phase 3 Detail: Detachable CLI

1. Create `cli/` directory structure
2. Move `tools/repl_client.py` → `cli/acw_client.py` (or similar)
3. Add configurable server URL (env var + CLI flag)
4. Add session management commands (create, resume, list)
5. Add connection health/retry logic
6. Implement permission approval UX (inline Y/N prompt)
7. Update `acw` script with subcommand routing
8. Add `acw server` (starts FastAPI)
9. Add `acw connect [url]` (starts REPL client)
10. Test: local full stack (`acw server` + `acw connect` in separate terminals)
11. Test: remote (server on one machine, CLI on another)

---

## What This Means for AgentCore

Nothing changes for AgentCore. The container still:
- Implements `POST /invocations` + `GET /ping` on port 8080
- Runs the FastAPI server with Claude Agent SDK
- Includes all skills, commands, agents, CLAUDE.md
- Uses IAM roles for Bedrock model access

The only difference: instead of a browser tab connecting to the container, it's `acw connect https://your-agentcore-endpoint`. Same protocol. Same API. Different client.

This is actually **better** for AgentCore because:
- No static file serving needed (smaller container)
- CLI is more natural for infrastructure operators
- No browser security concerns (CORS, CSP)
- Works from bastion hosts, jump boxes, CI/CD pipelines

---

## What This Means for the Blog

Part 3 Section 5 narrative changes from "we built a web UI" to "we built a remote CLI." The story is:

1. We built the ACW Server (FastAPI wrapping the SDK) — same as before
2. We built a detachable CLI that connects to it — the remote interface
3. We deployed the server to EC2 using AWS Coworker itself — "deploy yourself"
4. We connected to the remote instance with `acw connect` — the payoff moment

The narrative arc is actually stronger: "We asked AWS Coworker to deploy itself. Then we connected to the deployed instance from our laptop — same CLI, same experience, different machine."

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| REPL client not mature enough | Low | Medium | Already has spinners, tables, markdown, sub-agents. Mostly needs polish. |
| Permission flow gaps | Medium | Medium | REPL client doesn't yet have permission approval UX. Needs implementation. |
| Blog timeline slip | Low | Low | Detachable CLI is simpler than web UI — less work, not more. |
| Web UI stakeholders disappointed | Low | Low | Web UI is parked, not cancelled. Server API is the same. |
| `acw` script complexity | Low | Low | Keep it simple — bash routes to Python. |

---

## Summary

The pivot is architecturally clean because:

1. **Core is untouched** — commands, skills, agents, CLAUDE.md, safety model — all identical
2. **Server is untouched** — REST + SSE API, session management, event streaming — all identical
3. **Only the client layer changes** — swap web UI (parked) for detachable CLI (promoted)
4. **Tenet 10 is strengthened** — "Clients-Consume" is more general than "UI-Consumes"
5. **Container simplifies** — no React build stage, smaller image
6. **Blog narrative improves** — remote CLI is more compelling for infrastructure audience

The detachable CLI is not a consolation prize for lacking a web UI. It's the *right* interface for the target audience (infrastructure engineers) and the deployment model (containers, AgentCore, bastion hosts). The web UI remains a future option — when we build it, the server API is already there.

---

**Next steps after approval:**
1. Confirm answers to clarifying questions (Q1–Q5)
2. Update `docs/PLAN-WEB-UI-AND-DEPLOYMENT.md` with Phase 3 changes
3. Begin Phase 3 implementation (CLI directory, `acw` subcommands, REPL client promotion)
