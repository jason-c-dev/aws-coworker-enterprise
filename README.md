# AWS Coworker

**A batteries-included, fully extensible meta-system of agents, skills, and slash commands for enterprise AWS interaction.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is AWS Coworker?

AWS Coworker is a framework for safely and effectively interacting with AWS in enterprise environments. It provides:

- **Reference Library** — Pre-built agents, skills, and workflows for common AWS operations
- **Safety-First Design** — Read-only defaults, explicit approvals for mutations, blast radius awareness
- **GitOps Native** — All changes via branches and pull requests with human review
- **Self-Evolving** — Meta-layer that can create and refine its own capabilities based on usage
- **Enterprise Ready** — Supports single-account through complex multi-account Organizations

AWS Coworker is **not** an application architecture framework—it's a platform for *interacting with AWS* safely and consistently.

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
┌─────────────────────────────────────────────────────────────┐
│                      SLASH COMMANDS                         │
│                   (Workflow Orchestration)                  │
├─────────────────────────────────────────────────────────────┤
│                         AGENTS                              │
│   Core │ Planner │ Executor │ Guardrail │ Obs/Cost │ Meta  │
├─────────────────────────────────────────────────────────────┤
│                         SKILLS                              │
│        aws/ │ org/ │ meta/ │ core/                         │
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
│   └── commands/        # Slash command definitions
├── skills/
│   ├── aws/             # AWS-focused skills
│   ├── org/             # Organization-specific
│   ├── meta/            # Meta-design skills
│   └── core/            # Non-AWS core skills
├── config/              # Configuration templates
├── docs/                # Documentation
└── examples/            # Example implementations
```

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
