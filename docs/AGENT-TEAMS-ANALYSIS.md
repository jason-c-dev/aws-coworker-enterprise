# Agent Teams Analysis: Why We Didn't Get Ahead of Our Skis

**Status:** Parked — revisit after remaining phases complete
**Date:** 2026-02-13
**Context:** Claude Code Agent Teams (experimental) — https://code.claude.com/docs/en/agent-teams
**Decision:** Continue with current sub-agent orchestration. Evaluate teams as a future additive feature.

---

## The Question

Claude Code introduced Agent Teams — independent agents with their own context windows, direct inter-agent messaging, and a shared task list. Should AWS Coworker adopt this instead of its current single-orchestrator + sub-agent model?

The idea: a Discovery agent, a WAR Assessor agent, a Planner agent, and an Executor agent — each independent, coordinating through markdown files (the messaging medium), with Opus as the Team Lead holding the approval gate.

The microservices analogy: our current architecture is an orchestrator pattern (saga coordinator). Agent Teams would enable choreography (event-driven, agents reacting to each other's outputs). The question is whether the benefits of choreography outweigh the costs for enterprise AWS management.

---

## Current Architecture (Orchestration)

```
User Request
    ↓
Core Agent (Opus) — single orchestrator
    ├── Spawns Planner (Haiku/Sonnet) via Task tool
    ├── Spawns Executor (Sonnet) via Task tool
    ├── Spawns Guardrail (Haiku) via Task tool
    └── Spawns Observability/Cost (Haiku) via Task tool
    ↓
Sub-agents report back → Orchestrator aggregates → User sees result
```

**Characteristics:**
- All decisions flow through the orchestrator
- Sub-agents are workers, not decision-makers
- State is centralized in the orchestrator's context
- Sub-agents have no context of each other's work
- Cost-efficient: Haiku/Sonnet sub-agents are lightweight

---

## Agent Teams Architecture (Choreography)

```
User Request
    ↓
Team Lead (Opus) — coordinator, not micromanager
    ├── Discovery Teammate (Haiku) — explores AWS infrastructure
    ├── WAR Assessor Teammate (Sonnet) — assesses Well-Architected compliance
    ├── Planner Teammate (Sonnet) — creates plans incorporating WAR findings
    └── Executor Teammate (Sonnet) — executes approved plans
    ↓
Teammates message each other directly
WAR challenges Planner's choices before plan reaches Lead
Lead holds approval gate — the HAL 9000 moment stays centralized
```

**Characteristics:**
- Teammates have full Claude sessions (own context windows)
- Direct inter-agent messaging (not just report-back)
- Parallel analysis with independent deep dives
- Higher token cost per interaction
- Experimental API — likely to change

---

## Where Teams Add Genuine Value

### 1. Separation of Concerns (No More Self-Grading)

The blog's central lesson — "grading its own homework" — is directly relevant. Currently, the orchestrator produces *both* the plan and the WAR assessment. With teams, the WAR agent independently challenges the Planner. That's genuine separation, not delegation.

### 2. Parallel Deep Analysis

For complex operations (multi-region audit, architecture review), Discovery, WAR, and Cost analysis can happen truly in parallel. Each agent maintains deep context in its domain rather than the orchestrator juggling everything.

### 3. Competing Hypotheses

For complex architectures, two Planner teammates could propose different approaches. The Lead selects the best one. This is impossible with the current single-planner sub-agent model.

### 4. Inter-Agent Debate

The WAR teammate could message the Planner directly: "You're proposing unencrypted S3 in staging — that's BLOCKED." This happens *before* the plan reaches the user, producing better first-draft plans.

---

## Where Teams Hurt (Or Don't Help)

### 1. Cost

Each teammate is a full Claude session. The current model is deliberately cheap — Haiku discovery, Sonnet mutations, results summarized back. For "list my S3 buckets" (the majority of interactions), teams are massive overkill.

### 2. The HAL 9000 Moment Requires Centralized State

Staging enforcement (the W9 test) requires the approval gate to know: what was requested, what was blocked, what the user tried to bypass, and what the legitimate options are. That context must be centralized. The Lead pattern solves this, but you must be deliberate — the Lead is *always* the final gate.

### 3. Session Resumption is Broken

The docs state `/resume` doesn't restore teammates. For enterprise use where you step away mid-plan, that's a real problem.

### 4. It's Experimental

Disabled by default. API likely to change. Building on it now means potential rewrites when it stabilises.

### 5. File Conflicts

Multiple teammates editing shared files (plan.md, execution logs) creates coordination challenges. Read-only access to skills/config is fine; shared mutable state is not.

### 6. Simple Queries Don't Need a Team

"What EC2 instances are running?" → single Haiku sub-agent. Done. No team coordination overhead justified.

---

## The Decision

**Continue with the current sub-agent orchestration for all remaining phases.**

The architecture is proven (W9 video demonstrates it working). The safety model is enforced. The cost model is efficient. The remaining AWS services (VPC, IAM, RDS, Lambda, etc.) don't require architectural changes — they need skills, MVA baselines, and command coverage.

**Evaluate Agent Teams as a future additive feature when:**
1. The API graduates from experimental
2. Session resumption with teammates works
3. We've completed the foundation (all core AWS services covered)
4. We have complex multi-account, multi-region use cases to benchmark against

---

## The Implementation Path (When Ready)

This is NOT a rewrite. It's an alternative execution strategy that reuses ~90% of existing components.

### What doesn't change:
- Agent definitions (planner, executor, guardrail, observability-cost)
- Skills library
- Slash commands
- CLAUDE.md routing
- Safety model enforcement points
- Config layers (environments, profiles, org-config)
- Model hierarchy philosophy (Opus thinks, Haiku discovers, Sonnet mutates)

### What changes:
- Orchestration-config.md gains an `execution_strategy` option
- Core Agent gains the ability to spawn teammates instead of sub-agents
- Inter-agent communication via structured markdown files (plan.md, war-assessment.md)
- Lead always holds the approval gate (non-negotiable)

### Proposed config addition:
```yaml
execution_strategy:
  default: sub-agents          # Current behaviour — cost-efficient
  advanced: agent-teams        # When scope warrants it
  threshold_trigger: parallel  # Use teams when parallel thresholds exceeded
```

Simple queries stay on sub-agents. Complex operations escalate to teams. Same agents, same safety model, different coordination mechanism.

---

## The Markdown-as-Messaging Pattern

One idea worth adopting *now* (independent of Agent Teams): structured markdown files as the communication medium between agents.

```
.claude/workspace/
├── current-plan.md          # Planner writes, WAR reviews, Lead approves
├── war-assessment.md        # WAR agent writes, Planner consumes
├── execution-log.md         # Executor writes, Lead monitors
└── discovery-findings.md    # Discovery writes, all consume
```

This creates an audit trail, is human-readable, decouples agents, and makes the future transition to teams smoother. Whether sub-agents or teammates produce these files is an implementation detail.

---

## Blog Part 3 Notes

**Working title:** "Why We Didn't Get Ahead of Our Skis"

**Key narrative points:**

1. **We considered Agent Teams seriously.** This isn't ignorance of the new capability — it's a deliberate architectural decision.

2. **The microservices parallel.** Orchestration vs choreography is a well-understood trade-off. We chose orchestration for the same reasons early microservices teams do: simplicity, predictability, centralized enforcement. Choreography comes later when the foundation is solid and the coordination patterns are proven.

3. **The HAL 9000 moment demands centralized state.** The staging enforcement gate — the feature we're most proud of — requires the orchestrator to hold the full context of what was approved, rejected, and attempted. Distributing that across teammates introduces risk we're not ready to take.

4. **Cost governance matters.** We built AWS Coworker to help enterprises manage costs (among other things). Introducing a more expensive execution model for simple queries would be ironic.

5. **It's additive, not disruptive.** The existing architecture is the foundation. Teams are an advanced mode for specific use cases. When the time comes, ~90% of the work carries forward unchanged.

6. **Social media is excited. We're cautious.** New capabilities are exciting. But enterprise infrastructure management rewards caution over novelty. We'd rather ship a proven orchestrator today than an experimental choreographer tomorrow.

---

*This document is part of the AWS Coworker repository and will be expanded into a blog post (Lessons Learned Part 3) after the remaining phases are complete.*
