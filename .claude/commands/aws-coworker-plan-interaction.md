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

### Step 2: Identify Profile, Region, and Classify Environment

Based on the target environment, determine the AWS profile, region, and environment classification using this **fallback chain**:

#### MANDATORY FIRST CHECK — Scan User Message Before Anything Else

**Before evaluating profile names, config files, or any other classification method, you MUST scan the user's original message for explicit environment statements.**

Look for phrases like:
- "this is a development environment"
- "this is a staging environment"
- "treat this as production"
- "development", "staging", "production", "test", "sandbox" used in the context of describing what environment this is

**If the user's message contains ANY such statement, STOP. Use that classification. Do NOT proceed to Step 2b, 2c, or 2d.** The user's explicit statement overrides everything — profile name, config file, inference. Skip all other steps.

**Example:** User says "Deploy to aws-coworker-test. This is a development environment."
- The profile name contains "test" — IGNORE IT
- The config file may say "test" — IGNORE IT
- The user said "development" — USE THAT
- Classification: `development`
- Source: `user explicit override`

**Why this must be first:** The profile name indicates where credentials point. The user's statement indicates what governance rules to apply. A user may want to test staging enforcement on a test account, or run development-tier rules against a production profile for planning purposes.

#### Step 2a: User explicit override

If the user explicitly states the environment classification in their request (e.g., "This is a staging environment", "treat this as production"), **use that classification regardless of profile name or config**. The user is the authority.

**Classification source: `user explicit override`.**

> **Why this takes precedence:** A user may want to test staging enforcement rules using a test profile, or simulate production constraints in development. The profile name indicates where credentials point; the user's statement indicates what governance rules to apply.

#### Step 2b: Infer classification from profile name (ONLY if Step 2a did not match)

Match the profile name against known patterns:

| Pattern | Classification |
|---------|---------------|
| `*sandbox*` | sandbox |
| `*-dev-*` or `*-dev` | development |
| `*-test-*` or `*-test` | test |
| `*-staging-*` or `*-staging` | staging |
| `*-prod-*` or `*-prod` | production |
| `*-production-*` or `*-production` | production |

If a pattern matches, use that classification. **Classification source: `inferred from name`.**

#### Step 2c: Check AWS CLI config for explicit classification

If no pattern matches, check whether the user has set a custom classification in their AWS CLI config:

```bash
aws configure get aws_coworker_classification --profile {profile-name}
```

If the command returns a valid classification (one of: sandbox, development, test, staging, production), use it. **Classification source: `explicit in ~/.aws/config`.**

> **How users set this:** `aws configure set aws_coworker_classification development --profile acme-dept-a`
> This keeps profile classification in the same file as credentials — single source of truth.

#### Step 2d: Default to unknown (read-only)

If neither inference nor explicit mapping yields a classification:
- Classification: `unknown`
- Permissions: `read-only`
- Approval required: `all-mutations`

Inform the user that the profile is unclassified and suggest they set the classification in their AWS CLI config:
```bash
aws configure set aws_coworker_classification {classification} --profile {profile-name}
```
**Classification source: `default (unknown)`.**

#### Announce before any AWS operations:

```
I will use:
- Profile: {profile-name}
- Region: {region}
- Environment classification: {classification}
- Classification source: {user explicit override | inferred from name | explicit in ~/.aws/config | default (unknown)}

This is a planning session - I will only run read-only discovery commands.
```

#### CRITICAL: Classification is Orchestrator-Inline

**The orchestrator MUST perform Steps 2a-2d itself. DO NOT delegate classification to a sub-agent.**

Sub-agents cannot see the user's original message. If Step 2a (user explicit override) is evaluated by a sub-agent, the sub-agent has no way to detect phrases like "this is a development environment" because it only receives the task prompt, not the conversation. The orchestrator is the only entity with visibility into the user's intent.

**What sub-agents may do:** Run `aws sts get-caller-identity` or `aws configure get aws_coworker_classification` — but only as data-gathering commands whose output the orchestrator interprets. The orchestrator makes the classification decision.

**What sub-agents must NOT do:** Decide the environment classification or enforcement level. That is an orchestrator responsibility.

### Step 3: Discovery and Scope Estimation (Always-Agent Mode)

**Configuration:** Read thresholds from `config/orchestration-config.md`

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

#### MANDATORY PRE-CHECK: Profile Delegation — Do This BEFORE Constructing Any Task Prompt

**STOP. Before you write a single line of any sub-agent Task prompt, you MUST complete this checklist. Do NOT skip this. Do NOT "plan to do it later." Do it NOW.**

**Step A:** Read `config/orchestration-config.md` → find the `profile_delegation` section. Note the suffixes: `readonly` suffix and `admin` suffix.

**Step B:** Compute the scoped profile name:
- For a **discovery** sub-agent: `{base_profile}` + readonly suffix → e.g., `aws-coworker-test` + `-readonly` = `aws-coworker-test-readonly`
- For a **mutation** sub-agent: `{base_profile}` + admin suffix → e.g., `aws-coworker-test` + `-admin` = `aws-coworker-test-admin`

**Step C:** Run this command to check if the scoped profile exists:
```bash
aws configure get region --profile {scoped_profile_name} 2>/dev/null
```

**Step D:** Print your resolution result:
```
Profile delegation:
  Base profile: {base_profile}
  Scoped profile: {scoped_profile_name}
  Exists: {yes/no}
  Using: {scoped_profile_name OR base_profile (fallback)}
```

**Step E:** The profile you printed in "Using:" is the ONLY profile that goes into the Task prompt's `## Target` section. Not the base profile. The resolved profile.

**Concrete example:**
- User asks about `aws-coworker-test`
- You compute: `aws-coworker-test` + `-readonly` = `aws-coworker-test-readonly`
- You run: `aws configure get region --profile aws-coworker-test-readonly`
- It returns a region → profile exists → Using: `aws-coworker-test-readonly`
- Your Task prompt says: `Profile: aws-coworker-test-readonly` — NOT `Profile: aws-coworker-test`
- If the command fails → check `fallback_to_base` in config → if true, use base profile WITH a warning printed to the user

**DO NOT pass the base profile to a sub-agent if a scoped profile exists. This is the same class of bug as the flow logs bypass — acknowledging the rule and then not following it.**

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

    ## Credential Scope
    You MUST use the following profile for ALL AWS CLI commands.
    Do not use any other profile. Do not run `aws configure list-profiles`.
    Do not attempt to discover or switch to other profiles.

    ## CLI Failure Protocol
    If any CLI command fails: STOP. Report the exact command, exit code,
    and error message. Do NOT write scripts, use boto3, try alternative
    CLI namespaces, or improvise workarounds. A clear failure report is
    a valid outcome.

    ## Target
    Profile: {resolved_readonly_profile}
    Region: {region}

    ## Task
    Run these discovery commands and report findings:
    aws ec2 describe-vpcs --profile {resolved_readonly_profile} --region {region}
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

    ## Credential Scope
    You MUST use the following profile for ALL AWS CLI commands.
    Do not use any other profile. Do not run `aws configure list-profiles`.
    Do not attempt to discover or switch to other profiles.

    ## Target
    Profile: {resolved_admin_profile}
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
- Use `subagent_type: "Explore"` (codebase exploration burns tokens without AWS value)
- Spawn "Bash agents" directly
- Omit agent identity from prompt
- Use sub-agents for codebase exploration — the orchestrator already has skill context loaded via the `skills:` frontmatter. If you need to read a skill file, read it directly as the orchestrator.

**Sub-agents exist for one purpose: running AWS CLI commands.** Discovery sub-agents run read-only AWS CLI. Mutation sub-agents run approved write commands. That's it. All reasoning, classification, WAR evaluation, and plan design stays with the orchestrator.

#### Sub-Agent Failure Protocol (Non-Negotiable)

When a sub-agent reports a CLI failure:

1. **Accept the failure.** Do not spawn additional sub-agents to work around it.
2. **Do not** write Python scripts, use boto3/botocore, or try alternative tools.
3. **Do not** explore the filesystem or install packages to find workarounds.
4. **Report** the failure to the user with the exact command, exit code, and error message.
5. **Continue** with whatever discovery data was successfully gathered. Partial results are fine.

A clear failure report is a valid and useful outcome. The user can then decide whether to update the CLI, check permissions, try a different approach, or accept partial results. The orchestrator's job is to coordinate and report — not to improvise solutions when tools don't work.

**Why this matters:** When a sub-agent fails and the orchestrator spawns creative workarounds (writing Python, trying boto3, exploring alternative APIs), it operates outside the system's contract with the user. The user trusts that AWS Coworker operates within its defined tools — the AWS CLI, as documented in the playbook. A success achieved through improvisation is less trustworthy than a failure with a clear explanation, because the user never agreed to the improvised approach.

#### 3a: Initial Discovery

```bash
# Identity check
aws sts get-caller-identity --profile {profile}

# Resource-specific discovery (examples)
aws ec2 describe-instances --profile {profile} --region {region}
aws ec2 describe-vpcs --profile {profile} --region {region}
aws s3 ls --profile {profile}
```

**For Bedrock/AgentCore deployments:** Discovery MUST verify that the orchestrator model is available via Bedrock, not just sub-agent models. AWS Coworker requires Opus (or equivalent) as the orchestrator. If only Haiku and Sonnet are enabled, the deployment cannot function — flag this as a prerequisite failure.

```bash
# Check orchestrator model availability (not just sub-agent models)
aws bedrock list-foundation-models --profile {profile} --region {region} \
  --by-provider Anthropic --query "modelSummaries[?contains(modelId, 'opus')].modelId"
```

If no Opus model is enabled, report: "AWS Coworker requires Opus as the orchestrator model. Currently enabled models: {list}. Request access to Opus via the Bedrock console before deploying."

Load relevant information from:
- `aws-cli-playbook` skill for command patterns
- `aws-org-strategy` skill for account/OU context
- `config/orchestration-config.md` for thresholds
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
   - **BLOCKED** — Gap exists, enforcement requires resolution but plan doesn't address it. Must be resolved before execution.
9. **Apply execution gate:**
   - If enforcement=`optional`: Show findings, proceed (all gaps are ACCEPTABLE)
   - If enforcement=`warn`: Show findings, all gaps ACCEPTABLE but user warned
   - If enforcement=`strict`: Critical/High/Medium gaps are BLOCKED unless REMEDIATE; Low are ACCEPTABLE
   - If enforcement=`enforce`: ALL gaps are BLOCKED unless REMEDIATE; no override path

**The agent's default is to REMEDIATE everything enforcement requires.** If the user's initial request asks to skip an item that enforcement requires, that item is **BLOCKED, not ACCEPTABLE**. Examples:
- "Don't worry about flow logs" at strict enforcement where flow logs are High severity → **BLOCKED** (High is above threshold)
- "Don't configure CloudWatch logging" at strict enforcement where CloudWatch logging is Medium severity → **BLOCKED** (Medium is above threshold)
- "Skip tagging" at strict enforcement where tagging is Low severity → **ACCEPTABLE** (Low is below threshold)

The user's request does not override the enforcement gate — it triggers the gate. The user is informed that the item is required and given three options: include it in the plan, deploy to a lower environment, or modify the enforcement config. User intent expressed in the initial request has exactly the same standing as user intent expressed after the plan is presented — enforcement rules apply equally to both.

**Apply statuses mechanically based on severity and enforcement level.** All items at the same severity get the same treatment — the agent does not exercise discretion about which items to block and which to allow at a given severity. If encryption (Critical) is BLOCKED, every Critical item is BLOCKED. If CloudWatch logging (Medium) is BLOCKED, every Medium item is BLOCKED. There are no item-specific exceptions — no category of items (logging, monitoring, operational, etc.) gets special treatment. Enforcement is purely severity-based.

**DO NOT** proceed past a BLOCKED item without the user modifying the proposed architecture.
**DO NOT** allow the planner to self-generate WAR assessments — the orchestrator evaluates.
**DO NOT** use PASS for items in a plan — nothing can "pass" when it doesn't exist yet. Use REMEDIATE.
**DO NOT** offer "accept gaps explicitly" or similar escape hatches at `strict` or `enforce` enforcement for items at or above the blocking threshold (Medium and above at `strict`, all items at `enforce`). Enforcement gates are not negotiable at runtime — to change what enforcement requires, modify `config/environments/environments.yaml`.

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

**Configuration:** `config/orchestration-config.md`

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
