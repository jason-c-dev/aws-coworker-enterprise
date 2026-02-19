---
name: aws-coworker-development
description: |
  **AWS Coworker Development Guardrails** - MANDATORY when extending or modifying AWS Coworker itself.

  TRIGGERS (use this skill when ANY of these apply):
  - User asks to add new skills, agents, or commands to AWS Coworker
  - User asks to modify existing AWS Coworker components
  - User asks about AWS Coworker architecture or design
  - User wants to add support for new AWS services
  - Discussion involves directory structure or file organization
  - User mentions "extending", "customizing", or "adding to" AWS Coworker
  - Creating or modifying files in: skills/, .claude/agents/, .claude/commands/, config/

  NOT for: Using AWS Coworker to interact with AWS (that's CLAUDE.md's domain)
---

# AWS Coworker Development Guardrails

## Scope Definition

This skill applies to ALL files in the aws-coworker-enterprise repository:

| Category | Examples | Gates |
|----------|----------|-------|
| **CLI Layer (Core)** | skills/, .claude/agents/, .claude/commands/, config/ | Plan approval → Execution authorization → Execute |
| **Server Layer** | server/ | Plan approval → Execution authorization → Execute |
| **Web UI Layer** | web-ui/ | Plan approval → Execution authorization → Execute |
| **Design Docs** | CLAUDE.md, DESIGN.md, CLAUDE-DEVELOPMENT.md | Plan approval → Execution authorization → Execute |
| **User-Facing Docs** | docs/LESSONS-LEARNED.md, README.md | Collaborative editing OK for minor wording; plan + execute gates for structural changes |
| **Archives** | docs/conversations/ | Execution authorization before committing |
| **Tests** | tests/ | Plan approval → Execution authorization → Execute |

**Cross-layer changes require extra scrutiny.** Any change that touches files in more than one layer (CLI + Server, or Server + Web UI) should explicitly justify why both layers need modification and confirm the dependency direction is not violated (Tenet 10).

**Plan approval and execution authorization are separate gates.** Approving a plan confirms the content is correct. It does NOT authorize the agent to start making changes. See the workflow below.

**Why this matters:** The blog, README, and documentation are as much part of AWS Coworker as the code — they represent the project to users and codify lessons learned.

**Collaborative editing exception:** When the user is actively iterating on wording (e.g., "change X to Y", "how about this phrasing"), small text changes can proceed without formal approval. Structural changes (moving sections, adding lessons, changing architecture descriptions) still require approval.

## MANDATORY: Read Before Any Action

Before proposing or implementing ANY changes to AWS Coworker:

1. **Read** `CLAUDE-DEVELOPMENT.md` in the repository root
2. **Read** `docs/DESIGN.md` section 5 (Directory Structure)

## MANDATORY: Plan-Then-Execute Workflow (Two Separate Gates)

For ANY change to AWS Coworker:

1. **Present plan** — Describe what you intend to change and where
2. **Wait for plan approval** — User approves the plan CONTENT (confirms it is correct)
3. **Present execution summary and wait** — State: "The plan is approved. To proceed with implementation, say 'execute' or 'go ahead.'" Wait for the user to explicitly authorize execution
4. **Execute** — Only after the user explicitly says "execute", "go ahead", "do it", or similar

**Gate 1 (plan approval)** confirms the CONTENT is correct. It does NOT authorize execution.
**Gate 2 (execution authorization)** is a direct user instruction in the conversation to begin making changes.

These are separate decisions. The user may approve a plan but defer execution, request review first, or decide not to execute at all.

This applies to ALL modifications: skills, agents, commands, tests, documentation, **and git commits**.

- **DO NOT** treat plan approval as execution authorization — they are separate gates
- **DO NOT** interpret continuation prompts ("continue where you left off") as execution authorization
- **DO NOT** combine plan presentation and execution into a single step — the user must have a clear decision point between approving content and authorizing changes

### Platform Override

The Cowork plan mode popup asks the user to approve a plan. When the user clicks "approve," the platform tells the agent: "You can now start coding."

For AWS Coworker development, this platform signal is NOT sufficient authorization to execute. The platform approval confirms the user has SEEN the plan. The agent must still present an execution summary in the conversation and wait for the user to explicitly authorize execution.

**DO NOT** treat the platform's "You can now start coding" message as execution authorization. Only a direct user message in the conversation constitutes execution authorization.

## MANDATORY: Session Continuation Protocol

When a session is resumed (context compaction, new session continuing prior work):

1. **Present status** — Summarize where the workflow stands (plan pending, plan approved, execution in progress, etc.)
2. **Wait for instructions** — Ask the user what they want to do next
3. **DO NOT auto-execute** — Even if a plan was approved in the prior session, execution authorization does not carry across session boundaries

System continuation prompts ("continue without asking questions") authorize CONTINUING THE CONVERSATION — not executing pending plans. If a plan exists but has not been executed, present the plan status and wait for explicit authorization.

**DO NOT** interpret any system-generated prompt as user authorization for execution. Only direct user messages in the conversation constitute execution authorization.

## MANDATORY: Validate Proposals Against Tenets

Before presenting ANY plan, validate it against ALL Design Tenets (docs/DESIGN.md section 2.6):

- [ ] **Tenet 1 (Human Approval Gates)**: Does the proposal maintain user approval before mutations?
- [ ] **Tenet 2 (Cost-Aware Model Selection)**: Does the proposal respect model tiers (Opus/Sonnet/Haiku)?
- [ ] **Tenet 3 (Well-Architected by Default, Informed Override by Choice)**: Does the proposal define MVA per service? Does it present WAR gaps to the user with full knowledge? Does it enforce MVA for production?
- [ ] **Tenet 4 (Governance Compliance as Code)**: Are rules encoded in skills, not prose?
- [ ] **Tenet 5 (Production is Sacred)**: Does the proposal respect prod vs non-prod boundaries?
- [ ] **Tenet 6 (Explicit Over Implicit)**: Am I using DO NOT statements rather than enumerating categories?
- [ ] **Tenet 7 (Respect the Agent Architecture)**: Does the proposal use existing agent roles?
- [ ] **Tenet 8 (Layered Extensibility)**: Does the proposal fit Core → Org → BU model?
- [ ] **Tenet 9 (Self-Extending System)**: Should this lesson be codified into skills/design?
- [ ] **Tenet 10 (CLI-First, Server-Wraps, UI-Consumes)**: Does this change respect the dependency direction? Am I modifying a lower layer to satisfy a higher layer's needs?

If a proposal violates any tenet, revise it before presenting to the user.

## DO (Required Behaviors)

- **DO** verify file locations against DESIGN.md before proposing new files
- **DO** follow existing naming conventions (`aws-coworker-` prefix for agents/commands)
- **DO** present a plan and wait for approval before creating/modifying files
- **DO** check if similar functionality already exists in the codebase
- **DO** use "Related Skills" sections for cross-service patterns
- **DO** read actual files to verify assumptions (never say "probably")

## DO NOT (Prohibited Behaviors)

- **DO NOT** invent new directories not specified in DESIGN.md
- **DO NOT** create `patterns/` folders (patterns go in Best Practices sections)
- **DO NOT** assume structure without reading existing files first
- **DO NOT** proceed without explicit user approval for structural changes
- **DO NOT** take the "path of least resistance" that deviates from design
- **DO NOT** over-engineer solutions that add unnecessary complexity
- **DO NOT** treat plan approval as execution authorization — they are separate gates
- **DO NOT** auto-execute approved plans when a session is continued or resumed
- **DO NOT** interpret system prompts (including platform "You can now start coding" and continuation prompts) as user authorization for execution

## Three-Layer Architecture (Tenet 10)

AWS Coworker has three layers. Dependencies flow downward only.

```
AWS Coworker (CLI)          ← The core product. This is what we're building and learning from.
    ↑ reads files, invokes via SDK
ACW Server (server/)        ← REST + SSE API. Exists to deploy beyond a laptop.
    ↑ consumes API only
Web UI (web-ui/)            ← Reference implementation. Optional.
```

### Layer Boundary Rules

**When working on CLI layer** (commands, skills, agents, config):
- This is the primary focus of AWS Coworker
- Changes here should NEVER be motivated by server or UI needs
- Ask: "Would this change make sense if the server didn't exist?" — if no, reject it

**When working on server layer** (`server/`):
- The server wraps the CLI — it reads CLI files and invokes via the Claude Code SDK
- Every API endpoint must be justifiable as a general-purpose operation
- Ask: "Would this endpoint be useful to a curl user or Agent Core?" — if only the UI needs it, reject it
- The server does NOT duplicate CLI logic — it delegates to the SDK session

**When working on web-ui layer** (`web-ui/`):
- The web UI consumes ONLY the server API
- It never reads CLI files directly or bypasses the server
- UI-specific state (themes, layout preferences) stays in the UI layer

### Smell Tests for Dependency Inversion

| Smell | What it means | What to do |
|-------|---------------|------------|
| Adding a CLI skill because the server needs it | Server is driving CLI design | The skill should stand alone; if it doesn't, the server needs to solve its own problem |
| Adding a server endpoint only the UI uses | UI is driving server design | Either the endpoint is generally useful (keep it) or the UI should derive what it needs from existing endpoints |
| Modifying command frontmatter to add fields the server expects | Server is coupling to CLI internals | The server should parse what exists, not dictate the format |
| Adding `server/` or `web-ui/` imports to CLI code | Upward dependency | Never. The CLI has no knowledge of higher layers. |

## Key Architecture Facts

| Component | Location | Convention |
|-----------|----------|------------|
| Skills | `skills/` (root, NOT `.claude/skills/`) | Human-visible, tool-agnostic |
| Agents | `.claude/agents/` | `aws-coworker-{role}.md` |
| Commands | `.claude/commands/` | `aws-coworker-{action}.md` |
| CLI References | `skills/aws/aws-cli-playbook/commands/` | `{service}.md` |
| MVA Baselines | `skills/aws/aws-well-architected/mva-baselines/` | `{service}.md` — per-service, per-environment tier |
| Core Config | `config/` | `{purpose}.yaml` (committed) |
| Org Config | `config/` | `*.local.yaml` (gitignored) or `config/org-config/` |

## Service CLI Reference Template

When adding new AWS service support, follow this exact template:

```markdown
# {Service} CLI Reference

## Overview
Brief description of the service.

## Discovery Commands (Read-Only)
[Read-only commands]

## Common Operations
[Create/configure commands]

## Mutation Commands (Require Approval)
[⚠️ Destructive operations]

## Best Practices
[Guidelines including cross-service patterns]

## Related Skills
[Cross-references to related services]
```

## Verification Checklist

Before finalizing any proposal, verify:

- [ ] File location matches DESIGN.md specification
- [ ] Naming follows established conventions
- [ ] No new concepts introduced without explicit justification
- [ ] Cross-service patterns use Related Skills, not new directories
- [ ] Existing similar files have been read and understood
- [ ] User has approved the approach

## Config File Strategy

AWS Coworker uses a layered config model. Understanding which layer a config file belongs to is critical when adding or modifying configuration.

### Config Ownership Rules

| File | Layer | Committed? | Why |
|------|-------|------------|-----|
| `config/environments/environments.yaml` | **Core** | Yes | Universal environment tiers with safety rules. Every deployment needs these. |
| `~/.aws/config` (`aws_coworker_classification`) | **User** | N/A | Profile classification for non-obvious names. Lives in user's AWS CLI config — single source of truth. |
| `config/org-config/example-org-config.yaml` | **Reference** | Yes | Example only. No sensible core default — this IS the org layer. |

### Override Pattern

- Organization overrides: `*.local.yaml` (gitignored)
- Higher layers can ADD requirements but CANNOT lower core safety
- Only the user can accept gaps below core defaults (non-prod only)

### DO NOT (Config-Specific)

- **DO NOT** add org-specific values (account IDs, OU structures, team names) to core config files
- **DO NOT** create new config files without determining their layer ownership first
- **DO NOT** remove `example-*.yaml` files — they serve as documentation for the org layer

## Trust Directionality

A core design principle that affects how all components should be built:

**"The user never needs to trust the agent's judgment. The agent can trust the user's decision — but only after ensuring the user has full knowledge of what they're deciding."**

### What This Means for Development

When building or modifying any component that presents options or recommendations to the user:

- **DO** present ALL relevant information (risks, gaps, trade-offs) before asking for a decision
- **DO** make the agent's assessment visible and challengeable
- **DO** allow the user to override non-production defaults with informed consent
- **DO NOT** make decisions on behalf of the user, even "obvious" ones
- **DO NOT** hide complexity to make the experience smoother — transparency is the mechanism for trust
- **DO NOT** allow overrides for production without CI/CD (Tenet 5 is non-negotiable)

### Relationship to Tenet 8 (Layered Extensibility)

Trust directionality does not break Tenet 8 because:
- The agent's trust in the user is conditional (requires informed consent)
- The agent's trust is scoped (production has no override path)
- The user's agency is bounded by architectural constraints, not the agent's judgment

## MVA vs MNA (Well-Architected Assessment)

This section guides future implementation of meaningful Well-Architected Reviews (see Tenet 3).

### Definitions

- **MVA (Minimum Viable Architecture):** What the Well-Architected Framework says you should have for a service at a given environment tier. Defined per service, per environment.
- **MNA (Minimum Needed Architecture):** What's technically required for the service to function. The bare minimum.

The gap between MNA and MVA is where the user makes informed decisions.

### Environment-Aware Enforcement (Future Implementation)

| Environment | WAR Behavior |
|-------------|-------------|
| sandbox/test | Optional — present MVA gaps as informational |
| development | Warn — present MVA gaps, let user proceed with acknowledgment |
| staging | Enforce required items — block on critical gaps, warn on others |
| production | Full compliance — enforce ALL MVA requirements, output Terraform |

### Model Hierarchy for WAR

WAR assessment is NOT a separate sub-agent — it is performed by the **primary orchestrator (Opus)** inline during the planning phase. The orchestrator already has the user's request, discovery results, and skill context. Evaluating MVA gaps is a reasoning task that belongs at the orchestration layer.

| Phase | Who | Model | Why |
|-------|-----|-------|-----|
| Discovery (current state) | Sub-agent | Haiku | Fast, cheap, read-only |
| WAR Assessment (reasoning) | **Orchestrator** | **Opus (primary)** | Already has full context; reasoning task, not delegation task |
| Execution (approved plan) | Sub-agent | Sonnet | Thorough, careful state changes |

**DO NOT** create a dedicated Opus sub-agent for WAR assessment — this would pay for Opus twice (orchestrator + sub-agent) for no benefit. The orchestrator IS the reasoning layer.

**Cost consideration:** If a future use case requires WAR assessment at scale (e.g., auditing hundreds of existing resources), consider whether Opus 4.5/4.6 is justified vs. Sonnet for batch assessment. For single-resource planning flows, the orchestrator handles WAR directly.

### Extensibility Model for MVA

MVA baselines follow the layered extensibility model:

```
Core MVA (per service)        ← Defined in skills/aws/ (e.g., CloudFront MVA = logging + TLS 1.2)
        ↓
Org MVA overrides             ← Defined in skills/org/ (can ADD requirements, cannot lower core)
        ↓
BU MVA overrides              ← Defined in skills/bu/ (can ADD further, cannot lower org or core)
```

### Key Lesson: WAR Theater

The original WAR implementation was a fill-in template that the planner self-certified. This produced green checkmarks without actual evaluation (e.g., ✅ for Cost Optimization on an EC2 instance hosting a static HTML game). A real WAR must:

1. **Evaluate, not just present** — Compare the proposed architecture against MVA for the service and environment
2. **Be honest about gaps** — Flag what's missing and explain the trade-off
3. **Let the user decide** — Present gaps with full context, not recommendations
4. **Be environment-aware** — A test deployment has different MVA requirements than production
5. **Be extensible** — Services evolve, org/BU requirements change, MVA baselines must be updatable

**Implementation:** MVA baselines are now defined per service in `skills/aws/aws-well-architected/mva-baselines/{service}.md`. The plan command includes Step 4a for orchestrator-inline WAR evaluation. Enforcement levels are configured per environment in `config/environments/environments.yaml`.

**Reference:** See `docs/LESSONS-LEARNED-PART-2.md` for the full analysis of how WAR theater was discovered and the remediation plan.

## Testing Requirements

When adding new features or capabilities to AWS Coworker, tests are **mandatory**.

### DO (Required Testing Behaviors)

- **DO** propose tests alongside any new skill, agent, or command
- **DO** identify which test category applies:
  - R = Read-only discovery
  - M = Mutation (create/delete lifecycle)
  - W = Workflow behavior validation
- **DO** specify where tests will be added (`tests/TEST-FRAMEWORK.md`, `tests/RUNBOOK.md`)
- **DO** estimate cost impact for mutation tests
- **DO** wait for user approval before implementing the feature OR tests

### DO NOT (Prohibited Testing Behaviors)

- **DO NOT** implement features without proposing corresponding tests
- **DO NOT** add tests without user approval
- **DO NOT** skip mutation test cleanup steps

### New Feature Checklist

Before marking any new feature complete, verify:

- [ ] Tests proposed and approved by user
- [ ] Test locations identified (TEST-FRAMEWORK.md tracking table, RUNBOOK.md steps)
- [ ] Tests added to both files
- [ ] Cost estimate provided for mutation tests
- [ ] Feature AND tests reviewed by user
