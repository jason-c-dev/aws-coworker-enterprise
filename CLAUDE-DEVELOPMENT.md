# CLAUDE-DEVELOPMENT.md - AWS Coworker Development Context

This file provides context for Claude when **developing or maintaining** AWS Coworker itself. It ensures consistency across sessions, especially after conversation compression.

**Important:** This file is for *development* of AWS Coworker. For *using* AWS Coworker to interact with AWS, see [CLAUDE.md](CLAUDE.md).

---

## Two-File Context Structure

AWS Coworker uses two context files for different purposes:

| File | Purpose | When Loaded |
|------|---------|-------------|
| `CLAUDE.md` | **Usage context** — Intercepts all AWS requests and routes them through AWS Coworker commands. Enforces safety model. | When using AWS Coworker to interact with AWS |
| `CLAUDE-DEVELOPMENT.md` | **Development context** — Directory conventions, naming patterns, design decisions for maintainers. | When developing/maintaining AWS Coworker itself |

The `CLAUDE.md` file is **mandatory** for safe AWS operations. Without it, free-form AWS requests would bypass the command system and safety model.

---

## Project Overview

**AWS Coworker** is a batteries-included, fully extensible meta-system of agents, skills, and slash commands for enterprise AWS interaction. It is NOT an application architecture framework — it's a platform for *interacting with AWS* safely and consistently.

**Key documentation for deeper context:**
- [docs/DESIGN.md](docs/DESIGN.md) — Full architectural specification
- [README.md](README.md) — Project overview and quick start
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to add components
- [docs/customization/README.md](docs/customization/README.md) — Extending for organizations

---

## Directory Structure Convention

```
aws-coworker/
├── .claude/
│   ├── agents/          # Agent definitions (execution components)
│   └── commands/        # Slash commands (workflow triggers)
├── skills/              # Knowledge documents (NOT in .claude/)
│   ├── aws/             # AWS-focused skills
│   ├── org/             # Organization-specific policies
│   ├── meta/            # Meta-design skills
│   └── core/            # Non-AWS core skills
├── config/              # Configuration templates
├── docs/                # Documentation
└── examples/            # Example implementations
```

### Why This Structure?

**This is an intentional design decision, not an oversight:**

| Location | Contains | Rationale |
|----------|----------|-----------|
| `.claude/agents/` | Agent definitions | Claude Code convention for execution components |
| `.claude/commands/` | Slash commands | Claude Code convention for workflow triggers |
| `skills/` (root) | Knowledge & policy docs | Intentionally visible, human-maintainable, tool-agnostic |

**Skills are at repository root (not `.claude/skills/`) because:**
1. They are knowledge documents, not hidden tool configuration
2. They should be visible, browsable, and maintainable by humans
3. They can be referenced by tools other than Claude
4. Agents load them via explicit `Read` operations, so location is flexible

**Reference:** [docs/DESIGN.md#52-directory-structure-rationale](docs/DESIGN.md#52-directory-structure-rationale)

---

## Naming Conventions

All AWS Coworker components use the `aws-coworker-` prefix:

| Component | Pattern | Example |
|-----------|---------|---------|
| Agents | `aws-coworker-{role}.md` | `aws-coworker-planner.md` |
| Commands | `aws-coworker-{action}.md` | `aws-coworker-plan-interaction.md` |
| Skills | `{domain}-{name}/SKILL.md` | `aws-cli-playbook/SKILL.md` |

**File naming rules:**
- Lowercase with hyphens (not camelCase or underscores)
- `.md` for definitions and documentation
- `.yaml` for configuration

---

## Layered Architecture

AWS Coworker uses three layers with clear precedence:

```
┌─────────────────────────────────────┐
│  BU/Tenant Layer (most specific)    │  ← Optional team overlays
├─────────────────────────────────────┤
│  Organization Layer                 │  ← skills/org/, config/org-config/
├─────────────────────────────────────┤
│  Core Layer (batteries-included)    │  ← skills/aws/, skills/core/, skills/meta/
└─────────────────────────────────────┘
```

**Key principle:** Extend, don't modify core. Organization customizations go in designated directories.

---

## Component Relationships

### How Skills Are Loaded

1. Commands declare skills in frontmatter: `skills: [aws-cli-playbook, aws-governance-guardrails]`
2. Agents load skills using the `Read` tool when guidance is needed
3. Skills are knowledge/policy documents that inform agent behavior

### Agent Roster

| Agent | Role | Key Constraint |
|-------|------|----------------|
| `aws-coworker-core` | Primary orchestrator | Announces profile/region before any operation |
| `aws-coworker-planner` | Planning | No Bash mutations, read-only |
| `aws-coworker-executor` | Execution | Non-prod via CLI, prod via CI/CD generation |
| `aws-coworker-guardrail` | Compliance | Validates against governance skills |
| `aws-coworker-observability-cost` | Monitoring/cost | Read-only AWS CLI only |
| `aws-coworker-meta-designer` | Self-evolution | No AWS mutations, only modifies AWS Coworker itself |

### Command Roster

| Command | Purpose |
|---------|---------|
| `/aws-coworker-plan-interaction` | Plan AWS operations |
| `/aws-coworker-execute-nonprod` | Execute in non-production |
| `/aws-coworker-prepare-prod-change` | Generate CI/CD for production |
| `/aws-coworker-rollback-change` | Rollback procedures |
| `/aws-coworker-bootstrap-account` | New account setup |
| `/aws-coworker-new-skill-from-session` | Create skills from usage |
| `/aws-coworker-refactor-skills` | Improve existing skills |
| `/aws-coworker-audit-library` | Health check AWS Coworker |

---

## Safety Model

**These principles are non-negotiable:**

1. **Read-only by default** — Unknown/new profiles start read-only
2. **Announce before action** — Always state profile and region before any AWS CLI operation
3. **Explicit approval for mutations** — Destructive operations require human confirmation
4. **Production via CI/CD only** — Never direct CLI mutations to production
5. **Rollback ready** — Every execution plan includes rollback procedures
6. **Blast radius awareness** — Articulate scope and impact before changes

---

## Git/GitHub Workflow

- All changes via feature branches and pull requests
- Human review required before merge
- Tag releases for versioned baselines (e.g., `v1.0.0`, `baseline/pre-customization`)
- Never silently mutate production definitions

---

## When Adding New Components

### New Skill
1. Determine category: `aws/`, `org/`, `meta/`, or `core/`
2. Create directory: `skills/{category}/{skill-name}/`
3. Create `SKILL.md` with required frontmatter
4. Reference: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-new-skill)

### New Command
1. Create file: `.claude/commands/aws-coworker-{action}.md`
2. Include frontmatter with `description`, `skills`, `agent`, `tools`
3. Define workflow steps with approval checkpoints
4. Reference: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-new-command)

### New Agent (rare)
1. Justify why existing agents can't cover the use case
2. Create file: `.claude/agents/aws-coworker-{role}.md`
3. Define purpose, scope, allowed tools, behavior guidelines
4. Reference: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-new-agent)

---

## Key Design Decisions to Preserve

1. **Skills at root, not in `.claude/`** — Intentional for visibility and tool-agnosticism
2. **`aws-coworker-` prefix on all components** — Namespace consistency
3. **Agents load skills via Read** — Explicit loading, not auto-discovery
4. **Production changes generate CI/CD, not direct CLI** — Safety boundary
5. **Meta-designer agent can evolve AWS Coworker** — Self-improvement capability
6. **Layered customization** — Core → Org → BU precedence

---

## Quick Reference Commands

```bash
# Audit AWS Coworker health
/aws-coworker-audit-library

# Plan an AWS interaction
/aws-coworker-plan-interaction

# Create a new skill from conversation patterns
/aws-coworker-new-skill-from-session
```

---

## Files to Read for Full Context

If you need to understand AWS Coworker deeply after compression:

**For using AWS Coworker (interacting with AWS):**
1. **Usage context** — `CLAUDE.md` (mandatory — routes all AWS requests through commands)

**For developing/maintaining AWS Coworker:**
1. **This file** — `CLAUDE-DEVELOPMENT.md` (you're here)
2. **Architecture** — `docs/DESIGN.md`
3. **Contributing** — `CONTRIBUTING.md`
4. **Customization** — `docs/customization/README.md`
5. **Sample agent** — `.claude/agents/aws-coworker-core.md`
6. **Sample skill** — `skills/aws/aws-cli-playbook/SKILL.md`
7. **Sample command** — `.claude/commands/aws-coworker-plan-interaction.md`
