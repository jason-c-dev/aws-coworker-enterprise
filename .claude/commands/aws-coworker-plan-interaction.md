---
description: Plan how to interact with AWS for a particular task or change
skills: [aws-cli-playbook, aws-well-architected, aws-org-strategy, aws-governance-guardrails]
agent: aws-coworker-planner
tools: [Read, Glob, Grep, Bash]
arguments:
  - name: objective
    description: What you want to accomplish with AWS
    required: true
  - name: environment
    description: Target environment (sandbox, development, staging, production)
    required: false
    default: development
---

# /aws-coworker-plan-interaction

## Overview

Plan an AWS interaction by understanding requirements, discovering current state, designing a safe execution plan, and validating against governance policies.

## Prerequisites

- AWS CLI configured with appropriate profile
- Understanding of the desired outcome
- Knowledge of target environment

---

## Workflow

### Step 1: Gather Requirements

Ask the user to clarify:

1. **Objective**: What do you want to accomplish?
2. **Scope**: What resources are involved?
3. **Environment**: Which environment (sandbox/dev/staging/prod)?
4. **Constraints**: Any specific requirements or limitations?

```
Example questions:
- "What's the end goal of this interaction?"
- "Which AWS account/environment should this target?"
- "Are there any specific constraints I should know about?"
```

### Step 2: Identify Profile and Region

Based on the target environment:

1. Determine appropriate AWS profile
2. Confirm target region
3. Announce before any AWS operations:

```
I will use:
- Profile: {profile-name}
- Region: {region}
- Environment classification: {sandbox|development|staging|production}

This is a planning session - I will only run read-only discovery commands.
```

### Step 3: Discovery and Scope Estimation (Always-Agent Mode)

**Configuration:** Read thresholds from `.claude/config/orchestration-config.md`

Run read-only AWS CLI commands to understand current state and estimate task complexity:

#### 3a: Initial Discovery

```bash
# Identity check
aws sts get-caller-identity --profile {profile}

# Resource-specific discovery (examples)
aws ec2 describe-instances --profile {profile} --region {region}
aws ec2 describe-vpcs --profile {profile} --region {region}
aws s3 ls --profile {profile}
```

Load relevant information from:
- `aws-cli-playbook` skill for command patterns
- `aws-org-strategy` skill for account/OU context
- `.claude/config/orchestration-config.md` for thresholds
- Existing infrastructure state

#### 3b: Scope Estimation Against Thresholds

After discovery, compare scope against configurable thresholds:

```markdown
## Scope Assessment

### Resources Involved
- Resource count: {number}
- Regions: {list}
- Accounts: {list if multi-account}

### Threshold Evaluation (from orchestration-config.md)
| Factor | Value | Threshold | Result |
|--------|-------|-----------|--------|
| Resources | {count} | single: <50, parallel: >=50 | {single/parallel} |
| Regions | {count} | single: <=3, parallel: >3 | {single/parallel} |
| Accounts | {count} | single: <=3, parallel: >3 | {single/parallel} |
| Est. Time | {minutes} | advise: >5min, approve: >10min | {advise/approve/none} |

### Execution Decision
- Mode: {single_agent | parallel_agents}
- Agent count: {N}
- Partitioning: {by_region | by_account | by_batch | none}

### User Advisement (if above thresholds)
```

**Always-Agent Mode Note:** Every request spawns at least one agent. Thresholds determine whether to use a single agent (sequential) or multiple agents (parallel).

If above thresholds (resources >= 50, regions > 3, or estimated > 5 minutes):

```
This task involves:
- {X} resources across {Y} regions
- Estimated time: {Z} minutes

I'll work in parallel ({N} agents). Do you want to proceed?
```

Wait for user confirmation before continuing with parallel operations.

### Step 4: Design the Plan

Using the planner agent and skills:

1. **Load skills**:
   - `aws-cli-playbook` for command patterns
   - `aws-well-architected` for architectural alignment
   - `aws-governance-guardrails` for policy compliance

2. **Create detailed plan** following this structure:

```markdown
# Plan: {Objective}

## Summary
[1-2 sentence summary]

## Target
- Environment: {environment}
- Profile: {profile}
- Region: {region}

## Prerequisites
- [What must be in place]

## Current State
[Discovery findings]

## Proposed Changes

### Phase 1: {Phase Name}
**Actions:**
1. {action}
2. {action}

**Commands:**
```bash
{commands}
```

**Expected Outcome:**
{what should happen}

**Validation:**
```bash
{validation commands}
```

### Phase 2: {Phase Name}
...

## Well-Architected Assessment

| Pillar | Status | Notes |
|--------|--------|-------|
| Operational Excellence | ✅/⚠️/❌ | |
| Security | ✅/⚠️/❌ | |
| Reliability | ✅/⚠️/❌ | |
| Performance Efficiency | ✅/⚠️/❌ | |
| Cost Optimization | ✅/⚠️/❌ | |
| Sustainability | ✅/⚠️/❌ | |

## Governance Compliance

- [ ] Tagging requirements
- [ ] IAM least privilege
- [ ] Encryption requirements
- [ ] Network policies
- [ ] Environment policies

## Rollback Procedure

### If Phase 1 fails:
{rollback steps}

### If Phase 2 fails:
{rollback steps}

## Estimated Impact
- Blast radius: {scope}
- Risk level: {Low/Medium/High}
- Cost impact: {estimate}
```

### Step 5: Guardrail Validation

Submit the plan to `aws-coworker-guardrail` for validation:

1. Check against `aws-governance-guardrails`
2. Verify tagging compliance
3. Validate security requirements
4. Check environment-specific rules

Present findings:
```markdown
## Guardrail Validation

**Status**: {PASS|WARN|FAIL}

### Findings
{any issues or concerns}

### Required Changes
{if any}
```

### Step 6: Present Plan for Approval

Present the complete plan to the user:

```
Here's the plan for {objective}:

[Plan summary]

Key points:
- {point 1}
- {point 2}
- {point 3}

Guardrail validation: {status}

Do you want to:
1. Approve and proceed to execution
2. Request modifications
3. Cancel
```

---

## Output

The command produces:
1. **Detailed execution plan** with commands and validation steps
2. **Guardrail validation report** with compliance status
3. **Risk assessment** with blast radius and rollback procedures

---

## Next Steps

After plan approval:

- **For non-prod**: Run `/aws-coworker-execute-nonprod` to execute
- **For production**: Run `/aws-coworker-prepare-prod-change` to generate CI/CD changes

---

## Always-Agent Mode Orchestration

**Configuration:** `.claude/config/orchestration-config.md`

AWS Coworker operates in Always-Agent Mode: every request spawns at least one agent. Thresholds determine whether to use single or parallel execution.

### Threshold Reference (from config)

| Factor | Single Agent | Parallel Agents |
|--------|--------------|-----------------|
| Resources | < 50 | >= 50 |
| Regions | <= 3 | > 3 |
| Accounts | <= 3 | > 3 |
| Est. Time | < 5 min | > 5 min (advise), > 10 min (require approval) |

### Partitioning Strategies

| Strategy | Use When |
|----------|----------|
| `by_region` | Multi-region operations |
| `by_account` | Multi-account operations |
| `by_batch` | Large homogeneous resource sets |
| `hybrid` | Complex cross-cutting operations |

### Parallel Execution Pattern

For operations above thresholds, delegate to sub-agents:

```yaml
# Example: Multi-region audit (8 regions, above threshold)
partitions:
  - region: us-east-1
    task: "Audit S3 buckets for public access"
  - region: us-west-2
    task: "Audit S3 buckets for public access"
  - region: eu-west-1
    task: "Audit S3 buckets for public access"
  # ... (5 more regions)

# Model selection (from config):
# - read_only operations: haiku (fast)
# - mutations: sonnet (thorough)
```

### User Communication During Operations

```
Starting audit with 8 parallel agents (one per region)...

Progress:
├── us-east-1: Scanning 150 buckets... ✓
├── us-west-2: Scanning 120 buckets... ✓
├── eu-west-1: Scanning 100 buckets... [in progress]
├── ap-southeast-1: Scanning 95 buckets... [queued]
...

Completed: 4/8 regions (50%)
Estimated remaining: 2 minutes
```

### Single Agent Execution (Below Thresholds)

For simple tasks (below all thresholds), a single agent handles the request sequentially:

```
[Single agent executing]

Listing EC2 instances in us-east-1...

Found 4 instances:
- i-abc123 (running) - web-server
- i-def456 (running) - api-server
...
```

---

## Error Handling

### Insufficient Permissions

```
Discovery failed due to insufficient permissions.

Profile: {profile}
Operation: {operation}
Error: {error}

Please verify:
1. Correct profile selected
2. Profile has required read permissions
3. Region is correct
```

### Unclear Requirements

```
I need more information to create a complete plan:

Missing:
- {missing info 1}
- {missing info 2}

Please provide additional details.
```
