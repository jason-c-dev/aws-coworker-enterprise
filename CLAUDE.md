# CLAUDE.md - AWS Coworker Usage Instructions

**This file ensures all AWS interactions go through AWS Coworker's safety model.**

---

## Critical Instruction

**NEVER execute AWS CLI commands directly.** All AWS operations must go through AWS Coworker commands to ensure:

- Profile and region are announced before any operation
- Governance guardrails are consulted
- Mutations require explicit approval
- Production changes go through CI/CD, not direct CLI
- Rollback procedures are considered

---

## How to Handle AWS Requests

When a user asks anything related to AWS, route to the appropriate command:

| User Intent | Route To |
|-------------|----------|
| Discover/query AWS resources | `/aws-coworker-plan-interaction` (discovery mode) |
| Plan a change or deployment | `/aws-coworker-plan-interaction` |
| Execute in non-production | `/aws-coworker-execute-nonprod` |
| Deploy to production | `/aws-coworker-prepare-prod-change` |
| Rollback a change | `/aws-coworker-rollback-change` |
| Set up a new AWS account | `/aws-coworker-bootstrap-account` |
| Cost or monitoring questions | `/aws-coworker-plan-interaction` with observability focus |

### Trigger Patterns

**ANY request involving these keywords or concepts MUST route through AWS Coworker:**

- AWS services: S3, EC2, Lambda, RDS, VPC, IAM, CloudWatch, Cost Explorer, etc.
- AWS operations: list, describe, create, delete, start, stop, deploy, etc.
- Cost/billing: cost summary, spending, budget, billing, charges, usage
- Monitoring: metrics, alarms, logs, CloudWatch, dashboards
- Infrastructure: instances, buckets, databases, functions, networks

### Examples

When a user makes a free-form request, invoke the appropriate command and pass the user's request as context:

| User Says | Action |
|-----------|--------|
| "What S3 buckets exist?" | Invoke `/aws-coworker-plan-interaction` with goal: "Discover S3 buckets" |
| "List my EC2 instances" | Invoke `/aws-coworker-plan-interaction` with goal: "List EC2 instances" |
| "Create a new VPC" | Invoke `/aws-coworker-plan-interaction` with goal: "Create a new VPC" |
| "Show me my AWS costs" | Invoke `/aws-coworker-plan-interaction` with goal: "Retrieve cost summary" |
| "What's my spending this month?" | Invoke `/aws-coworker-plan-interaction` with goal: "Cost analysis" |
| "Check CloudWatch alarms" | Invoke `/aws-coworker-plan-interaction` with goal: "Review CloudWatch alarms" |
| "Deploy this to staging" | Invoke `/aws-coworker-execute-nonprod` with the user's deployment context |
| "Push to production" | Invoke `/aws-coworker-prepare-prod-change` with the user's change context |
| "Undo the last change" | Invoke `/aws-coworker-rollback-change` with details of what to roll back |

**When in doubt, route through `/aws-coworker-plan-interaction`.** It's always safer to go through the safety model than to execute AWS CLI directly.

**Invocation pattern:** When invoking a command on behalf of the user, pass their original request as the input/goal so the command workflow has full context of what the user wants to achieve.

---

## Safety Model (Non-Negotiable)

1. **Announce before action** — Always state AWS profile and region before any operation
2. **Read-only by default** — Unknown profiles are treated as read-only
3. **Explicit approval for mutations** — Never modify resources without user confirmation
4. **Production is protected** — Production changes generate CI/CD artifacts, not direct CLI
5. **Consult guardrails** — Check `skills/org/aws-governance-guardrails/` before mutations

---

## AWS Profile Handling

Before ANY AWS operation:

1. Identify which profile will be used
2. State it explicitly: "I will use profile `{profile}` in region `{region}`"
3. If profile is unknown/new, treat as read-only until configured
4. Check environment classification (sandbox/dev/staging/prod)

---

## Quick Reference: Available Commands

| Command | Purpose |
|---------|---------|
| `/aws-coworker-plan-interaction` | Plan any AWS operation (start here) |
| `/aws-coworker-execute-nonprod` | Execute approved plan in non-prod |
| `/aws-coworker-prepare-prod-change` | Generate CI/CD changes for production |
| `/aws-coworker-rollback-change` | Design and execute rollback |
| `/aws-coworker-bootstrap-account` | Set up new AWS account |
| `/aws-coworker-audit-library` | Audit AWS Coworker health |

---

## What NOT to Do

❌ `aws s3 ls` — Direct CLI without going through AWS Coworker
❌ `aws ec2 describe-instances` — Even read-only should announce profile first
❌ `aws ce get-cost-and-usage` — Cost queries should also go through AWS Coworker
❌ `aws cloudwatch get-metric-data` — Monitoring queries need profile announcement
❌ `aws ec2 terminate-instances` — Never without plan, approval, and guardrail check
❌ Any AWS CLI in production — Must go through CI/CD

**Rule of thumb:** If it starts with `aws `, it MUST go through AWS Coworker.

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

Simple tasks like "list my S3 buckets" work perfectly fine — they use a single agent rather than spawning parallel workers. The overhead is minimal; the consistency benefits are significant.

### Model Hierarchy

AWS Coworker uses a tiered model strategy for cost efficiency:

| Role | Model | Purpose |
|------|-------|---------|
| **Primary (Orchestrator)** | Your selected model (Opus, Sonnet, etc.) | Orchestration, threshold evaluation, user communication, result synthesis |
| **Sub-Agents (Read-Only)** | Haiku | Fast parallel discovery, audits, cost analysis |
| **Sub-Agents (Mutations)** | Sonnet | Thorough state-change analysis |

**Why this matters:** If you run AWS Coworker with Opus 4.5, Opus handles the "thinking" while Haiku does the parallelized "doing" — best quality where it counts, optimized cost at scale.

### Configurable Thresholds

Thresholds determine **how many agents** to spawn, not **whether** to spawn agents.

**Configuration:** `.claude/config/orchestration-config.md`

| Factor | Single Agent | Parallel Agents |
|--------|--------------|-----------------|
| Resources | < 50 | >= 50 |
| Regions | <= 3 | > 3 |
| Accounts | <= 3 | > 3 |
| Est. Time | < 5 min | > 5 min (advise user) |

### User Advisement

For tasks above thresholds, advise the user before proceeding:

```
This task involves:
- 847 resources across 8 regions
- Estimated time: 8-10 minutes

I'll work in parallel (8 agents) to minimize time. Do you want to proceed?
```

### Permission Delegation

When spawning sub-agents via the Task tool:
1. Read thresholds from `.claude/config/orchestration-config.md`
2. Pass the user's explicit approval scope
3. Constrain sub-agent to approved actions only
4. Sub-agents cannot expand scope beyond user's approval

### Result Aggregation

After execution (single or parallel):
1. Wait for all sub-agents to complete
2. Merge results into coherent summary
3. Present unified response to user
4. Note any partial failures clearly

---

## For Developers Maintaining AWS Coworker

If you are working on AWS Coworker itself (adding skills, commands, agents), see:

- [CLAUDE-DEVELOPMENT.md](CLAUDE-DEVELOPMENT.md) — Development context and conventions
- [docs/DESIGN.md](docs/DESIGN.md) — Full architectural specification
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to contribute

---

## Skills Reference

AWS Coworker agents use these skills for guidance:

| Skill | Purpose |
|-------|---------|
| `skills/aws/aws-cli-playbook/` | AWS CLI patterns for all services |
| `skills/aws/aws-well-architected/` | Well-Architected Framework alignment |
| `skills/aws/aws-governance-guardrails/` | Never-do / always-do policies |
| `skills/org/aws-org-strategy/` | Organization's account structure |

Commands load the appropriate skills automatically. You don't need to read them manually unless debugging.
