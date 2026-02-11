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

Run read-only AWS CLI commands to understand current state and estimate task complexity.

#### CRITICAL: Sub-Agents Must Use Agent Identity (NOT Raw Bash)

**When spawning sub-agents, use the defined agent identities from `.claude/agents/`.**

```
CORRECT (agent identity with model):
⏺ Task(Discover VPC state) Haiku 4.5
  prompt: "You are acting as aws-coworker-planner..."
  ⎿  Done (2 tool uses)

WRONG (raw Bash - no agent context):
⏺ 3 Bash agents finished
   ├─ Verify AWS identity
```

**Sub-agent invocation pattern (from agent definitions):**

For discovery (read-only):
```yaml
Task:
  description: "Discover VPC and subnet state"
  subagent_type: "general-purpose"    # NOT "Bash"
  model: "haiku"
  prompt: |
    You are acting as aws-coworker-planner.

    ## Permission Context
    Operation type: read-only (discovery only)

    ## Target
    Profile: {profile}
    Region: {region}

    ## Task
    Run these discovery commands and report findings:
    aws ec2 describe-vpcs --profile {profile} --region {region}
```

For mutations (after approval):
```yaml
Task:
  description: "Create security group"
  subagent_type: "general-purpose"    # NOT "Bash"
  model: "sonnet"
  prompt: |
    You are acting as aws-coworker-executor.

    ## Permission Context
    User has approved this operation.

    ## Target
    Profile: {profile}
    Region: {region}

    ## Approved Actions
    {specific mutation commands}
```

**Model selection rules:**
| Operation Type | Agent Identity | Model |
|----------------|----------------|-------|
| Discovery / Read-only | aws-coworker-planner | `haiku` |
| Mutations / Write | aws-coworker-executor | `sonnet` |

**DO NOT:**
- Use `subagent_type: "Bash"` (bypasses agent context)
- Spawn "Bash agents" directly
- Omit agent identity from prompt

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

### Step 4a: Well-Architected Evaluation (Orchestrator-Inline)

This step is performed by the orchestrator (primary model) directly — NOT delegated to a sub-agent. WAR assessment is a reasoning task that belongs at the orchestration layer.

**DO NOT skip this step. DO NOT self-certify with green checkmarks. DO NOT defer to the planner.**

1. **Read** the environment's `well_architected.enforcement` level from `config/environments/environments.yaml`
2. **Read** `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions and the WAR Findings Format
3. **Identify** the primary service(s) being deployed or modified
4. **Check service appropriateness** — Is this the right service for the use case? (A perfectly configured EC2 is still wrong for hosting a static HTML file.)
5. **Read** `skills/aws/aws-well-architected/mva-baselines/{service}.md` for the service MVA baseline
6. **Load org/BU extensions** if they exist in `skills/org/aws-mva-extensions/` or `skills/bu/`
7. **Evaluate** the proposed change against MVA items for the target environment tier
8. **Assign statuses** using the **planning context** status set (this is a plan, not a review of existing infrastructure):
   - **REMEDIATE** — The plan includes the fix for this gap. Default for everything enforcement requires.
   - **ACCEPTABLE** — Gap exists, plan doesn't address it, acceptable at this tier per enforcement rules.
   - **BLOCKED** — Gap exists, enforcement requires resolution but the user asked to skip it. Must be resolved.
9. **Apply execution gate:**
   - If enforcement=`optional`: Show findings, proceed (all gaps are ACCEPTABLE)
   - If enforcement=`warn`: Show findings, all gaps ACCEPTABLE but user warned
   - If enforcement=`strict`: Critical/High gaps are BLOCKED unless REMEDIATE; Medium/Low are ACCEPTABLE
   - If enforcement=`enforce`: ALL gaps are BLOCKED unless REMEDIATE; no override path

**The agent's default is to REMEDIATE everything enforcement requires.** BLOCKED only fires when the user explicitly asks to skip a required item.

**Apply statuses mechanically based on severity and enforcement level.** All items at the same severity get the same treatment — the agent does not exercise discretion about which items to block and which to allow at a given severity. If encryption (Critical) is BLOCKED, every Critical item is BLOCKED.

**DO NOT** proceed past a BLOCKED item without the user modifying the proposed architecture.
**DO NOT** allow the planner to self-generate WAR assessments — the orchestrator evaluates.
**DO NOT** use PASS for items in a plan — nothing can "pass" when it doesn't exist yet. Use REMEDIATE.
**DO NOT** offer "accept gaps explicitly" or similar escape hatches at `strict` or `enforce` enforcement for items at or above the blocking threshold. Enforcement gates are not negotiable at runtime — to change what enforcement requires, modify `config/environments/environments.yaml`.

After presenting the plan, offer the user override options:
- REMEDIATE items: user can say "skip {item}" → becomes ACCEPTABLE (if enforcement allows) or stays BLOCKED
- ACCEPTABLE items: user can say "add {item}" → becomes REMEDIATE
- BLOCKED items: cannot be downgraded — user must modify the plan or change `config/environments/environments.yaml`

The WAR findings from this step are passed to the planner in Step 4b and included in the plan output.

---

### Step 4b: Design the Plan

Using the planner agent and skills, incorporating the WAR findings from Step 4a:

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

## Well-Architected Assessment (from Step 4a — orchestrator-generated)

### Summary
- Service(s): {list of services being deployed/modified}
- Environment: {tier}
- Enforcement: {level from environments.yaml}
- Overall: COMPLIANT | GAPS_NOTED | CRITICAL_GAPS

### Service Appropriateness
- Use case: {what the user wants to achieve}
- Proposed service: {service}
- Assessment: APPROPRIATE | INAPPROPRIATE
- If inappropriate: Recommended alternative: {service} — {reason}

### MVA Baseline Comparison (Planning Context)

| Pillar | MVA Item | Status | Detail | Severity | Remediation |
|--------|----------|--------|--------|----------|-------------|
| {pillar} | {item} | REMEDIATE / ACCEPTABLE / BLOCKED | {what plan does or why acceptable/blocked} | {severity} | {how plan fixes it} |

### User Overrides Available
- REMEDIATE items: say "skip {item}" to accept the gap instead
- ACCEPTABLE items: say "add {item}" to include remediation in plan
- BLOCKED items: must be resolved; modify the plan to address these

### Execution Gate
- Gate: PROCEED | WARN_AND_PROCEED | BLOCKED
- REMEDIATE items: {count} (plan addresses these)
- ACCEPTABLE items: {count} (user informed)
- BLOCKED items: {count} (must resolve)

## Governance Compliance

- [ ] Tagging requirements (ALL resources, not just primary)
- [ ] IAM least privilege
- [ ] Encryption requirements
- [ ] Network policies
- [ ] Environment policies

## Resource Tagging Plan

**CRITICAL:** ALL resources created must be tagged at creation time. This includes supporting resources, not just the primary resource.

### Resources That MUST Be Tagged

| Resource Type | How to Tag |
|---------------|------------|
| EC2 Instance | `--tag-specifications 'ResourceType=instance,Tags=[...]'` |
| EBS Volume | `--tag-specifications 'ResourceType=volume,Tags=[...]'` (in run-instances) |
| Security Group | `--tag-specifications 'ResourceType=security-group,Tags=[...]'` |
| Key Pair | `--tag-specifications 'ResourceType=key-pair,Tags=[...]'` |
| S3 Bucket | `aws s3api put-bucket-tagging` (separate command after create) |
| RDS Instance | `--tags` parameter |
| Lambda Function | `--tags` parameter |

### Tagging Plan for This Request

| Resource | Tags to Apply |
|----------|---------------|
| {resource 1} | Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate |
| {resource 2} | Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate |
| {EBS volumes} | Same tags as EC2 instance |
| {key pairs} | Same tags as EC2 instance |
| {security groups} | Same tags as EC2 instance |

**Tag values for this plan:**
- `Name`: {descriptive name for resource}
- `Environment`: {environment}
- `Owner`: {owner from profile or user}
- `CostCenter`: {cost center or CC-00000 placeholder}
- `Application`: {application name}
- `CreatedBy`: aws-coworker
- `CreatedDate`: {today's date YYYY-MM-DD}

**Example EC2 with all resources tagged:**
```bash
aws ec2 run-instances ... \
  --tag-specifications \
    'ResourceType=instance,Tags=[{Key=Name,Value=...},{Key=Environment,Value=...},...]' \
    'ResourceType=volume,Tags=[{Key=Name,Value=...},{Key=Environment,Value=...},...]'
```

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

---

**Next Step (REQUIRED):**
- Non-prod: Run `/aws-coworker-execute-nonprod`
- Production: Run `/aws-coworker-prepare-prod-change`

Do you want to:
1. **Approve this plan** — I will then run the appropriate execute command
2. **Request modifications** — Adjust the plan before approval
3. **Cancel** — Abandon this plan
```

**CRITICAL:** After user approves, you MUST invoke `/aws-coworker-execute-nonprod` (or `/aws-coworker-prepare-prod-change` for production). Do NOT execute AWS CLI commands directly.

---

## Output

The command produces:
1. **Detailed execution plan** with commands and validation steps
2. **Guardrail validation report** with compliance status
3. **Risk assessment** with blast radius and rollback procedures
4. **Explicit next step** — Which command to run for execution

---

## What Happens After Approval

**This is mandatory, not optional:**

```
┌─────────────────────────────────────────────────────────────────┐
│  User approves plan                                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  YOU MUST invoke /aws-coworker-execute-nonprod                  │
│  (or /aws-coworker-prepare-prod-change for production)          │
│                                                                 │
│  ❌ DO NOT run AWS CLI commands directly                        │
│  ❌ DO NOT treat approval as permission to execute inline       │
└─────────────────────────────────────────────────────────────────┘
```

- **For non-prod**: Invoke `/aws-coworker-execute-nonprod` with the approved plan
- **For production**: Invoke `/aws-coworker-prepare-prod-change` to generate CI/CD changes

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
