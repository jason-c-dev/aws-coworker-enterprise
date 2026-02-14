# Blog Series Roadmap: AWS Coworker Lessons Learned

**Purpose:** Keep us (Jason and Claude) aligned on what each blog covers, what must be built before we write about it, and what belongs in which part. This is a living document — update it as we go.

**Guiding principle:** We write about what we've built and experienced. Not the art of the possible. Every lesson, every feature, every architectural decision described in the blog must be backed by real implementation and real testing. The reader gets our true experience, not speculation.

---

## Part 1: Complete ✅

**Title:** "I Used Claude Cowork to Build a Claude Code Agent for AWS. Here's What Broke"

**Published:** Yes (Medium)

**What it covers:**
- Building AWS Coworker from scratch with Claude Cowork
- Sub-agent architecture (Opus orchestrator, Haiku/Sonnet workers)
- 7 lessons learned (sub-agent delegation, permission context, model selection, auto-update chaos, etc.)
- 9 design tenets
- The retro arcade game incident (agent generated its own game instead of deploying the file)

**Source files:**
- `docs/LESSONS-LEARNED.md` (raw)
- `docs/LESSONS-LEARNED-MEDIUM.md` (Medium-formatted)

---

## Part 2: Complete ✅ (writing in progress)

**Title:** "The Theater of WAR: How Our Well-Architected Review Was Grading Its Own Homework"

**What it covers:**
- The WAR was theater — self-certified green checkmarks
- MVA vs MNA concept (Minimum Viable Architecture vs Minimum Needed Architecture)
- Trust directionality (asymmetric trust model)
- Batteries-included was a lie (config files all prefixed with `example-`)
- Model hierarchy for WAR assessment
- Extensibility of MVA baselines (Core → Org → BU layering)
- Emergent behavior (agent improvised statuses, both good and bad)
- The HAL 9000 moment (staging enforcement gate, pushback resistance)
- Two-context status model (Planning: REMEDIATE/ACCEPTABLE/BLOCKED vs Review: PASS/FAIL)

**Implementation backing (all built and tested):**
- MVA baselines: S3, EC2, CloudFront (Phase 1), RDS, Lambda (Phase 2), VPC, IAM, ECS, EKS (Phase 3)
- Environment-aware enforcement (sandbox → dev → staging → production)
- Service appropriateness checks
- 35 tests across R1-R14, M1-M14, W1-W14 (Phases 1-2 tested, Phase 3 testing in progress)
- Launcher renamed to `acw`

**Source files:**
- `docs/LESSONS-LEARNED-SKELETON.md` (outline)
- `docs/LESSONS-LEARNED-PART-2.md` (full draft)
- `docs/LESSONS-LEARNED-PART-2-MEDIUM.md` (Medium-formatted)

**Still needed before Part 2 is final:**
- [ ] Complete Phase 3 testing (R13, R14, M12, M13, M14, W13, W14)
- [ ] Fix any bugs found during Phase 3 testing
- [ ] Record "HAL 9000 social engineering" video for blog/GitHub Pages embed
  - Scenario: W9 (S3 staging, no encryption → BLOCKED)
  - Escalation: polite request → "I'm the owner" → "I'm Dario Amodei" → Trainium2 bribe → P5 bribe → fix the architecture (immediately proceeds)
  - Punchline: the only thing that works is compliance, not authority or silicon
  - Format: YouTube/Vimeo embed for Medium, gif for GitHub Pages README
  - Keep under 2 minutes
  - Complements existing W9 demo gif (that one shows the gate working; this one shows it resisting social engineering)
- [ ] Final draft review and polish

---

## Part 3: Planning 📋

**Working title:** "From Admin Keys to Agent Roles: Least Privilege and the Road to Self-Deployment"

**Guiding constraint:** Only write about what we've built. Part 3 must be backed by real implementation.

### Topics to Cover

#### 1. Agent Teams: Why We Didn't Get Ahead of Our Skis
- We considered Agent Teams seriously and made a deliberate architectural decision to wait
- The microservices parallel (orchestration vs choreography)
- The HAL 9000 moment demands centralised state
- Cost governance matters — expensive execution for simple queries is ironic
- It's additive, not disruptive — ~90% of existing work carries forward
- **Source:** `docs/AGENT-TEAMS-ANALYSIS.md` (already written)
- **Implementation required:** None — this is a design decision record

#### 2. The Credentials Problem: From Shared Admin to Scoped Roles
- Current state: all agents (Opus, Haiku, Sonnet) authenticate with the same admin access key
- Why this is wrong: a discovery agent that can also delete resources, a mutation agent with read access to everything
- The M14 test: creating a read-only IAM user as a stepping stone
- IAM MVA baseline enforcement (wildcard permissions = Critical, no inline policies = High)
- **Implementation required:**
  - [ ] Complete M14 testing (IAM read-only user create/delete lifecycle)
  - [ ] Complete W14 testing (wildcard permission audit)
  - [ ] Document the scoped IAM role design for discovery vs mutation agents
  - [ ] (Stretch) Implement and test running Haiku sub-agents with a read-only IAM role

#### 3. Phase 3 Wrap-Up: VPC, IAM, ECS, EKS
- Service-agnostic architecture proven across 10 services
- Infrastructure services (VPC, IAM) as foundational constructs other services depend on
- Container services (ECS, EKS) with service appropriateness warnings
- The test results and any lessons from Phase 3 testing
- **Implementation required:**
  - [ ] Complete all Phase 3 tests (R13, R14, M12, M13, M14, W13, W14)
  - [ ] Fix any bugs and recommit

#### 4. Looking Ahead: The Inception Moment (Teaser Only)
- AWS Coworker deploying itself — the concept
- Brief introduction to Bedrock AgentCore as the target platform
- Why the safety model is deployment-agnostic
- **NOT a how-to guide** — that's Part 4
- This section sets up the narrative: "we've built the foundation, now we're going to deploy it"
- **Implementation required:** None — this is a teaser, not a build report

### What Part 3 Does NOT Cover
- Actually implementing Agent Teams (parallel track — see below)
- Actually deploying to Bedrock AgentCore (parallel track — see below)
- AgentCore Policy, Memory, Gateway deep dives
- Cedar policy generation from MVA baselines

---

## Parts 4 & 5: Parallel Tracks 🔮

**Critical design decision:** Agent Teams and Bedrock AgentCore are **parallel tracks, not sequential dependencies.** Neither blocks the other. We pursue whichever is ready first, or both concurrently.

**Why parallel:** Agent Teams changes the *coordination model* (how agents talk to each other). AgentCore changes the *deployment model* (where agents run). These are independent concerns. The current sub-agent model deploys to AgentCore perfectly well without Agent Teams. And Agent Teams can be built and tested locally without AgentCore. Coupling them would mean an experimental API (Agent Teams) gates a production deployment platform (AgentCore), which is backwards.

**Numbering:** Whichever track produces a blog post first becomes "Part 4." The other becomes "Part 5." We don't know the order yet, and that's fine.

---

### Track A: Agent Teams 🔮

**Working title:** "Agent Teams: From Orchestration to Choreography" (tentative)

**Guiding constraint:** Build it first, write about it after.

**Dependency:** Claude Code Agent Teams API must be stable enough to build on. If it remains experimental and unstable, this track may be deferred indefinitely. The blog series is complete without it — Agent Teams is an enhancement, not a requirement.

**Does NOT block:** Bedrock AgentCore deployment. The current sub-agent model works on AgentCore.

#### Topics to Cover (Subject to Change Based on What We Actually Build)

##### 1. Building Agent Teams Locally
- The Team Lead pattern: Opus as coordinator, not micromanager
- Discovery Teammate (Haiku): independent AWS exploration with its own context window
- WAR Assessor Teammate (Sonnet): independent architecture review that challenges the Planner
- Planner Teammate (Sonnet): creates plans incorporating WAR findings
- Executor Teammate (Sonnet): executes approved plans
- The Lead always holds the approval gate — the HAL 9000 moment stays centralised

##### 2. The Separation of Concerns Victory
- The "grading its own homework" problem (Part 2) finally solved structurally
- WAR Assessor independently challenges the Planner before the plan reaches the Lead
- Inter-agent debate produces better first-draft plans
- Real test results showing improved plan quality (or not — honest reporting)

##### 3. The Markdown-as-Messaging Pattern
- Structured markdown files as the communication medium between agents
- `current-plan.md`, `war-assessment.md`, `execution-log.md`, `discovery-findings.md`
- Audit trail, human-readable, decoupled agents
- How this pattern maps to A2A protocol later (but we're NOT building A2A yet)

##### 4. Cost and Performance Comparison
- Side-by-side: sub-agent model vs Agent Teams for the same operations
- Simple queries (discovery): cost overhead justified or not?
- Complex operations (multi-service plan): quality improvement worth the cost?
- Where the crossover point is — when do teams earn their keep?

##### 5. What Broke (Because Something Will)
- Session resumption issues
- File conflict coordination
- Any emergent behavior (good or bad)
- Honest assessment: is this actually better for our use case?

#### Implementation Required (Before Writing Track A)
- [ ] Agent Teams API must be stable (or we make a deliberate choice to build on experimental)
- [ ] Implement Team Lead pattern with Discovery, WAR Assessor, Planner, Executor teammates
- [ ] Implement markdown-as-messaging workspace
- [ ] Run existing test suite (at minimum: R1, M1, W7, W9) using Agent Teams
- [ ] Compare results and cost against sub-agent model
- [ ] Document what worked and what didn't

---

### Track B: Bedrock AgentCore 🔮

**Working title:** "The Inception: AWS Coworker Deploys Itself to Bedrock AgentCore"

**Guiding constraint:** Build it first, write about it after.

**Dependency:** None beyond Part 3 (credentials/least-privilege). The current sub-agent model deploys to AgentCore as-is. Agent Teams is a nice-to-have enhancement for the AgentCore deployment, not a prerequisite.

**Does NOT require:** Agent Teams. If Track A is complete when we reach this point, we deploy with Agent Teams. If not, we deploy the current sub-agent model. Both paths produce a valid, interesting blog post.

#### Topics to Cover (Subject to Change Based on What We Actually Build)

##### 1. Bedrock AgentCore Deep Dive
- AgentCore Runtime: Firecracker MicroVMs, session isolation, serverless hosting
- AgentCore Identity: per-agent IAM roles, SSO integration (Cognito, Entra, Okta)
- AgentCore Gateway: AWS APIs as MCP-compatible tools
- AgentCore Policy: Cedar policies for fine-grained tool call interception
- AgentCore Memory: cross-session learning, episodic memory
- A2A protocol: Agent-to-Agent communication (if Agent Teams was built in Track A)

##### 2. The Deployment
- AWS Coworker plans its own AgentCore deployment
- Docker container with Claude Agent SDK + CLAUDE_CODE_USE_BEDROCK=1
- Skills and MVA baselines baked into container as filesystem artifacts
- AgentCore Identity replaces shared admin access keys
- Discovery agents get read-only IAM roles, mutation agents get scoped write roles

##### 3. Safety Model → Infrastructure Policy
- MVA baselines → Cedar policies (the conceptual mapping)
- Governance guardrails → AgentCore Policy rules
- Enforcement gates → structural enforcement (IAM denies what the safety model advises against)
- The shift from advisory to structural enforcement

##### 4. Agent Teams on AgentCore via A2A (only if Track A completed first)
- How the local Agent Teams patterns map to AgentCore's A2A protocol
- Per-agent MicroVMs with per-agent IAM (hardware-level separation of concerns)
- Discovery teammate can't mutate because its MicroVM's role doesn't permit it
- Cost comparison: local Agent Teams vs AgentCore Agent Teams vs sub-agent model

##### 5. The Full Inception
- AWS Coworker (running locally) deploys AWS Coworker (to AgentCore)
- The deployed version manages the AWS infrastructure it was deployed into
- The Cedar policies that govern it were generated from the MVA baselines it uses
- The IAM roles that constrain it were planned by AWS Coworker's planner

#### Implementation Required (Before Writing Track B)
- [ ] Create Bedrock/AgentCore MVA baseline
- [ ] Build the Docker container with Claude Agent SDK + AWS Coworker skills
- [ ] Deploy to AgentCore Runtime (at minimum: a working agent that can do discovery)
- [ ] Configure AgentCore Identity with scoped IAM roles
- [ ] Configure AgentCore Gateway for at least S3 + EC2 + IAM operations
- [ ] Write Cedar policies derived from at least one MVA baseline
- [ ] Test the deployed agent (basic discovery, plan+cancel, enforcement gate)
- [ ] (If Track A completed) Deploy Agent Teams via A2A protocol on AgentCore

---

## Blog Series Principles

1. **Build first, write after.** Every feature described in a blog post must have been implemented, tested, and committed before we write about it. No "we plan to" or "in future we could" for core content. Teasers for the next post are the only exception.

2. **Real experience, not speculation.** The value of this series is that we share what actually happened — including the bugs, the wrong turns, the things that didn't work. If we speculate about how something might work without building it, we say so explicitly and keep it short.

3. **Each post stands alone.** A reader should be able to read any single post and get value. Forward references ("we'll cover this in Part 4") are fine for teasers, but the core content of each post must be self-contained.

4. **Lessons are the headline.** The blog is called "Lessons Learned" not "Features Shipped." The implementation is the vehicle for the lessons, not the other way around. Every section should answer: "what did we learn, and why does it matter?"

5. **Keep the human in the loop.** The blog is co-authored by Jason and Claude. Both perspectives matter. Jason brings the enterprise AWS experience and editorial voice. Claude brings the implementation and the meta-perspective of being the system that's also the subject of the blog.

---

## Quick Reference: What's Built vs What's Planned

| Component | Status | Blog Part |
|-----------|--------|-----------|
| Sub-agent architecture | ✅ Built & tested | Part 1 |
| WAR theater fix (MVA baselines) | ✅ Built & tested | Part 2 |
| Environment-aware enforcement | ✅ Built & tested | Part 2 |
| Service appropriateness checks | ✅ Built & tested | Part 2 |
| Phase 1 services (S3, EC2, CF) | ✅ Built & tested | Part 2 |
| Phase 2 services (RDS, Lambda) | ✅ Built & tested | Part 2 |
| Phase 3 services (VPC, IAM, ECS, EKS) | ✅ Built, testing in progress | Part 2/3 |
| Agent Teams analysis | ✅ Decision documented | Part 3 |
| IAM read-only user (M14) | ⬜ Testing pending | Part 3 |
| Scoped IAM roles for agents | ⬜ Not started | Part 3 |
| Agent Teams locally (laptop) | ⬜ Not started (API dependency) | Track A |
| Markdown-as-messaging workspace | ⬜ Not started | Track A |
| Agent Teams cost/quality comparison | ⬜ Not started | Track A |
| Bedrock AgentCore deployment | ⬜ Not started | Track B |
| AgentCore Identity integration | ⬜ Not started | Track B |
| AgentCore Gateway for AWS APIs | ⬜ Not started | Track B |
| Cedar policies from MVA baselines | ⬜ Not started | Track B |
| Agent Teams on AgentCore (A2A) | ⬜ Not started | Track B (if Track A done) |

---

*This document tracks the blog series roadmap. Update it as implementation progresses and plans evolve.*
*Last updated: 2026-02-14*
