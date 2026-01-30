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

### Step 3: Discovery

Run read-only AWS CLI commands to understand current state:

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
- Existing infrastructure state

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
