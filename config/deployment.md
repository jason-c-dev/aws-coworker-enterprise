# AWS Coworker — Deployment Manifest

This file describes AWS Coworker as a deployable application. When the orchestrator is asked to deploy AWS Coworker (i.e. deploy *itself*), it should read this manifest to understand the application's specific requirements.

**Why this exists:** The MVA baseline for Bedrock AgentCore describes generic platform requirements — IAM roles, ECR, VPC, tags. But AWS Coworker has application-specific dependencies that the generic baseline cannot know about. This manifest bridges the gap between "deploy an agent to AgentCore" and "deploy *this* agent to AgentCore."

Without this file, the orchestrator treats AWS Coworker as a generic AgentCore workload and misses critical configuration. The agent doesn't know it's deploying itself unless we tell it.

---

## Application Identity

| Field | Value |
|-------|-------|
| Name | AWS Coworker |
| Runtime | Claude Code (`@anthropic-ai/claude-code`) |
| Inference backend | Amazon Bedrock (via IAM roles) |
| Dockerfile | `tests/assets/Dockerfile.aws-coworker` |

---

## Critical Configuration

### CLAUDE_CODE_USE_BEDROCK=1

This environment variable **must** be set in the container. It tells Claude Code to use IAM-based Bedrock model access instead of an Anthropic API key.

- **Without it:** Claude Code looks for `ANTHROPIC_API_KEY`, finds nothing, and fails to start
- **With it:** Claude Code uses the agent runtime IAM role to call `bedrock:InvokeModel` — no secrets needed

This is the most important configuration detail for deploying AWS Coworker to AgentCore. It must appear in the Dockerfile (`ENV CLAUDE_CODE_USE_BEDROCK=1`) or in the AgentCore runtime environment configuration.

---

## Required Bedrock Models

AWS Coworker uses a tiered model strategy. All three tiers must be available in the target account and region.

| Role | Model | Purpose | Impact if missing |
|------|-------|---------|-------------------|
| Orchestrator | Opus (e.g. `anthropic.claude-opus-*`) | Planning, reasoning, enforcement decisions, user communication | **Fatal** — AWS Coworker cannot function without an orchestrator |
| Mutation agents | Sonnet (e.g. `anthropic.claude-sonnet-*`) | Executing state changes (create, delete, modify) | Mutations fail — read-only mode only |
| Discovery agents | Haiku (e.g. `anthropic.claude-haiku-*`) | Read-only AWS CLI queries, parallel discovery | Discovery fails — no resource visibility |

**IAM requirement:** The agent runtime role must include `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` scoped to these model families:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:{region}::foundation-model/anthropic.claude-opus-*",
    "arn:aws:bedrock:{region}::foundation-model/anthropic.claude-sonnet-*",
    "arn:aws:bedrock:{region}::foundation-model/anthropic.claude-haiku-*"
  ]
}
```

---

## Container Contents

The container must include the AWS Coworker repository contents so Claude Code can find its skills, commands, agents, and configuration:

| Path in container | Source | Purpose |
|-------------------|--------|---------|
| `/opt/aws-coworker/CLAUDE.md` | Repository root | Entry point — Claude Code reads this on startup |
| `/opt/aws-coworker/skills/` | `skills/` | AWS CLI playbooks, MVA baselines, governance guardrails |
| `/opt/aws-coworker/.claude/` | `.claude/` | Agent definitions, commands, config |
| `/opt/aws-coworker/config/` | `config/` | Environment config, orchestration config, this manifest |

---

## System Dependencies

| Dependency | Why | Install method |
|------------|-----|----------------|
| Node.js | Claude Code runtime | `dnf install nodejs` |
| AWS CLI v2 | Sub-agents execute AWS commands | Official installer |
| Git | Repository operations | `dnf install git` |
| jq | JSON processing in scripts | `dnf install jq` |

---

## Health Check

```bash
claude --version && aws --version
```

Both must succeed for the container to be considered healthy.

---

## Notes

- This manifest is for deploying AWS Coworker specifically. Other agents deployed to AgentCore will have their own deployment requirements.
- The generic AgentCore MVA baseline (`skills/aws/aws-well-architected/mva-baselines/bedrock-agentcore.md`) covers platform requirements. This manifest covers application requirements. Both apply.
- The MVA baseline's gap detection for "Agent's model invocation configured via IAM" and "Required Bedrock foundation models enabled" both reference "the application's deployment manifest" — that's this file.
