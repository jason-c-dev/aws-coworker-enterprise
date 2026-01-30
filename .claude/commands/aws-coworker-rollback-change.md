---
description: Design and execute rollback for a previous change
skills: [aws-cli-playbook, aws-governance-guardrails]
agent: aws-coworker-executor
tools: [Read, Write, Bash]
arguments:
  - name: change
    description: Reference to the change to rollback (plan ID, commit, or description)
    required: true
  - name: environment
    description: Target environment
    required: true
---

# /aws-coworker-rollback-change

## Overview

Design and (for non-production) execute rollback sequences for previous changes. For production, generates CI/CD pipeline rollback changes.

## Prerequisites

- Knowledge of the change to rollback
- Access to original plan or change details
- Appropriate AWS profile for the environment

---

## Workflow

### Step 1: Identify the Change

```
## Rollback Request

Change reference: {change}
Environment: {environment}

Searching for change details...
```

Locate change information from:
- Original plan
- Git commit history
- CloudFormation stack events
- CloudTrail logs

```
## Change Identified

Change: {change name/ID}
Date: {when executed}
Type: {what was changed}
Resources affected:
- {resource 1}
- {resource 2}

Original plan rollback steps:
{if available from plan}
```

### Step 2: Assess Current State

Discovery to understand current state:

```bash
# Check current state of affected resources
aws ec2 describe-instances --instance-ids {ids} --profile {profile} --region {region}
aws cloudformation describe-stacks --stack-name {stack} --profile {profile} --region {region}
```

```
## Current State

| Resource | Original State | Current State | Drift |
|----------|---------------|---------------|-------|
| {resource} | {original} | {current} | {yes/no} |

Additional changes since original change:
- {any subsequent changes}
```

### Step 3: Design Rollback Plan

```
## Rollback Plan

### Objective
Restore system to state before: {change description}

### Rollback Strategy
{CloudFormation rollback | Manual CLI | IaC revert}

### Steps

#### Step 1: {Description}
```bash
{command}
```
Expected outcome: {outcome}

#### Step 2: {Description}
```bash
{command}
```
Expected outcome: {outcome}

### Validation
After rollback, verify:
```bash
{validation commands}
```

### Risks
- {potential issue 1}
- {potential issue 2}

### Dependencies
Resources that depend on rolled-back resources:
- {dependent resource}: {impact}
```

### Step 4: Environment-Specific Handling

**For Non-Production (sandbox, development):**

```
Environment: {development}

This is a non-production environment. I can execute the rollback directly.

## Rollback Steps

1. {step 1}
2. {step 2}
3. {step 3}

Do you approve rollback execution? (yes/no)
```

**For Production:**

```
Environment: production

⚠️ Production rollbacks require CI/CD pipeline.

I will:
1. Generate rollback IaC changes
2. Create a rollback branch
3. Prepare PR for emergency merge

Proceeding with rollback preparation...
```

### Step 5: Execute Rollback (Non-Prod)

```
## Executing Rollback

[Step 1 of N]
Action: {description}
Command:
```bash
{command}
```

```
Result: {output}
Status: ✅ Success

[Step 2 of N]
...
```

### Step 6: Validate Rollback

```bash
# Run validation commands
{validation command 1}
{validation command 2}
```

```
## Rollback Validation

| Check | Status |
|-------|--------|
| {check 1} | ✅/❌ |
| {check 2} | ✅/❌ |

Overall validation: {PASSED/FAILED}
```

### Step 7: Completion Report

```
## Rollback Complete

### Summary
- Original change: {change reference}
- Rollback status: ✅ Successful / ❌ Failed
- Duration: {time}

### State After Rollback
| Resource | Expected State | Actual State | Match |
|----------|---------------|--------------|-------|
| {resource} | {expected} | {actual} | ✅/❌ |

### Actions Taken
1. {action 1}
2. {action 2}

### Follow-up Required
- {any follow-up items}

### Incident Documentation
```
Date: {date}
Change rolled back: {change}
Reason for rollback: {reason}
Rollback executed by: {who}
Time to rollback: {duration}
Impact: {impact assessment}
```
```

---

## Rollback Patterns

### CloudFormation Stack Rollback

```bash
# Cancel in-progress update
aws cloudformation cancel-update-stack \
  --stack-name {stack} \
  --profile {profile} \
  --region {region}

# Rollback to previous version (via update)
aws cloudformation update-stack \
  --stack-name {stack} \
  --use-previous-template \
  --parameters ParameterKey=Param1,UsePreviousValue=true \
  --profile {profile} \
  --region {region}

# Delete stack (if needed)
aws cloudformation delete-stack \
  --stack-name {stack} \
  --profile {profile} \
  --region {region}
```

### CDK Rollback

```bash
# Deploy previous version
git checkout {previous-commit}
cdk deploy --profile {profile}

# Or revert commit and deploy
git revert {commit}
cdk deploy --profile {profile}
```

### Terraform Rollback

```bash
# Show previous state
terraform state list

# Target specific resources
terraform plan -target={resource} -var-file={env}.tfvars

# Apply previous state
git checkout {previous-commit}
terraform plan -var-file={env}.tfvars
terraform apply -var-file={env}.tfvars
```

### EC2 Instance Recovery

```bash
# From AMI
aws ec2 run-instances \
  --image-id {ami-before-change} \
  --instance-type {original-type} \
  --profile {profile} \
  --region {region}

# From snapshot (EBS)
aws ec2 create-volume \
  --snapshot-id {snapshot-before-change} \
  --availability-zone {az} \
  --profile {profile} \
  --region {region}
```

### S3 Object Recovery

```bash
# List versions
aws s3api list-object-versions \
  --bucket {bucket} \
  --prefix {key} \
  --profile {profile}

# Restore previous version
aws s3api copy-object \
  --bucket {bucket} \
  --copy-source "{bucket}/{key}?versionId={previous-version}" \
  --key {key} \
  --profile {profile}
```

---

## Error Handling

### Rollback Failed

```
❌ Rollback step failed

Step: {step}
Error: {error}

Options:
1. Retry this step
2. Manual intervention required
3. Escalate to incident management

Current state:
- Partially rolled back
- Resources in inconsistent state
```

### Original State Unknown

```
⚠️ Original state unclear

Unable to determine pre-change state from:
- Original plan: {not found/incomplete}
- Git history: {status}
- CloudTrail: {status}

Options:
1. Provide original state manually
2. Restore from backup
3. Rebuild from known-good state
```

---

## Output

The command produces:
1. **Rollback plan** with detailed steps
2. **Execution log** (for non-prod)
3. **Validation results** confirming rollback success
4. **Incident documentation** for records
