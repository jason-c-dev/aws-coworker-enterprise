---
description: Execute an approved plan in non-production environments
skills: [aws-cli-playbook, aws-governance-guardrails]
agent: aws-coworker-executor
tools: [Read, Write, Bash]
arguments:
  - name: plan
    description: Reference to the approved plan (or "last" for most recent)
    required: true
  - name: dry-run
    description: Show commands without executing
    required: false
    default: false
---

# /aws-coworker-execute-nonprod

## Overview

Execute an approved AWS interaction plan in non-production environments (sandbox, development, or test). This command will NOT execute against staging or production—use `/aws-coworker-prepare-prod-change` instead.

## Prerequisites

- Approved plan from `/aws-coworker-plan-interaction`
- AWS profile configured for target non-prod environment
- Guardrail validation passed

---

## Workflow

### Step 1: Load and Verify Plan

Load the approved plan:

1. Retrieve plan details
2. Verify it was approved
3. Verify guardrail validation passed

```
Loading plan: {plan reference}

Plan: {plan name}
Created: {timestamp}
Approval: {approved by user at timestamp}
Guardrail: {validation status}
```

### Step 2: Environment Verification

**CRITICAL**: Verify this is NOT production:

```
## Environment Verification

Profile: {profile}
Environment classification: {classification}

Checking environment...
```

```bash
# Verify profile
aws sts get-caller-identity --profile {profile}
```

**If environment is staging or production:**
```
⚠️ STOPPING: This command is for non-production only.

Detected environment: {staging|production}

For staging/production changes, use:
/aws-coworker-prepare-prod-change

This will generate CI/CD pipeline changes instead of direct execution.
```

**If environment is sandbox or development:**
```
✅ Environment verified: {environment}

Proceeding with execution preparation...
```

### Step 3: Pre-Execution Confirmation

Present commands and request explicit approval:

```
## Execution Plan

I will execute the following operations:

### Phase 1: {Phase Name}
Commands:
1. {command 1}
2. {command 2}

### Phase 2: {Phase Name}
Commands:
1. {command 1}
2. {command 2}

---

Target:
- Profile: {profile}
- Region: {region}
- Environment: {environment}

Blast radius: {scope}

⚠️ This will modify AWS resources.

Do you approve execution? (yes/no)
```

**Wait for explicit "yes" before proceeding.**

### Step 4: Execute with Validation

For each phase:

```
## Executing Phase 1: {Phase Name}

[Step 1 of N]
Command: {command}
```

```bash
# Execute command
{actual command}
```

```
Result: {output summary}
Status: ✅ Success / ❌ Failed
```

**Validation after each step:**
```bash
# Run validation command from plan
{validation command}
```

```
Validation: ✅ Passed / ❌ Failed

Proceeding to next step...
```

### Step 5: Handle Failures

**If a step fails:**

```
❌ Step {N} failed

Error: {error message}

Options:
1. Retry this step
2. Skip and continue (if safe)
3. Rollback completed steps
4. Pause and investigate

What would you like to do?
```

**Rollback execution:**
```
## Initiating Rollback

Rolling back in reverse order:

[Rollback Step 2]
Command: {rollback command}
Result: {output}

[Rollback Step 1]
Command: {rollback command}
Result: {output}

Rollback complete. System returned to pre-execution state.
```

### Step 6: Completion Report

```
## Execution Complete

### Summary
- Plan: {plan name}
- Status: ✅ Successful / ⚠️ Partial / ❌ Failed
- Duration: {time}
- Steps completed: {X}/{Y}

### Resources Affected
| Resource | Action | Result |
|----------|--------|--------|
| {resource} | {action} | ✅/❌ |

### Validation Results
All post-execution validations: {passed/failed}

### Next Steps
{recommendations if any}

### Change Log Entry
```
Date: {date}
Plan: {plan name}
Executor: {profile}
Status: {status}
Resources: {list}
```
```

---

## Output

The command produces:
1. **Execution log** with all commands and outputs
2. **Resource change summary** with before/after state
3. **Validation results** confirming success
4. **Rollback status** if rollback was needed

---

## Safety Features

### Automatic Stops

Execution automatically stops if:
- Environment is staging or production
- User doesn't explicitly approve
- Critical validation fails
- Unexpected error occurs

### Checkpoints

Execution pauses for confirmation at:
- Before starting execution
- Before destructive operations (delete, terminate)
- After unexpected output
- Before proceeding to new phase

---

## Error Handling

### Permission Denied

```
❌ Permission denied

Profile: {profile}
Operation: {operation}
Error: {error}

This may indicate:
1. Profile lacks required permissions
2. SCP blocking the operation
3. Resource policy restriction

Please verify permissions and retry.
```

### Resource Not Found

```
❌ Resource not found

Resource: {resource}
Error: {error}

The resource may have been:
1. Already deleted
2. In a different region
3. Named differently

Verify resource and retry.
```

### Rate Limiting

```
⚠️ Rate limiting encountered

Waiting {seconds} seconds before retry...

[Retry attempt {N}]
```
