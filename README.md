# AWS Coworker

**A batteries-included system for enterprise AWS infrastructure management, built on [Claude Code](https://claude.ai/code). Works out of the box. Designed to be extended.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Built on Claude Code

AWS Coworker is built on **[Claude Code](https://claude.ai/code)** and **Anthropic's Claude Agent SDK**, augmenting AWS best practices with Claude's agentic capabilities for safe, effective infrastructure management.

| What Claude Code Provides | What AWS Coworker Adds |
|---------------------------|------------------------|
| Agent architecture & Task tool | AWS-specific agents with defined roles |
| Skill system for knowledge | AWS CLI patterns, Well-Architected guidance |
| Slash commands for workflows | Safety-first workflows with approval gates |
| Multi-agent orchestration | Configurable thresholds for parallel execution |
| Model flexibility (Opus, Sonnet, Haiku) | Tiered model strategy optimized for cost |

**The goal:** Show how Claude can be a trusted partner for cloud operations—not by constraining it, but by giving it the right context, guardrails, and patterns.

---

## Important Notice

**You are responsible for what AWS Coworker does to your AWS account(s).**

While we continue to enhance and test AWS Coworker's safety guardrails, managing complex cloud architectures requires more than opinionated frameworks. Every AWS environment is unique—different account structures, security requirements, compliance needs, and operational patterns.

AWS Coworker is designed to **augment, not replace**:
- Platform Engineers
- DevOps Engineers
- Cloud Architects
- Site Reliability Engineers (SREs)
- Security Engineers
- FinOps Practitioners

**The non-deterministic nature of generative AI is a double-edged sword.** It enables Claude to navigate complexity, adapt to unique situations, and provide nuanced recommendations that brittle rule-based systems cannot. But it also means outputs can vary, and human judgment remains essential.

AWS Coworker provides guardrails, approval gates, and safety defaults—but **you must review plans before execution**, especially for production workloads. The system is a powerful tool to help you work faster and more consistently, not an autopilot.

---

## What is AWS Coworker?

AWS Coworker is a **production-ready system** for managing AWS with Claude. The core works out of the box, and the layered architecture lets you extend it for your organization's needs. It provides:

- **Curated Agents** — Pre-configured agents for planning, execution, compliance, and cost analysis
- **AWS Skills Library** — CLI patterns, Well-Architected pillars, governance policies
- **Safety Guardrails** — Read-only defaults, explicit approvals, production protection
- **Enterprise Patterns** — Multi-account, multi-region orchestration with parallel execution
- **Self-Evolution** — Meta-layer that can extend itself based on usage patterns

With proper structure, Claude handles infrastructure work **safely, efficiently, and at scale**.

---

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) or compatible Claude environment
- AWS CLI installed and configured (`aws --version`)
- Git installed (`git --version`)
- At least one AWS profile configured (`~/.aws/credentials` or `~/.aws/config`)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/aws-coworker-enterprise.git
cd aws-coworker-enterprise

# Verify AWS CLI access
aws sts get-caller-identity
```

### First Interaction

```
# In Claude Code, try:
/aws-coworker-plan-interaction

# Follow the prompts to plan an AWS interaction
```

See [Getting Started Guide](docs/getting-started/README.md) for detailed instructions.

---

## Architecture

```
               User Request (free-form or /command)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE.md (Request Interception)               │
├─────────────────────────────────────────────────────────────┤
│                      SLASH COMMANDS                         │
│                   (Workflow Orchestration)                  │
├─────────────────────────────────────────────────────────────┤
│                         AGENTS                              │
│    Core │ Planner │ Executor │ Guardrail │ Obs/Cost │ Meta  │
│                   ↓ (parallel for complex tasks)            │
│              [Sub-Agent] [Sub-Agent] [Sub-Agent]            │
├─────────────────────────────────────────────────────────────┤
│                         SKILLS                              │
│         aws/ │ org/ │ meta/ │ core/                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    AWS CLI / IaC Tools
```

### Layers

| Layer | Purpose | Location |
|-------|---------|----------|
| **Core** | Universal, batteries-included | `skills/aws/`, `skills/core/`, `skills/meta/` |
| **Organization** | Org-specific policies | `skills/org/`, `config/org-config/` |
| **BU/Tenant** | Team-specific overlays | Custom directories |

---

## Components

### Agents

| Agent | Purpose |
|-------|---------|
| `aws-coworker-core` | Primary interaction orchestrator |
| `aws-coworker-planner` | Planning without execution |
| `aws-coworker-executor` | Execute approved plans |
| `aws-coworker-guardrail` | Compliance validation |
| `aws-coworker-observability-cost` | Monitoring and cost optimization |
| `aws-coworker-meta-designer` | Self-evolution and maintenance |

### Key Skills

| Skill | Category | Purpose |
|-------|----------|---------|
| `aws-cli-playbook` | aws | CLI patterns for major services |
| `aws-well-architected` | aws | Well-Architected alignment |
| `aws-governance-guardrails` | org | Never-do/always-do policies |
| `skill-designer` | meta | Create new skills |

### Commands

| Command | Purpose |
|---------|---------|
| `/aws-coworker-plan-interaction` | Plan AWS operations |
| `/aws-coworker-execute-nonprod` | Execute in non-production |
| `/aws-coworker-prepare-prod-change` | Generate CI/CD changes for production |
| `/aws-coworker-audit-library` | Audit AWS Coworker health |

---

## Safety Model

1. **Read-only by default** — Unknown profiles start with read-only access
2. **Profile/region announcement** — Always stated before any operation
3. **Explicit approval** — Mutations require human confirmation
4. **Production via CI/CD** — No direct CLI mutations to production
5. **Rollback ready** — Every plan includes rollback procedures

### How Safety is Enforced

The `CLAUDE.md` file at the repository root **intercepts all AWS-related requests** and routes them through AWS Coworker commands. This means:

- **Explicit commands** like `/aws-coworker-plan-interaction` invoke the safety model directly
- **Free-form requests** like "list my S3 buckets" are automatically routed through the appropriate command

This ensures the safety model is enforced regardless of how you phrase your request. You can use natural language — AWS Coworker will handle the routing.

For development/maintenance of AWS Coworker itself, see `CLAUDE-DEVELOPMENT.md`.

---

## Always-Agent Mode

AWS Coworker operates in **Always-Agent Mode**: every request spawns at least one agent via the Task tool. This ensures consistent execution paths, comprehensive audit trails, and efficient handling of enterprise workloads.

### Why Always-Agent Mode?

| Benefit | Explanation |
|---------|-------------|
| **Consistency** | Same execution path regardless of task complexity |
| **Auditability** | Every operation tracked through agent invocation |
| **Scalability** | Seamless transition from simple to complex tasks |
| **Enterprise-ready** | Designed for environments where complex tasks are common |

Simple tasks like "list my S3 buckets" work perfectly fine — they use a single agent. The overhead is minimal; the consistency benefits are significant.

### Model Hierarchy

AWS Coworker uses a tiered model strategy for cost efficiency and performance:

| Role | Model | Purpose |
|------|-------|---------|
| **Primary (Orchestrator)** | Your selected model (Opus, Sonnet, etc.) | Orchestration, decisions, user communication, result synthesis |
| **Sub-Agents (Read-Only)** | Haiku | Fast parallel discovery, audits, cost analysis |
| **Sub-Agents (Mutations)** | Sonnet | Thorough state-change analysis |

**Why this matters:** If you run AWS Coworker with Opus 4.5, Opus handles the "thinking" (orchestration, threshold evaluation, aggregation) while Haiku does the parallelized "doing" (scanning each region). You get the best quality where it counts, with optimized cost at scale.

### Configurable Thresholds

Thresholds determine **how many agents** to spawn, not **whether** to spawn agents.

| Factor | Single Agent | Parallel Agents |
|--------|--------------|-----------------|
| Resources | < 50 | >= 50 |
| Regions | <= 3 | > 3 |
| Accounts | <= 3 | > 3 |

**Configuration:** `.claude/config/orchestration-config.md`

### Example: Large-Scale Audit

```
User: "Audit all S3 buckets for public access"

AWS Coworker:
  Discovery reveals 847 buckets across 8 regions.
  Estimated audit time: 8-10 minutes.

  I'll work in parallel (8 agents, one per region). Proceed? (yes/no)

User: yes

AWS Coworker:
  Starting audit with 8 parallel agents...
  - us-east-1: Scanning 150 buckets... ✓
  - us-west-2: Scanning 120 buckets... ✓
  - eu-west-1: Scanning 100 buckets... ✓
  - ap-southeast-1: Scanning 95 buckets... ✓
  ... (4 more regions)

  Audit complete (3m 45s). Found 12 buckets with public access.
```

### Example: Simple Query

```
User: "List my EC2 instances"

AWS Coworker:
  [Single agent executes]

  Found 4 instances in us-east-1:
  - i-abc123 (running) - t3.medium - web-server
  - i-def456 (running) - t3.large - api-server
  ...
```

The primary agent (Core Agent) remains the gatekeeper — all approvals flow through the user, and sub-agents only receive permission for the specific scope the user approved.

---

## Customization

AWS Coworker supports layered customization:

```
Your Customizations (BU/Tenant)
        ↓
Organization Policies (skills/org/)
        ↓
Core Framework (batteries-included)
```

See [Customization Guide](docs/customization/README.md) for:
- Adding organization-specific skills
- Integrating with your governance processes
- Setting up multi-tenant overlays

---

## Directory Structure

```
aws-coworker/
├── .claude/
│   ├── agents/          # Agent definitions
│   ├── commands/        # Slash command definitions
│   └── config/          # Agent orchestration (thresholds, model selection)
├── config/              # AWS environment configuration (profiles, environments)
├── skills/
│   ├── aws/             # AWS-focused skills
│   ├── org/             # Organization-specific
│   ├── meta/            # Meta-design skills
│   └── core/            # Non-AWS core skills
├── docs/                # Documentation
└── examples/            # Example implementations
```

**Why this structure?**

- **`.claude/`** contains *execution components* (agents, commands, orchestration config) — follows Claude Code conventions
- **`/config/`** at root contains *AWS environment templates* (profile classification, environment definitions)
- **`skills/`** at root contains *knowledge documents* (policies, patterns) — intentionally visible and human-maintainable

**Two config directories explained:**

| Directory | Purpose | Contents |
|-----------|---------|----------|
| **`.claude/config/`** | How Claude orchestrates agents | Thresholds, model selection (haiku/sonnet), parallelization limits |
| **`/config/`** (root) | How AWS environments are classified | Profile → environment mapping, safety rules, org settings |

Skills are loaded by agents via explicit `Read` operations, making their location flexible. Placing them at root (not `.claude/skills/`) emphasizes they are core content meant to be browsed, edited, and referenced beyond just Claude tooling.

See [DESIGN.md](docs/DESIGN.md#52-directory-structure-rationale) for detailed rationale.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to propose new skills or commands
- Code style and documentation standards
- Pull request process

---

## Documentation

- [Design Document](docs/DESIGN.md) — Full architectural specification
- [Getting Started](docs/getting-started/README.md) — Installation and first steps
- [Customization Guide](docs/customization/README.md) — Extending AWS Coworker

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/aws-coworker-enterprise/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/aws-coworker-enterprise/discussions)

---

## Acknowledgments

AWS Coworker is built on [Claude Code](https://claude.ai/code) and the [Claude Agent SDK](https://docs.anthropic.com/en/docs/build-with-claude/claude-code/sdk) by [Anthropic](https://www.anthropic.com).

Learn more about building with Claude:
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/build-with-claude/claude-code)
- [Anthropic API Documentation](https://docs.anthropic.com/en/api)
