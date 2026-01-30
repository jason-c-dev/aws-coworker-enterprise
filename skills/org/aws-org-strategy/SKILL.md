---
name: aws-org-strategy
description: Multi-account and OU strategy, landing zone patterns, and workload placement
version: 1.0.0
category: org
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-guardrail]
tools: [Read]
---

# AWS Organization Strategy

## Purpose

This skill captures organizational AWS multi-account strategy, OU structure, landing zone patterns, and workload placement rules. Customize this skill to reflect your organization's specific AWS structure.

## When to Use

- Planning new workloads or accounts
- Understanding account relationships
- Applying organizational policies
- Navigating multi-account operations
- Bootstrapping new accounts

## When NOT to Use

- Single-account deployments (simplified patterns apply)
- Cross-organization federation (separate considerations)

---

## Organization Patterns

This skill supports multiple organizational patterns. Configure based on your setup:

### Pattern 1: Single Account

```
┌─────────────────────────────────────┐
│            Single Account           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ Dev │ │ Stg │ │ Prd │ │ Sec │   │
│  │ VPC │ │ VPC │ │ VPC │ │ VPC │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
└─────────────────────────────────────┘
```

**When to use:** Small teams, limited workloads, getting started

### Pattern 2: Multi-Account Basic

```
┌─────────────────────────────────────────────────────┐
│                  AWS Organizations                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐                                       │
│  │Management│  (Billing, Organizations)              │
│  └──────────┘                                       │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Security │  │   Dev    │  │   Prod   │          │
│  │ Account  │  │ Account  │  │ Account  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**When to use:** Growing teams, need workload isolation

### Pattern 3: Multi-Account with OUs

```
┌──────────────────────────────────────────────────────────────────┐
│                       AWS Organizations                           │
├──────────────────────────────────────────────────────────────────┤
│                        Management Account                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Security OU   │  │ Infrastructure  │  │  Workloads OU   │  │
│  │                 │  │      OU         │  │                 │  │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │ ┌─────────────┐ │  │
│  │  │  Audit    │  │  │  │  Shared   │  │  │ │ Non-Prod OU │ │  │
│  │  │  Account  │  │  │  │  Services │  │  │ │ ┌─────────┐ │ │  │
│  │  └───────────┘  │  │  │  Account  │  │  │ │ │  Dev    │ │ │  │
│  │  ┌───────────┐  │  │  └───────────┘  │  │ │ └─────────┘ │ │  │
│  │  │Log Archive│  │  │  ┌───────────┐  │  │ │ ┌─────────┐ │ │  │
│  │  │  Account  │  │  │  │  Network  │  │  │ │ │ Staging │ │ │  │
│  │  └───────────┘  │  │  │   Hub     │  │  │ │ └─────────┘ │ │  │
│  │                 │  │  └───────────┘  │  │ └─────────────┘ │  │
│  │                 │  │                 │  │ ┌─────────────┐ │  │
│  │                 │  │                 │  │ │  Prod OU    │ │  │
│  │                 │  │                 │  │ │ ┌─────────┐ │ │  │
│  │                 │  │                 │  │ │ │  Prod   │ │ │  │
│  │                 │  │                 │  │ │ └─────────┘ │ │  │
│  │                 │  │                 │  │ └─────────────┘ │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                   │
│  ┌─────────────────┐                                             │
│  │   Sandbox OU    │                                             │
│  │  ┌───────────┐  │                                             │
│  │  │  Sandbox  │  │                                             │
│  │  │ Accounts  │  │                                             │
│  │  └───────────┘  │                                             │
│  └─────────────────┘                                             │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**When to use:** Enterprise, compliance requirements, team isolation

### Pattern 4: Control Tower Landing Zone

```
Extends Pattern 3 with:
- Automated account provisioning
- Guardrails (preventive and detective)
- Account Factory
- Centralized logging and audit
```

---

## Account Types

### Management Account

**Purpose:** AWS Organizations management, consolidated billing

**Contains:**
- Organizations service
- Billing and cost management
- SSO/Identity Center
- SCPs

**Rules:**
- No workloads
- Minimal direct access
- Break-glass only

### Security/Audit Account

**Purpose:** Centralized security tooling and audit

**Contains:**
- GuardDuty delegated admin
- Security Hub aggregation
- CloudTrail organization trail
- AWS Config aggregator

**Rules:**
- Security team access only
- Read-only to other accounts
- Alert destination

### Log Archive Account

**Purpose:** Immutable log storage

**Contains:**
- S3 buckets for CloudTrail
- S3 buckets for VPC Flow Logs
- S3 buckets for application logs
- Glacier for long-term retention

**Rules:**
- Write-only from other accounts
- No delete permissions
- Compliance retention policies

### Shared Services Account

**Purpose:** Shared infrastructure services

**Contains:**
- Transit Gateway
- Shared VPCs (optional)
- Directory services
- Shared container registries
- Shared artifact repositories

**Rules:**
- Infrastructure team managed
- Shared resources only
- No application workloads

### Workload Accounts

**Purpose:** Application workloads

**Types:**
- Development accounts
- Staging accounts
- Production accounts

**Rules:**
- Environment-specific permissions
- Team ownership
- Workload isolation

### Sandbox Accounts

**Purpose:** Experimentation and learning

**Contains:**
- Experimental workloads
- Proof of concepts
- Training environments

**Rules:**
- Time-limited or budget-limited
- No production data
- May be periodically cleaned

---

## OU Policies

### Service Control Policies (SCPs)

```json
// Example: Deny leaving organization
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeaveOrganization",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    }
  ]
}

// Example: Require IMDSv2 for EC2
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    }
  ]
}

// Example: Restrict regions
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOtherRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "organizations:*",
        "support:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2",
            "eu-west-1"
          ]
        }
      }
    }
  ]
}
```

---

## Workload Placement

### Decision Matrix

| Workload Type | Account Type | OU |
|---------------|--------------|-----|
| Production app | Prod workload | Production OU |
| Pre-prod testing | Staging workload | Non-Production OU |
| Development | Dev workload | Non-Production OU |
| Security tools | Security | Security OU |
| Shared networking | Shared services | Infrastructure OU |
| Experiments | Sandbox | Sandbox OU |

### Placement Questions

```markdown
1. What environment? → Determines OU
2. What team owns it? → May determine specific account
3. What compliance needs? → May require dedicated account
4. What network connectivity? → Determines VPC placement
5. What data classification? → Determines security controls
```

---

## Network Architecture

### Hub-and-Spoke with Transit Gateway

```
                    ┌─────────────────┐
                    │ Transit Gateway │
                    │  (Shared Svcs)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────┴────┐        ┌────┴────┐        ┌────┴────┐
    │ Dev VPC │        │ Stg VPC │        │ Prd VPC │
    │ Account │        │ Account │        │ Account │
    └─────────┘        └─────────┘        └─────────┘
```

### VPC Sharing

```
Shared VPC Account
├── Shared-Prod-VPC
│   ├── Private-Subnet-App-A (shared to Account A)
│   ├── Private-Subnet-App-B (shared to Account B)
│   └── Private-Subnet-Shared (shared to all)
└── Shared-Dev-VPC
    └── ...
```

---

## CIDR Allocation

### Example Allocation

```markdown
## CIDR Allocation Plan

### Primary Region (us-east-1)
| Environment | CIDR | Notes |
|-------------|------|-------|
| Production | 10.0.0.0/16 | 65,536 IPs |
| Staging | 10.10.0.0/16 | 65,536 IPs |
| Development | 10.20.0.0/16 | 65,536 IPs |
| Shared Services | 10.100.0.0/16 | 65,536 IPs |
| Sandbox | 10.200.0.0/16 | 65,536 IPs |

### Secondary Region (us-west-2)
| Environment | CIDR | Notes |
|-------------|------|-------|
| Production DR | 10.1.0.0/16 | DR site |

### Reserved
| Range | Purpose |
|-------|---------|
| 10.50.0.0/16 - 10.99.0.0/16 | Future expansion |
| 172.16.0.0/12 | On-premises |
```

---

## Account Provisioning

### Account Request Checklist

```markdown
## New Account Request

### Basic Information
- [ ] Account name (following naming convention)
- [ ] Environment type (dev/staging/prod/sandbox)
- [ ] Owner team
- [ ] Cost center

### Technical Requirements
- [ ] Required regions
- [ ] Network connectivity needs
- [ ] Compliance requirements
- [ ] Data classification

### Access Requirements
- [ ] Team roles needed
- [ ] Service roles needed
- [ ] Break-glass access plan

### Budget
- [ ] Monthly budget estimate
- [ ] Budget alerts configuration
```

### Account Bootstrap Steps

```markdown
1. Create account via Organizations/Account Factory
2. Configure SSO access
3. Apply baseline SCPs
4. Deploy baseline CloudFormation/CDK
   - VPC and networking
   - IAM roles
   - CloudTrail
   - Config
   - GuardDuty membership
5. Configure budgets and alerts
6. Add to monitoring
7. Document in account registry
```

---

## Customization Guide

**To customize this skill for your organization:**

1. Update the organization pattern section with your actual structure
2. Document your specific accounts and their purposes
3. Define your CIDR allocation plan
4. Specify your SCP policies
5. Document your account provisioning process

Store organization-specific details in:
- `templates/single-account.md`
- `templates/multi-account-basic.md`
- `templates/multi-account-control-tower.md`

---

## Related Skills

- `aws-governance-guardrails` — Policy enforcement
- `aws-cli-playbook` — Organizations CLI commands
- `aws-well-architected` — Architectural guidance
