# Getting Started with AWS Coworker

Welcome to AWS Coworker! This guide will help you get up and running quickly.

---

## What is AWS Coworker?

AWS Coworker is a **production-ready system** built on [Claude Code](https://claude.ai/code) and Anthropic's Claude Agent SDK. It augments AWS best practices with Claude's agentic capabilities for safe, effective infrastructure management.

**The core works out of the box.** The layered architecture lets you extend it for your organization's needs.

### What You Get

| From Claude Code | From AWS Coworker |
|------------------|-------------------|
| Agent architecture (Task tool) | Pre-configured agents for AWS operations |
| Skill system | AWS CLI patterns, Well-Architected guidance |
| Slash commands | Safety-first workflows with approval gates |
| Model flexibility | Cost-optimized model hierarchy (Opus/Sonnet/Haiku) |

> **Important:** AWS Coworker augments—it doesn't replace—your expertise. You remain responsible for what it does to your AWS account(s). Always review plans before execution, especially for production workloads. See the [full notice in README](../../README.md#important-notice).

---

## What You'll Learn

1. How to set up AWS Coworker with Claude Code
2. How to run your first AWS interaction
3. How to understand AWS Coworker's safety model
4. Where to go for more advanced usage

**Time estimate:** 15-30 minutes

---

## Prerequisites

Before starting, ensure you have:

### Required

- [ ] **Claude Code** or compatible Claude environment
- [ ] **AWS CLI** installed and configured
  ```bash
  aws --version
  # Should show: aws-cli/2.x.x ...
  ```
- [ ] **Git** installed
  ```bash
  git --version
  # Should show: git version 2.x.x
  ```
- [ ] **At least one AWS profile** configured
  ```bash
  aws configure list
  # Should show configured profile
  ```

### Recommended

- [ ] GitHub CLI (`gh`) for easier PR workflows
- [ ] A sandbox/development AWS account for learning
- [ ] Familiarity with AWS services you'll be working with

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/aws-coworker-enterprise.git
cd aws-coworker-enterprise
```

### Step 2: Verify AWS Access

```bash
# Check you can reach AWS
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAEXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/youruser"
# }
```

### Step 3: Review Your Profiles

```bash
# List configured profiles
aws configure list-profiles

# Check a specific profile
aws configure list --profile your-profile-name
```

### Step 4: Open in Claude Code

Open the `aws-coworker-enterprise` directory in Claude Code. AWS Coworker leverages Claude Code's built-in capabilities:

- **Task tool** — For spawning specialized sub-agents
- **Skill system** — For loading AWS patterns and policies
- **Slash commands** — For triggering workflows
- **Model selection** — For cost-optimized execution

When you open this directory, Claude automatically reads `CLAUDE.md` and routes all AWS-related requests through the safety model.

---

## Your First Interaction

### Understanding the Safety Model

Before running commands, understand AWS Coworker's safety approach:

1. **Read-only by default** — Discovery operations don't modify anything
2. **Profile announcement** — Always told which profile/region will be used
3. **Explicit approval** — Mutations require your confirmation
4. **Blast radius awareness** — Impact is disclosed before changes

### Try a Discovery Operation

Start with a read-only discovery:

```
User: What EC2 instances are running in my account?

AWS Coworker will:
1. Route the request through /aws-coworker-plan-interaction
2. State the profile and region it will use
3. Run read-only discovery commands
4. Present findings without modifying anything
```

> **Note:** All AWS-related requests—whether commands like `/aws-coworker-plan-interaction` or free-form prompts like the one above—are automatically routed through AWS Coworker commands. The [CLAUDE.md](../../CLAUDE.md) configuration enforces this safety model.

### Plan an Interaction

Use the planning command for more complex operations:

```
/aws-coworker-plan-interaction

This will:
1. Ask what you want to accomplish
2. Generate a detailed plan
3. Show proposed commands
4. Wait for your approval before any execution
```

---

## Key Concepts

### How AWS Coworker Uses Claude Code

AWS Coworker builds on Claude Code's agent architecture:

```
Your Request
     │
     ▼
CLAUDE.md (routes AWS requests)
     │
     ▼
Slash Command (workflow orchestration)
     │
     ▼
Primary Agent (your selected model: Opus, Sonnet)
     │
     ├── Reads Skills (AWS patterns, policies)
     │
     └── Spawns Sub-Agents via Task tool
              │
              ├── Haiku agents (fast read-only work)
              └── Sonnet agents (mutations requiring care)
```

### Agents

AWS Coworker defines specialized agents using Claude Code's Task tool:

| Agent | Role |
|-------|------|
| Core | Primary interaction orchestrator |
| Planner | Creates plans without executing |
| Executor | Runs approved plans (non-prod) |
| Guardrail | Validates compliance |

### Skills

Skills use Claude Code's skill system to provide reference patterns and policies:

| Category | Examples |
|----------|----------|
| `aws/` | CLI playbooks, Well-Architected guidance |
| `org/` | Your organization's policies |
| `meta/` | AWS Coworker self-management |
| `core/` | Git, documentation standards |

### Commands

Slash commands orchestrate workflows:

| Command | Purpose |
|---------|---------|
| `/aws-coworker-plan-interaction` | Plan AWS operations |
| `/aws-coworker-execute-nonprod` | Execute in non-prod |
| `/aws-coworker-audit-library` | Check AWS Coworker health |

---

## Common First Tasks

### 1. Inventory Your Resources

```
"Show me all S3 buckets in this account"
"What VPCs exist and what's their CIDR ranges?"
"List all IAM roles with admin permissions"
```

### 2. Check Compliance

```
"Are there any public S3 buckets?"
"Which EC2 instances are missing required tags?"
"Show me security groups with 0.0.0.0/0 ingress"
```

### 3. Plan a Change

```
/aws-coworker-plan-interaction

"I need to add a new tag to all EC2 instances in the dev environment"
```

---

## Safety Guardrails

AWS Coworker has built-in safety measures:

### Environment Classification

| Environment | CLI Access |
|-------------|------------|
| Sandbox | Read-write |
| Development | Read-write with approval |
| Staging | Read-only (changes via IaC) |
| Production | Read-only (changes via CI/CD) |

### Approval Requirements

| Operation Type | Approval Needed |
|----------------|-----------------|
| Discovery (read-only) | None |
| Non-destructive creation | Confirmation |
| Destructive changes | Explicit approval |
| Production changes | Via CI/CD only |

### Profile Safety

- Unknown profiles default to read-only
- Production profiles restricted to read-only
- Profile/region always announced before operations

---

## Next Steps

### Customize for Your Organization

See the [Customization Guide](../customization/README.md) to:

- Add organization-specific policies
- Configure your account structure
- Set up tagging standards

### Learn Advanced Workflows

Explore these guides:

- [Common Workflows](common-workflows.md) — Detailed workflow examples
- [Installation Deep Dive](installation.md) — Advanced setup options

### Contribute

Found a gap or improvement? See [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## Troubleshooting

### "No AWS profile configured"

```bash
# Configure a profile
aws configure --profile your-profile-name

# Or set environment variables
export AWS_PROFILE=your-profile-name
export AWS_DEFAULT_REGION=us-east-1
```

### "Access denied" errors

1. Check your profile has appropriate permissions
2. Verify you're using the intended profile
3. Check for SCPs or permission boundaries

### Commands not recognized

Ensure you're in the AWS Coworker directory and using a compatible Claude environment.

---

## Getting Help

- **Documentation**: Browse the `docs/` directory
- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions for questions

Welcome to AWS Coworker! 🚀
