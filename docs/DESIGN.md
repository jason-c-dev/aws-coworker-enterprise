# AWS Coworker Design Document

**Version:** 1.0.0-draft
**Status:** Draft - Awaiting Approval
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Design Principles](#2-design-principles)
3. [Architecture Overview](#3-architecture-overview)
4. [Conceptual Layers](#4-conceptual-layers)
5. [Directory Structure & Naming Conventions](#5-directory-structure--naming-conventions)
6. [Governance Model](#6-governance-model)
7. [AWS Interaction Model](#7-aws-interaction-model)
8. [Extensibility & Evolution Model](#8-extensibility--evolution-model)
9. [Documentation Model](#9-documentation-model)
10. [Security & Compliance](#10-security--compliance)
11. [Reference Library Specifications](#11-reference-library-specifications)
12. [Implementation Phases](#12-implementation-phases)

---

## 1. Executive Summary

**AWS Coworker** is a batteries-included, fully extensible meta-system of agents, skills, and slash commands designed for enterprise AWS interaction. It provides:

- **A reference library** of agents, skills, and workflows for safe, effective AWS operations
- **A meta-layer** enabling self-evolution through meta-agents, meta-skills, and meta-commands
- **GitOps-native governance** with human approval, audit trails, and rollback capabilities
- **Enterprise-grade flexibility** supporting single-account through complex multi-account Organizations

AWS Coworker is **not** an application architecture framework—it is a platform for *interacting with AWS* safely and consistently across diverse organizational contexts.

### Key Characteristics

| Attribute | Description |
|-----------|-------------|
| **Target Users** | Platform engineers, DevOps teams, cloud architects, SREs |
| **AWS Scope** | Any AWS estate: single account → multi-account with Organizations/Control Tower |
| **Governance** | Git/GitHub-managed with PR-based change control |
| **Extensibility** | Layered design: Core → Org → BU/Tenant overlays |
| **Safety Model** | Read-first, plan-before-execute, explicit approval for mutations |

---

## 2. Design Principles

### 2.1 Safety First

1. **Read-only by default** — Discovery and planning operations require no special approval
2. **Explicit confirmation for mutations** — Destructive or state-changing operations require human approval
3. **Blast radius awareness** — Every plan must articulate scope and potential impact
4. **Rollback-ready** — Every execution plan includes rollback procedures

### 2.2 AWS Well-Architected Alignment

All agents, skills, and workflows align with the six pillars:

| Pillar | AWS Coworker Alignment |
|--------|------------------------|
| **Operational Excellence** | Automation, IaC-first, runbook-driven operations |
| **Security** | Least-privilege IAM, encryption defaults, audit logging |
| **Reliability** | Multi-AZ awareness, backup validation, DR planning |
| **Performance Efficiency** | Right-sizing recommendations, resource optimization |
| **Cost Optimization** | Cost-aware planning, budget integration, waste detection |
| **Sustainability** | Efficient resource utilization, idle resource identification |

### 2.3 GitOps Native

1. **Everything as code** — Agents, skills, commands, and configuration are version-controlled
2. **Branch-based changes** — All modifications via feature branches and pull requests
3. **Human review required** — No silent mutations to production definitions
4. **Revertible baselines** — Tagged releases enable rollback to known-good states

### 2.4 Layered Extensibility

```
┌─────────────────────────────────────────────────────────────┐
│                    BU/Tenant Layer                          │
│         (Business unit or tenant-specific overlays)         │
├─────────────────────────────────────────────────────────────┤
│                    Organization Layer                       │
│         (Org-specific policies, patterns, naming)           │
├─────────────────────────────────────────────────────────────┤
│                    Core/Base Layer                          │
│     (Batteries-included library - generic, universal)       │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 Progressive Disclosure

- **Simple tasks stay simple** — Common operations don't require deep configuration
- **Advanced capabilities available** — Complex governance, multi-tenancy when needed
- **Graceful degradation** — Works with minimal setup, improves with configuration

---

## 3. Architecture Overview

### 3.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Coworker                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         SLASH COMMANDS                              │    │
│  │                      (Workflow Orchestration)                       │    │
│  │  /aws-coworker-plan-interaction    /aws-coworker-execute-nonprod    │    │
│  │  /aws-coworker-prepare-prod-change /aws-coworker-rollback-change    │    │
│  │  /aws-coworker-bootstrap-account   /aws-coworker-audit-library      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           AGENTS                                    │    │
│  │                      (Execution Roles)                              │    │
│  │                                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │    Core     │  │   Planner   │  │  Executor   │  │ Guardrail  │  │    │
│  │  │   Agent     │  │  Subagent   │  │  Subagent   │  │  Subagent  │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────┐   │    │
│  │  │ Observability/Cost  │  │        Meta-Designer Agent          │   │    │
│  │  │     Subagent        │  │     (Self-evolution & maintenance)  │   │    │
│  │  └─────────────────────┘  └─────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           SKILLS                                    │    │
│  │                    (Policy & Patterns)                              │    │
│  │                                                                     │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │   skills/aws/  │  │  skills/org/   │  │     skills/meta/       │ │    │
│  │  │  CLI Playbook  │  │  Org Strategy  │  │   Skill Designer       │ │    │
│  │  │Well-Architected│  │   Guardrails   │  │   Command Designer     │ │    │
│  │  │  Observability │  │                │  │   Audit Library        │ │    │
│  │  │ Cost Optimizer │  │                │  │                        │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  │                                                                     │    │
│  │  ┌────────────────────────────────────────────────────────────────┐ │    │
│  │  │                      skills/core/                              │ │    │
│  │  │        (Non-AWS core skills: Git, documentation, etc.)         │ │    │
│  │  └────────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AWS CLI / IaC                                   │
│           (Terraform, CDK, CloudFormation, native AWS CLI)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Interaction Flow

```
User Request (free-form or explicit command)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE.md Interception                      │
│        (All AWS requests routed through commands)               │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Slash Command  │────▶│   Core Agent    │────▶│     Skills      │
│   (Workflow)    │     │  (Orchestrator) │     │(Policy/Patterns)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Discovery    │
                        │ + Scope Estimate│
                        └─────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
     ┌─────────────────┐               ┌─────────────────┐
     │  Simple Task    │               │  Complex Task   │
     │  (< 50 resources│               │  (> 50 resources│
     │   single region)│               │   multi-region) │
     └────────┬────────┘               └────────┬────────┘
              │                                 │
              │                                 ▼
              │                        ┌─────────────────┐
              │                        │ User Advisement │
              │                        │ (time estimate) │
              │                        └────────┬────────┘
              │                                 │
              │                                 ▼
              │                        ┌─────────────────┐
              │                        │ Parallel Agents │
              │                        │ (see §3.3)      │
              │                        └────────┬────────┘
              │                                 │
              └────────────────┬────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │    Guardrail    │
                        │   Validation    │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Human Approval │
                        │  (if mutation)  │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Execution     │
                        │ (AWS CLI / IaC) │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Aggregation   │
                        │ (if parallel)   │
                        └─────────────────┘
```

### 3.3 Agent Orchestration Architecture

AWS Coworker supports multi-agent orchestration for complex, long-running tasks. The primary Claude instance (Core Agent) acts as the gatekeeper and orchestrator, delegating work to specialized sub-agents when appropriate.

#### Orchestration Model

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PRIMARY CLAUDE (Core Agent)                             │
│                         [Gatekeeper & Orchestrator]                         │
│                                                                             │
│  • Intercepts all requests via CLAUDE.md                                    │
│  • Routes through commands                                                  │
│  • Performs discovery to assess scope                                       │
│  • Estimates complexity and time                                            │
│  • Requests explicit user approval                                          │
│  • Delegates to sub-agents when beneficial                                  │
│  • Aggregates results into coherent response                                │
└─────────────────────────────────────────────────────────────────────────────┘
     │                                    │
     │ (Simple tasks)                     │ (Complex tasks - after approval)
     │                                    │
     ▼                                    ▼
┌──────────────────┐     ┌────────────────────────────────────────────────────┐
│ Direct Execution │     │              TASK DELEGATION                       │
│  (single-thread) │     │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
└──────────────────┘     │  │ Sub-Agent 1 │ │ Sub-Agent 2 │ │ Sub-Agent N │   │
                         │  │ (Region A)  │ │ (Region B)  │ │ (Account X) │   │
                         │  └─────────────┘ └─────────────┘ └─────────────┘   │
                         │         │               │               │          │
                         │         └───────────────┴───────────────┘          │
                         │                         │                          │
                         │                         ▼                          │
                         │              ┌─────────────────────┐               │
                         │              │  Result Aggregation │               │
                         │              └─────────────────────┘               │
                         └────────────────────────────────────────────────────┘
```

#### When to Use Multi-Agent Orchestration

| Scenario | Single Agent | Multi-Agent Swarm |
|----------|--------------|-------------------|
| List S3 buckets (1 region) | ✅ Appropriate | Overkill |
| Start/stop single instance | ✅ Appropriate | Overkill |
| Audit compliance across 10+ accounts | Slow | ✅ Parallel per account |
| Cost analysis across all regions | Sequential | ✅ Parallel per region |
| Security group audit across VPCs | Sequential | ✅ Parallel per VPC |
| Tagging remediation (100s of resources) | Very slow | ✅ Batched parallel |

#### Scope Estimation and User Advisement

During discovery, the Core Agent estimates task complexity:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCOPE ESTIMATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Discovery reveals:                                                         │
│  • 847 S3 buckets across 3 regions                                          │
│  • Estimated audit time: 8-10 minutes                                       │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ This audit will take approximately 8-10 minutes due to the number      │ │
│  │ of resources. I'll work in parallel across regions to minimize time.   │ │
│  │                                                                        │ │
│  │ Do you want to proceed? (yes/no)                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Permission Delegation Model

When sub-agents are spawned, the Core Agent delegates permission context:

```yaml
delegation_context:
  approved_by: user          # User explicitly approved this operation
  approval_scope: "Audit all S3 buckets for public access"
  operation_type: read-only  # or: mutation (with constraints)
  constraints:
    - No modifications permitted
    - Report findings only
  timeout: 600s              # Maximum execution time

# Sub-agent receives:
"User has approved: Audit all S3 buckets for public access.
 You have permission to perform read-only discovery on S3.
 Report your findings; do not modify any resources."
```

#### Aggregation and Response

After all sub-agents complete, the Core Agent:

1. **Waits** for all parallel tasks to complete
2. **Collates** results from all sub-agents
3. **Deduplicates** overlapping findings
4. **Synthesizes** a coherent summary
5. **Presents** unified results to the user

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGGREGATED RESULTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Audit complete across 3 regions in 8 minutes 23 seconds.                   │
│                                                                             │
│  Summary:                                                                   │
│  • 847 buckets scanned                                                      │
│  • 12 have public access (see details)                                      │
│  • 3 have misconfigured policies                                            │
│  • 832 are properly secured                                                 │
│                                                                             │
│  [Detailed findings by region...]                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Technical Implementation

Sub-agents are spawned using the **Task tool** with specific parameters:

```yaml
task_invocation:
  subagent_type: "general-purpose"  # or specialized type
  prompt: |
    You are acting as aws-coworker-planner for region us-east-1.

    Context:
    - User approved: "Audit S3 buckets for public access"
    - Profile: dev-admin
    - Region: us-east-1
    - Permission: Read-only discovery

    Task:
    1. List all S3 buckets in this region
    2. Check each bucket's public access configuration
    3. Report any buckets with public access

    Return your findings in structured format.
  model: "haiku"  # Use efficient model for parallel tasks
```

---

## 4. Conceptual Layers

### 4.1 Layer Definitions

| Layer | Purpose | Ownership | Change Frequency |
|-------|---------|-----------|------------------|
| **Core** | Universal, batteries-included functionality | AWS Coworker maintainers | Low (versioned releases) |
| **Organization** | Org-specific policies, naming, governance | Platform team | Medium (as policies evolve) |
| **BU/Tenant** | Business unit or tenant-specific overlays | BU/Tenant owners | Variable |

### 4.2 Layer Interaction

```yaml
# Precedence (highest to lowest):
# 1. BU/Tenant layer (most specific)
# 2. Organization layer
# 3. Core layer (default fallback)

# Example: Tagging policy resolution
core:
  tags:
    required: [Environment, Owner]

org:
  tags:
    required: [Environment, Owner, CostCenter, DataClassification]

bu_finance:
  tags:
    required: [Environment, Owner, CostCenter, DataClassification, SOXCompliant]
```

### 4.3 Layer Isolation

- **Core layer is immutable** — Organizations cannot modify core files directly
- **Org layer extends, doesn't replace** — Org customizations overlay core defaults
- **BU layer is optional** — Not all deployments need BU-level customization
- **Upgrade path preserved** — Core updates don't break org/BU customizations

---

## 5. Directory Structure & Naming Conventions

### 5.1 Repository Structure

```
aws-coworker/
├── .claude/
│   ├── agents/                          # Agent definitions
│   │   ├── aws-coworker-core.md
│   │   ├── aws-coworker-planner.md
│   │   ├── aws-coworker-executor.md
│   │   ├── aws-coworker-guardrail.md
│   │   ├── aws-coworker-observability-cost.md
│   │   └── aws-coworker-meta-designer.md
│   │
│   ├── commands/                        # Slash command definitions
│   │   ├── aws-coworker-plan-interaction.md
│   │   ├── aws-coworker-execute-nonprod.md
│   │   ├── aws-coworker-prepare-prod-change.md
│   │   ├── aws-coworker-rollback-change.md
│   │   ├── aws-coworker-bootstrap-account.md
│   │   ├── aws-coworker-new-skill-from-session.md
│   │   ├── aws-coworker-refactor-skills.md
│   │   └── aws-coworker-audit-library.md
│   │
│   └── settings.json                    # Claude Code settings
│
├── skills/
│   ├── core/                            # Non-AWS core skills
│   │   ├── git-workflow/
│   │   │   └── SKILL.md
│   │   └── documentation-standards/
│   │       └── SKILL.md
│   │
│   ├── aws/                             # AWS-focused skills
│   │   ├── aws-cli-playbook/
│   │   │   ├── SKILL.md
│   │   │   └── commands/                # Service-specific command references
│   │   │       ├── iam.md
│   │   │       ├── organizations.md
│   │   │       ├── ec2.md
│   │   │       ├── vpc.md
│   │   │       ├── s3.md
│   │   │       ├── rds.md
│   │   │       ├── ecs.md
│   │   │       ├── eks.md
│   │   │       ├── lambda.md
│   │   │       └── cloudformation.md
│   │   │
│   │   ├── aws-well-architected/
│   │   │   ├── SKILL.md
│   │   │   └── pillars/
│   │   │       ├── operational-excellence.md
│   │   │       ├── security.md
│   │   │       ├── reliability.md
│   │   │       ├── performance-efficiency.md
│   │   │       ├── cost-optimization.md
│   │   │       └── sustainability.md
│   │   │
│   │   ├── aws-observability-setup/
│   │   │   └── SKILL.md
│   │   │
│   │   └── aws-cost-optimizer/
│   │       └── SKILL.md
│   │
│   ├── org/                             # Organization-specific skills
│   │   ├── aws-org-strategy/
│   │   │   ├── SKILL.md
│   │   │   └── templates/
│   │   │       ├── single-account.md
│   │   │       ├── multi-account-basic.md
│   │   │       └── multi-account-control-tower.md
│   │   │
│   │   └── aws-governance-guardrails/
│   │       ├── SKILL.md
│   │       └── policies/
│   │           ├── iam-policies.md
│   │           ├── network-policies.md
│   │           ├── data-policies.md
│   │           └── tagging-policies.md
│   │
│   └── meta/                            # Meta-design skills
│       ├── skill-designer/
│       │   └── SKILL.md
│       ├── command-designer/
│       │   └── SKILL.md
│       └── audit-library/
│           └── SKILL.md
│
├── config/                              # Configuration templates
│   ├── profiles/
│   │   └── example-profiles.yaml
│   ├── environments/
│   │   └── example-environments.yaml
│   └── org-config/
│       └── example-org-config.yaml
│
├── docs/                                # Documentation
│   ├── DESIGN.md                        # This document
│   ├── getting-started/
│   │   ├── README.md
│   │   ├── installation.md
│   │   ├── first-interaction.md
│   │   └── common-workflows.md
│   └── customization/
│       ├── README.md
│       ├── adding-org-skills.md
│       ├── governance-integration.md
│       └── multi-tenant-setup.md
│
├── examples/                            # Example implementations
│   ├── single-account/
│   ├── multi-account-organizations/
│   └── control-tower/
│
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

### 5.2 Directory Structure Rationale

**Why `.claude/` for agents and commands, but `skills/` at root level?**

This is an intentional architectural decision, not an oversight:

| Location | Contains | Rationale |
|----------|----------|-----------|
| `.claude/agents/` | Agent definitions | Claude Code convention for execution components |
| `.claude/commands/` | Slash commands | Claude Code convention for workflow triggers |
| `skills/` (root) | Knowledge & policy documents | Intentionally visible, human-readable, tool-agnostic |

**Detailed reasoning:**

1. **`.claude/` directory (Claude Code convention)**
   - Agents and commands are *execution components* — they define how Claude operates
   - Following Claude Code's standard location ensures compatibility with Claude tooling
   - The `.` prefix indicates these are tool-specific configuration files

2. **`skills/` at repository root (AWS Coworker design decision)**
   - Skills are *knowledge documents* — policies, patterns, and guidance
   - They should be visible, browsable, and maintainable by humans
   - No `.` prefix because these aren't hidden configuration; they're core content
   - Skills can be referenced by tools other than Claude (documentation, training, audits)
   - Agents load skills via the `Read` tool by path, so location is flexible

3. **How skills are loaded**
   - Commands reference skills in their frontmatter: `skills: [aws-cli-playbook, aws-governance-guardrails]`
   - Agents read skill files using the `Read` tool when guidance is needed
   - This explicit loading pattern means skills don't require a specific location

**Alternative considered:** Placing skills in `.claude/skills/` was considered for consistency, but rejected because skills are meant to be visible, human-maintained documentation rather than hidden tool configuration.

### 5.3 Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Agents | `aws-coworker-{role}.md` | `aws-coworker-planner.md` |
| Slash Commands | `aws-coworker-{action}.md` | `aws-coworker-plan-interaction.md` |
| Skills (dirs) | `{category}-{name}/` | `aws-cli-playbook/` |
| Skill files | `SKILL.md` (main), supporting `.md` files | `SKILL.md`, `iam.md` |
| Config files | `{purpose}.yaml` | `environments.yaml` |

### 5.4 File Naming Rules

1. **Lowercase with hyphens** — `aws-coworker-core.md`, not `AWSCoworkerCore.md`
2. **Descriptive prefixes** — All AWS Coworker components prefixed with `aws-coworker-`
3. **No spaces or special characters** — Use hyphens for word separation
4. **Extension consistency** — `.md` for documentation/definitions, `.yaml` for config

---

## 6. Governance Model

### 6.1 Change Management Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Change Management Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. PROPOSAL                                                            │
│     ┌──────────────────┐                                                │
│     │ Create feature   │                                                │
│     │ branch from main │                                                │
│     └────────┬─────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│  2. DEVELOPMENT                                                         │
│     ┌──────────────────┐                                                │
│     │ Make changes via │                                                │
│     │ meta-designer or │                                                │
│     │ manual edits     │                                                │
│     └────────┬─────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│  3. VALIDATION                                                          │
│     ┌──────────────────┐                                                │
│     │ Run audit-library│                                                │
│     │ skill checks     │                                                │
│     └────────┬─────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│  4. REVIEW                                                              │
│     ┌──────────────────┐                                                │
│     │ Open PR, request │                                                │
│     │ human review     │                                                │
│     └────────┬─────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│  5. APPROVAL & MERGE                                                    │
│     ┌──────────────────┐                                                │
│     │ Approved PR      │                                                │
│     │ merged to main   │                                                │
│     └────────┬─────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│  6. RELEASE (optional)                                                  │
│     ┌──────────────────┐                                                │
│     │ Tag release for  │                                                │
│     │ versioned        │                                                │
│     │ baseline         │                                                │
│     └──────────────────┘                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Branch Strategy

| Branch Type | Purpose | Naming | Merge Target |
|-------------|---------|--------|--------------|
| `main` | Production-ready baseline | `main` | N/A (protected) |
| `feature/*` | New agents/skills/commands | `feature/add-eks-skill` | `main` |
| `fix/*` | Bug fixes and corrections | `fix/guardrail-typo` | `main` |
| `org/*` | Organization-specific changes | `org/acme-tagging-policy` | `main` or org branch |
| `release/*` | Release preparation | `release/v1.2.0` | `main` + tag |

### 6.3 Version Tagging

```
# Semantic versioning for releases
v1.0.0          # Initial stable release
v1.1.0          # New features (backward compatible)
v1.1.1          # Bug fixes
v2.0.0          # Breaking changes

# Baseline tags for rollback
baseline/2026-01-29    # Date-based baseline
baseline/pre-org-customization  # Named baseline
```

### 6.4 Core vs Organization vs BU Separation

```
# Core changes (batteries-included updates)
# - Managed via official AWS Coworker releases
# - Organizations pull updates, don't modify directly
# - Protected by .github/CODEOWNERS

# Organization changes (org-specific customizations)
# - Stored in skills/org/ and config/org-config/
# - Follow org's change management process
# - Can extend but not modify core

# BU/Tenant changes (team-specific overlays)
# - Stored in separate directories or repos
# - Lightest governance appropriate to scope
```

### 6.5 Rollback Procedures

```bash
# Rollback to previous release
git checkout main
git reset --hard v1.1.0

# Rollback to named baseline
git checkout baseline/pre-org-customization

# Create rollback branch for review
git checkout -b rollback/from-v1.2.0-to-v1.1.0
git reset --hard v1.1.0
# Open PR for review before merging
```

---

## 7. AWS Interaction Model

### 7.1 Profile and Region Handling

#### Discovery

```yaml
# AWS Coworker discovers available profiles from:
# 1. ~/.aws/credentials
# 2. ~/.aws/config
# 3. Environment variables (AWS_PROFILE, AWS_DEFAULT_REGION)
# 4. AWS Coworker config/profiles/ configuration

# Profile classification
profiles:
  discovered:
    - name: default
      classification: unknown  # Must be explicitly configured
      permissions: read-only   # Conservative default

    - name: dev-admin
      classification: non-production
      permissions: read-write

    - name: prod-readonly
      classification: production
      permissions: read-only

    - name: prod-admin
      classification: production
      permissions: read-write
      require_approval: always
```

#### Announcement Protocol

Before ANY AWS CLI operation, agents MUST:

1. **State the profile**: "I will use profile `dev-admin`"
2. **State the region**: "targeting region `us-east-1`"
3. **State the operation type**: "This is a read-only discovery operation" or "This will modify resources"
4. **For mutations, state blast radius**: "This will affect 3 EC2 instances in the dev-web ASG"

#### Conservative Defaults

| Profile State | Default Permission | Rationale |
|--------------|-------------------|-----------|
| Newly discovered | Read-only | Prevent accidental mutations |
| Explicitly configured as non-prod | Read-write with approval | Allow productive work |
| Explicitly configured as prod | Read-only | Prod changes via CI/CD |
| Unknown/unclear | Read-only | Safety first |

### 7.2 Environment Classification

```yaml
environments:
  sandbox:
    purpose: Experimentation, learning
    aws_cli_permissions: read-write
    approval_required: none

  development:
    purpose: Active development
    aws_cli_permissions: read-write
    approval_required: destructive-only

  test:
    purpose: Integration and QA testing
    aws_cli_permissions: read-write
    approval_required: destructive-only

  staging:
    purpose: Pre-production validation
    aws_cli_permissions: read-only (direct), read-write (IaC pipelines)
    approval_required: all-mutations

  production:
    purpose: Live workloads
    aws_cli_permissions: read-only (direct CLI)
    approval_required: via-cicd-only
```

### 7.3 Operation Types

| Type | Description | Approval | Example |
|------|-------------|----------|---------|
| **Discovery** | Read-only queries | None | `aws ec2 describe-instances` |
| **Planning** | Dry-run, what-if | None | `aws cloudformation create-change-set` |
| **Non-destructive mutation** | Create new resources | Confirmation | `aws ec2 run-instances` |
| **Destructive mutation** | Delete, terminate, modify | Explicit approval | `aws ec2 terminate-instances` |
| **Sensitive operation** | IAM, security groups, encryption | Explicit approval + guardrail check | `aws iam create-role` |

### 7.4 IaC Preference

AWS Coworker prefers Infrastructure as Code over ad-hoc CLI:

```
Preference Order:
1. IaC (CDK, Terraform, CloudFormation) - Most preferred
2. AWS CLI with --dry-run validation - Acceptable for simple cases
3. Ad-hoc AWS CLI mutations - Discouraged, requires justification
```

### 7.5 Production Change Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Production Change Flow                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  AWS Coworker agents NEVER directly mutate production via CLI.          │
│                                                                         │
│  Instead:                                                               │
│                                                                         │
│  1. Plan the change using /aws-coworker-plan-interaction                │
│  2. Validate with guardrail subagent                                    │
│  3. Generate IaC code (CDK/Terraform/CloudFormation)                    │
│  4. Create PR with IaC changes                                          │
│  5. CI/CD pipeline applies changes after human approval                 │
│                                                                         │
│  For emergency production access:                                       │
│  - Use break-glass procedures defined in org governance                 │
│  - All actions logged and audited                                       │
│  - Post-incident review required                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Extensibility & Evolution Model

### 8.1 Adding New Skills

```yaml
# Skill addition workflow

1. Identify need:
   - User requests capability not covered by existing skills
   - Pattern emerges from multiple interactions
   - New AWS service requires coverage

2. Use meta-designer agent:
   - Run /aws-coworker-new-skill-from-session
   - Or manually create following skill-designer guidelines

3. Skill structure:
   skills/{category}/{skill-name}/
   ├── SKILL.md          # Main skill definition (required)
   ├── examples/         # Usage examples (optional)
   └── templates/        # Reusable templates (optional)

4. Skill frontmatter:
   ---
   name: aws-new-service
   description: Patterns for interacting with AWS New Service
   version: 1.0.0
   category: aws
   agents: [aws-coworker-core, aws-coworker-planner]
   tools: [Read, Bash]
   ---

5. Review and merge:
   - Create PR with new skill
   - Run /aws-coworker-audit-library for validation
   - Human review and approval
```

### 8.2 Adding New Commands

```yaml
# Command addition workflow

1. Identify workflow need:
   - Repeated multi-step interactions
   - Complex orchestration requirements
   - Standardized procedure needed

2. Use command-designer skill:
   - Follow patterns in skills/meta/command-designer/
   - Define clear input parameters
   - Specify agent and skill dependencies

3. Command structure:
   .claude/commands/aws-coworker-{action}.md

4. Command frontmatter:
   ---
   description: Brief description of what this command does
   skills: [skill1, skill2]
   agent: aws-coworker-core  # or specific subagent
   tools: [Read, Write, Bash]
   arguments:
     - name: target
       description: The target resource or scope
       required: true
     - name: dry-run
       description: Preview without executing
       required: false
       default: true
   ---
```

### 8.3 Adding New Agents

```yaml
# Agent addition workflow (rare, requires careful consideration)

1. Justify new agent:
   - Existing agents cannot cover the use case
   - Distinct permission boundary needed
   - Specialized tool access required

2. Agent definition:
   .claude/agents/aws-coworker-{role}.md

3. Required elements:
   - Purpose and scope
   - Allowed tools
   - Collaboration patterns
   - Safety constraints
   - Example interactions

4. Integration:
   - Update relevant slash commands
   - Document in agent catalog
   - Train users on when to use
```

### 8.4 Meta-Layer Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Meta-Designer Agent** | Evolve AWS Coworker itself | `.claude/agents/aws-coworker-meta-designer.md` |
| **Skill Designer** | Patterns for creating skills | `skills/meta/skill-designer/` |
| **Command Designer** | Patterns for creating commands | `skills/meta/command-designer/` |
| **Audit Library** | Validate AWS Coworker health | `skills/meta/audit-library/` |

### 8.5 Evolution Triggers

```yaml
automatic_triggers:
  - Repeated user questions not covered by existing skills
  - Error patterns indicating missing guidance
  - New AWS services or features released
  - Governance policy changes

manual_triggers:
  - Scheduled quarterly reviews
  - Post-incident improvements
  - Organizational changes
  - User feedback
```

---

## 9. Documentation Model

### 9.1 README Structure

```markdown
# README.md outline

## What is AWS Coworker?
- One-paragraph description
- Key capabilities
- Target users

## Quick Start
- Prerequisites
- Installation (link to getting-started/)
- First interaction example

## Architecture
- High-level diagram
- Link to DESIGN.md for details

## Components
- Agents overview
- Skills overview
- Commands overview

## Customization
- Adding org-specific skills
- Link to customization guide

## Contributing
- How to contribute
- Link to CONTRIBUTING.md

## License
```

### 9.2 Getting Started Guide Structure

```markdown
# docs/getting-started/

## README.md
- Prerequisites
- What you'll learn
- Time estimate

## installation.md
- Clone repository
- Configure AWS CLI
- Verify setup

## first-interaction.md
- Basic discovery workflow
- Planning a simple change
- Understanding output

## common-workflows.md
- Account inventory
- Security audit
- Cost review
- Resource tagging
```

### 9.3 Customization Guide Structure

```markdown
# docs/customization/

## README.md
- When to customize
- Customization layers
- Governance integration

## adding-org-skills.md
- Creating org-specific skills
- Extending core skills
- Testing custom skills

## governance-integration.md
- Connecting to ticketing systems
- Audit trail requirements
- Approval workflows

## multi-tenant-setup.md
- When to use multi-tenancy
- BU-level overlays
- Isolation patterns
```

### 9.4 Context Files (CLAUDE.md)

AWS Coworker uses two context files to provide Claude with appropriate instructions based on the interaction mode:

| File | Purpose | Critical |
|------|---------|----------|
| `CLAUDE.md` | **Usage context** — Intercepts all AWS-related requests and routes them through AWS Coworker commands. Enforces the safety model regardless of how users phrase their requests. | **Mandatory** |
| `CLAUDE-DEVELOPMENT.md` | **Development context** — Directory conventions, naming patterns, design decisions for maintainers working on AWS Coworker itself. | Recommended |

**Why two files?**

1. **Usage context** (`CLAUDE.md`): When users interact with AWS through Claude, all requests must go through AWS Coworker commands to ensure the safety model is enforced. This file intercepts free-form requests like "list my S3 buckets" and routes them to `/aws-coworker-plan-interaction` with the user's goal as context.

2. **Development context** (`CLAUDE-DEVELOPMENT.md`): When developers are maintaining or extending AWS Coworker itself, they need different context — directory conventions, naming patterns, how components relate to each other.

**The `CLAUDE.md` file is mandatory** because without it, free-form AWS requests bypass the command system entirely, and the safety model (profile announcement, approval gates, production protection) would not be enforced.

---

## 10. Security & Compliance

### 10.1 Secrets Management

```yaml
# .gitignore patterns for secrets
.env
.env.*
*.pem
*.key
credentials
credentials.*
**/secrets/
.aws/credentials  # If copied locally
```

### 10.2 Audit Trail

All AWS Coworker interactions should be auditable:

```yaml
audit_requirements:
  what_to_log:
    - Command invoked
    - Agent used
    - Skills referenced
    - AWS profile/region
    - Operations performed
    - Approval decisions

  where_to_log:
    - Git commit history (for changes)
    - AWS CloudTrail (for AWS operations)
    - Organization's SIEM (if integrated)

  retention:
    - Follow organization's data retention policy
    - Minimum: 90 days for non-prod, 7 years for prod (typical)
```

### 10.3 Least Privilege Defaults

```yaml
iam_principles:
  - Agents request minimum permissions needed
  - Read-only by default for unknown contexts
  - Temporary credentials preferred over long-lived
  - Role assumption over direct credentials where possible

example_permissions:
  discovery_operations:
    - ec2:Describe*
    - s3:List*
    - iam:Get*
    - cloudformation:Describe*

  planning_operations:
    - cloudformation:CreateChangeSet
    - cloudformation:DescribeChangeSet

  # Mutation permissions defined per-environment, per-service
```

### 10.4 Compliance Frameworks

AWS Coworker supports compliance through:

| Framework | Support Mechanism |
|-----------|-------------------|
| SOC 2 | Audit trails, access controls, change management |
| HIPAA | Data classification tagging, encryption defaults |
| PCI-DSS | Network segmentation validation, logging |
| FedRAMP | GovCloud region support, compliance checks |

---

## 11. Reference Library Specifications

### 11.1 Agents Summary

| Agent | Role | Tools | Key Behaviors |
|-------|------|-------|---------------|
| `aws-coworker-core` | Primary interaction orchestrator | Read, Write, Edit, Bash, Skills | Profile/region announcement, approval workflows |
| `aws-coworker-planner` | Planning without execution | Read, Grep, Glob | Generate interaction plans, no mutations |
| `aws-coworker-executor` | Execute approved plans | Bash, Read, Write, Git | Non-prod execution, CI/CD generation for prod |
| `aws-coworker-guardrail` | Compliance validation | Read, Grep, Glob | Check policies, produce findings |
| `aws-coworker-observability-cost` | Monitoring and cost | Read, Grep, limited Bash | Read-only AWS queries, recommendations |
| `aws-coworker-meta-designer` | Self-evolution | Read, Write, Edit, Git | Propose changes as PRs, no AWS mutations |

### 11.2 Skills Summary

| Skill | Category | Purpose |
|-------|----------|---------|
| `aws-cli-playbook` | aws | AWS CLI patterns for all major services |
| `aws-well-architected` | aws | Well-Architected Framework alignment |
| `aws-observability-setup` | aws | CloudWatch, CloudTrail, logging patterns |
| `aws-cost-optimizer` | aws | Cost awareness and optimization |
| `aws-org-strategy` | org | Multi-account/OU strategy templates |
| `aws-governance-guardrails` | org | Never-do/always-do policies |
| `skill-designer` | meta | Patterns for creating skills |
| `command-designer` | meta | Patterns for creating commands |
| `audit-library` | meta | Health checks for AWS Coworker |
| `git-workflow` | core | Git/GitHub best practices |
| `documentation-standards` | core | Documentation guidelines |

### 11.3 Commands Summary

| Command | Purpose | Primary Agent | Key Skills |
|---------|---------|---------------|------------|
| `/aws-coworker-plan-interaction` | Plan AWS interaction | planner | cli-playbook, well-architected, governance |
| `/aws-coworker-execute-nonprod` | Execute in non-prod | executor | cli-playbook, governance |
| `/aws-coworker-prepare-prod-change` | Generate CI/CD changes | executor | cli-playbook, governance |
| `/aws-coworker-rollback-change` | Design/execute rollback | executor | cli-playbook |
| `/aws-coworker-bootstrap-account` | Set up new account | planner + executor | org-strategy, governance |
| `/aws-coworker-new-skill-from-session` | Create skill from usage | meta-designer | skill-designer |
| `/aws-coworker-refactor-skills` | Refactor existing skills | meta-designer | audit-library |
| `/aws-coworker-audit-library` | Audit AWS Coworker health | meta-designer | audit-library |

---

## 12. Implementation Phases

### Phase 1: Foundation (Scaffold + Meta Layer)

**Deliverables:**
- Directory structure created
- Meta-designer agent defined
- Meta skills (skill-designer, command-designer, audit-library)
- Documentation framework (README, Getting Started outline, Customization outline)
- .gitignore and repository configuration

**Success Criteria:**
- Can run `/aws-coworker-audit-library` (even if findings are "no skills to audit yet")
- Documentation structure navigable

### Phase 2: Read-Only Capabilities

**Deliverables:**
- `aws-coworker-core` agent (read-only mode)
- `aws-coworker-planner` agent
- `aws-cli-playbook` skill (discovery commands)
- `aws-well-architected` skill
- `/aws-coworker-plan-interaction` command

**Success Criteria:**
- Can discover AWS resources across services
- Can generate interaction plans with Well-Architected alignment
- No mutation capabilities yet

### Phase 3: Non-Production Execution

**Deliverables:**
- `aws-coworker-executor` agent
- `aws-coworker-guardrail` agent
- `aws-governance-guardrails` skill
- `aws-org-strategy` skill
- `/aws-coworker-execute-nonprod` command
- `/aws-coworker-rollback-change` command

**Success Criteria:**
- Can execute approved plans in non-prod environments
- Guardrail validation working
- Rollback procedures functional

### Phase 4: Production & Observability

**Deliverables:**
- `aws-coworker-observability-cost` agent
- `aws-observability-setup` skill
- `aws-cost-optimizer` skill
- `/aws-coworker-prepare-prod-change` command
- `/aws-coworker-bootstrap-account` command

**Success Criteria:**
- Production changes generate CI/CD artifacts (not direct execution)
- Cost and observability recommendations working
- Account bootstrap workflow functional

### Phase 5: Full Meta-Evolution

**Deliverables:**
- All meta-commands fully operational
- `/aws-coworker-new-skill-from-session`
- `/aws-coworker-refactor-skills`
- Example implementations for all supported AWS estate types

**Success Criteria:**
- Can evolve AWS Coworker through usage
- Examples cover single-account through Control Tower
- Full audit and refactoring capabilities

---

## Appendix A: .gitignore Template

```gitignore
# AWS Coworker .gitignore

# Credentials and secrets
.env
.env.*
*.pem
*.key
*.p12
*.pfx
credentials
credentials.*
**/secrets/
.aws/

# AWS CLI local state
.aws-sam/
samconfig.toml

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!example.tfvars

# CDK
cdk.out/
cdk.context.json

# IDE and editor
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store

# Build artifacts
dist/
build/
*.zip
*.tar.gz

# Logs
*.log
logs/

# Local configuration (not to be committed)
config/local/

# Test artifacts
coverage/
.pytest_cache/
.nyc_output/
```

---

## Appendix B: Approval Checklist

Before approving this design document, please verify:

- [ ] Architecture aligns with your expected AWS estate patterns
- [ ] Governance model fits your change management requirements
- [ ] Agent responsibilities are clear and appropriate
- [ ] Skill categories cover your anticipated needs
- [ ] Command workflows match your operational patterns
- [ ] Security constraints are appropriate for your environment
- [ ] Phased implementation order makes sense for your priorities
- [ ] Documentation structure will serve your teams

---

**End of Design Document**

*Please review and provide approval or requested changes before implementation begins.*
