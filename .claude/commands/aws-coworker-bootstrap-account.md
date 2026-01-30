---
description: Plan and generate steps to bootstrap a new AWS account
skills: [aws-org-strategy, aws-governance-guardrails, aws-cli-playbook, aws-observability-setup]
agent: aws-coworker-planner
tools: [Read, Write, Bash]
arguments:
  - name: account-name
    description: Name for the new account
    required: true
  - name: account-type
    description: Type of account (sandbox, development, staging, production, security, shared-services)
    required: true
  - name: ou
    description: Target organizational unit
    required: false
---

# /aws-coworker-bootstrap-account

## Overview

Plan and generate Infrastructure as Code to bootstrap a new AWS account in line with organizational strategy and governance guardrails.

## Prerequisites

- AWS Organizations access (for account creation)
- Understanding of organizational OU structure
- Defined baseline requirements

---

## Workflow

### Step 1: Gather Requirements

```
## New Account Bootstrap

Account name: {account-name}
Account type: {account-type}
Target OU: {ou or TBD}

Let me verify the requirements:

1. What is the purpose of this account?
2. Which team will own it?
3. What's the cost center for billing?
4. Are there specific compliance requirements?
```

### Step 2: Validate Against Org Strategy

Load `aws-org-strategy` skill:

```
## Organization Alignment

Checking account against org strategy...

| Check | Status |
|-------|--------|
| Account type valid | ✅/❌ |
| OU exists | ✅/❌ |
| Naming convention | ✅/❌ |
| CIDR allocation available | ✅/❌ |
```

### Step 3: Define Baseline Configuration

Based on account type, determine baseline:

```
## Baseline Configuration

### Network
- VPC CIDR: {from allocation plan}
- Subnets: Public, Private, Data (per org standard)
- Availability Zones: {number}
- NAT Gateway: {yes/no based on type}

### Security
- CloudTrail: ✅ (org trail membership)
- GuardDuty: ✅ (enabled)
- Security Hub: ✅ (enabled)
- Config: ✅ (enabled)

### IAM
- SSO configuration: ✅
- Service roles: {list}
- Permission boundaries: ✅

### Tagging
- Environment: {from account type}
- Owner: {from input}
- CostCenter: {from input}

### Monitoring
- CloudWatch: ✅ (basic alarms)
- VPC Flow Logs: ✅
- Budgets: ✅ (based on account type)
```

### Step 4: Generate Bootstrap Plan

```markdown
# Account Bootstrap Plan: {account-name}

## Summary
Create and configure new {account-type} account in {ou} OU.

## Phase 1: Account Creation

### Via AWS Organizations
```bash
aws organizations create-account \
  --email {account-name}@{org-domain} \
  --account-name {account-name} \
  --iam-user-access-to-billing DENY \
  --profile management \
  --region us-east-1
```

### Via Control Tower Account Factory
{If using Control Tower, reference Account Factory}

## Phase 2: OU Placement

```bash
# Move to target OU
aws organizations move-account \
  --account-id {new-account-id} \
  --source-parent-id {root-or-current-ou} \
  --destination-parent-id {target-ou-id} \
  --profile management \
  --region us-east-1
```

## Phase 3: Baseline Deployment

### Option A: CDK Bootstrap

```typescript
// bootstrap/lib/baseline-stack.ts
export class BaselineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BaselineProps) {
    super(scope, id, props);

    // VPC
    const vpc = new ec2.Vpc(this, 'VPC', {
      cidr: props.vpcCidr,
      maxAzs: 3,
      // ... configuration
    });

    // ... other baseline resources
  }
}
```

### Option B: CloudFormation StackSet

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Account baseline

Resources:
  # VPC, IAM roles, etc.
```

### Option C: Terraform

```hcl
module "baseline" {
  source = "./modules/account-baseline"

  account_name = var.account_name
  vpc_cidr     = var.vpc_cidr
  # ... configuration
}
```

## Phase 4: Security Configuration

### Enable GuardDuty membership
```bash
# From security account
aws guardduty create-members \
  --detector-id {detector-id} \
  --account-details AccountId={new-account-id},Email={email} \
  --profile security \
  --region us-east-1
```

### Enable Security Hub membership
```bash
aws securityhub create-members \
  --account-details AccountId={new-account-id},Email={email} \
  --profile security \
  --region us-east-1
```

## Phase 5: Budget Configuration

```bash
aws budgets create-budget \
  --account-id {new-account-id} \
  --budget '{
    "BudgetName": "monthly-total",
    "BudgetLimit": {"Amount": "{limit}", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --profile {profile}
```

## Phase 6: Validation

### Checklist
- [ ] Account created and accessible
- [ ] OU placement correct
- [ ] VPC deployed with correct CIDR
- [ ] CloudTrail logging
- [ ] GuardDuty enabled
- [ ] Security Hub enabled
- [ ] Config recording
- [ ] SSO access working
- [ ] Budget alerts configured
- [ ] Tags applied

### Validation Commands
```bash
# Verify account
aws organizations describe-account --account-id {id}

# Verify OU
aws organizations list-parents --child-id {id}

# Verify VPC (from new account)
aws ec2 describe-vpcs --profile {new-account-profile}
```
```

### Step 5: Generate IaC Files

Create the actual IaC files:

```
## Generated Files

Creating baseline IaC:

1. infrastructure/accounts/{account-name}/
   ├── main.ts (or main.tf)
   ├── config.yaml
   └── README.md

2. config/accounts/{account-name}.yaml
   - Account metadata
   - Baseline configuration

Files created successfully.
```

### Step 6: Present Bootstrap Steps

```
## Account Bootstrap Ready

### Summary
Account: {account-name}
Type: {account-type}
OU: {ou}

### Generated Artifacts
| Artifact | Location |
|----------|----------|
| IaC code | infrastructure/accounts/{account-name}/ |
| Config | config/accounts/{account-name}.yaml |
| Plan | docs/bootstrap-plans/{account-name}.md |

### Execution Steps

1. **Create account** (requires Organizations admin):
   - Use Account Factory, OR
   - Run account creation command

2. **Deploy baseline** (after account available):
   ```bash
   cd infrastructure/accounts/{account-name}
   cdk deploy --profile {management-profile}
   ```

3. **Verify security integration**:
   - GuardDuty membership
   - Security Hub membership
   - CloudTrail in org trail

4. **Configure access**:
   - Add to SSO permission sets
   - Create initial IAM roles

5. **Validate**:
   - Run validation checklist
   - Verify all controls active

### Timeline
- Account creation: ~5 minutes
- Baseline deployment: ~15 minutes
- Security integration: ~10 minutes
- Total: ~30 minutes

### Next Steps
1. Review generated IaC
2. Get approval for account creation
3. Execute bootstrap
4. Add to account registry
```

---

## Output

The command produces:
1. **Bootstrap plan** with all steps
2. **IaC code** for baseline deployment
3. **Configuration files** for the account
4. **Validation checklist** for verification

---

## Account Types

| Type | VPC | NAT | Budget | Access |
|------|-----|-----|--------|--------|
| sandbox | Simple | Shared | $500 | Open |
| development | Standard | Shared | $2000 | Team |
| staging | Standard | Dedicated | $5000 | Team |
| production | Full | Multi-AZ | $20000+ | Restricted |
| security | Minimal | No | $1000 | Security team |
| shared-services | Hub | Dedicated | $5000 | Platform team |
