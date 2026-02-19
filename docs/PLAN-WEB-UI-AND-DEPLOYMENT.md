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

### Components

#### 1. Backend: FastAPI Wrapper

**Purpose:** Translate HTTP requests into Claude Agent SDK sessions.

**Key endpoints (AgentCore protocol contract):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/invocations` | POST | Unified API — routes requests to session/message handlers |
| `/ping` | GET | Health check — returns "Healthy" |
| `/sessions` | POST | Create new Claude session |
| `/sessions/{id}/messages` | POST | Send message to session |
| `/sessions/{id}/messages/stream` | POST | Send message with SSE streaming |
| `/sessions/{id}/status` | GET | Session status |
| `/sessions/{id}/history` | GET | Conversation history |

**Session management:**
- Map session IDs to Claude Agent SDK session instances
- Sessions persist for the lifetime of the server process (or configurable timeout)
- Each session has its own conversation context and working directory
- The SDK session has access to all AWS Coworker files (skills, commands, agents, CLAUDE.md)

**Claude Agent SDK integration:**
- Import the SDK directly (not subprocess)
- Configure tools: Read, Write, Edit, Bash, Glob, Grep, Task, TodoWrite
- Load CLAUDE.md as the system prompt
- Skills, commands, and agents are available via the filesystem — the SDK reads them the same way Claude Code does

**Key design decisions:**
- The FastAPI wrapper is thin — session management, HTTP translation, streaming
- All intelligence stays in the Claude Agent SDK + our skills/commands/agents
- The wrapper does NOT duplicate any governance logic — it delegates everything to the SDK session
- Implement the AgentCore protocol contract (`/invocations` + `/ping` on port 8080) from day one, so the same container works on EC2 now and AgentCore later

#### 2. Frontend: React Web UI

**Purpose:** Browser-based chat interface for interacting with AWS Coworker.

**Core features:**
- Chat interface with message history
- SSE streaming for real-time responses
- Session management (create, resume, list)
- File browser for workspace
- Permission approval UI (when the agent requests approval for mutations)
- Environment/profile indicator (which AWS profile and region are active)

**Technology:**
- React with Tailwind CSS
- No heavy dependencies — keep it lightweight
- Communicate with backend via REST API + SSE

**Nice-to-have (not MVP):**
- Cognito authentication (add when deploying for team use)
- S3 workspace persistence (add when deploying to AgentCore)
- GitHub OAuth (add when code repo access is needed)

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
- Set up `backend/` directory structure
- Implement core: server.py, session management, Claude Agent SDK integration
- Implement endpoints: `/invocations`, `/ping`, `/sessions`, `/messages`
- Implement SSE streaming
- Test locally with curl/httpie

### Phase 3: Frontend (React UI)
- Set up `frontend/` directory
- Build chat interface with streaming
- Session management UI
- Permission approval flow
- Build and serve from FastAPI

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

2. **Claude Agent SDK vs Claude Code subprocess** — The AWS sample uses the SDK directly. Should we also support running Claude Code CLI as a subprocess for users who prefer the CLI's full feature set? Recommendation: SDK first, subprocess as future option.

3. **Model access** — The deployed instance needs Bedrock model access (Opus for orchestrator, Haiku/Sonnet for sub-agents). Should the deployment command verify model access before deploying? Recommendation: yes, as a pre-flight check.

4. **Workspace persistence** — Where do session workspaces live on the EC2 instance? EBS volume? S3 sync? Recommendation: EBS for dev, S3 sync for prod.

5. **Cost** — t4g.micro is ~$6/month. Bedrock model invocations are the real cost. Should we add cost estimation to the deployment plan? Recommendation: yes, include estimated monthly cost.
