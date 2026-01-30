---
name: aws-governance-guardrails
description: Organization governance policies - never do, always do, and compliance rules
version: 1.0.0
category: org
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-guardrail, aws-coworker-executor]
tools: [Read]
---

# AWS Governance Guardrails

## Purpose

This skill encodes organizational governance and compliance rules for AWS operations. It defines what must always be done, what must never be done, and how to validate compliance.

## When to Use

- Validating any AWS operation before execution
- Planning new resources or changes
- Auditing existing resources
- Training new team members on policies

## When NOT to Use

- Emergency break-glass situations (document exception, review after)
- Explicit management-approved exceptions (document decision)

---

## Policy Categories

| Category | Description |
|----------|-------------|
| **Never Do** | Prohibited actions that could cause security or compliance issues |
| **Always Do** | Mandatory practices for all AWS operations |
| **Environment-Specific** | Rules that vary by environment |
| **Validation** | How to check compliance |

---

## Never Do Policies

### Security - Critical

```markdown
### NEVER: Public S3 Buckets for Sensitive Data
- Do not create S3 buckets with public read/write
- Do not disable Block Public Access for data buckets
- Exception: Intentionally public static content (requires documented approval)

### NEVER: Wildcard IAM Permissions
- Do not use "Action": "*" in IAM policies
- Do not use "Resource": "*" without conditions
- Do not use "NotAction" without careful scoping

### NEVER: Root Account Usage
- Do not use root credentials for operations
- Do not create access keys for root
- Exception: Account recovery and specific console-only tasks

### NEVER: Long-Lived Credentials in Code
- Do not commit AWS access keys to repositories
- Do not embed credentials in application code
- Do not store credentials in environment variables long-term
- Use: IAM roles, Secrets Manager, Parameter Store

### NEVER: Unencrypted Sensitive Data
- Do not store PII/sensitive data without encryption
- Do not transmit sensitive data over unencrypted channels
- Do not use deprecated encryption (MD5, SHA1 for security)

### NEVER: Open Security Groups
- Do not allow 0.0.0.0/0 to SSH (22)
- Do not allow 0.0.0.0/0 to RDP (3389)
- Do not allow 0.0.0.0/0 to database ports (3306, 5432, 1433, etc.)
```

### Operations - Critical

```markdown
### NEVER: Direct Production Changes
- Do not modify production via AWS Console for infrastructure
- Do not run ad-hoc AWS CLI commands that mutate production
- Use: CI/CD pipelines, Infrastructure as Code

### NEVER: Skip Change Management
- Do not deploy to staging/production without change ticket
- Do not bypass approval workflows
- Do not deploy during change freeze without emergency approval

### NEVER: Delete Without Backup
- Do not terminate production instances without AMI/snapshot
- Do not delete databases without verified backup
- Do not empty S3 buckets without lifecycle consideration
```

### Cost - Important

```markdown
### NEVER: Uncontrolled Spending
- Do not launch large instances without cost estimate
- Do not leave idle resources running indefinitely
- Do not skip cost tags on resources
```

---

## Always Do Policies

### Tagging - Mandatory

```markdown
### ALWAYS: Apply Required Tags

All AWS resources MUST have:

| Tag Key | Description | Format |
|---------|-------------|--------|
| Environment | Deployment environment | sandbox, development, staging, production |
| Owner | Responsible team/person | team-name or user@domain |
| CostCenter | Cost allocation | CC-NNNN format |

Recommended additional tags:
| Tag Key | Description | Format |
|---------|-------------|--------|
| Project | Project name | project-name |
| DataClassification | Data sensitivity | public, internal, confidential, restricted |
| CreatedBy | Creation method | terraform, cdk, manual |
| ExpirationDate | For temporary resources | YYYY-MM-DD |
```

### Security - Mandatory

```markdown
### ALWAYS: Encryption

At Rest:
- Enable encryption for EBS volumes (KMS)
- Enable encryption for RDS (KMS)
- Enable encryption for S3 (SSE-S3 minimum, SSE-KMS for sensitive)
- Enable encryption for Secrets Manager, Parameter Store

In Transit:
- Use HTTPS/TLS for all external connections
- Enforce TLS 1.2 minimum
- Use SSL for database connections

### ALWAYS: Logging

Enable for all accounts:
- CloudTrail (all regions, management + data events for sensitive)
- VPC Flow Logs (all VPCs)
- S3 Access Logs (for data buckets)
- Application logging to CloudWatch

### ALWAYS: Least Privilege IAM

- Scope permissions to specific resources
- Use conditions where appropriate
- Prefer managed policies over inline
- Regular access reviews (quarterly minimum)

### ALWAYS: Network Segmentation

- Use private subnets for databases and internal services
- Implement security groups with minimal required access
- Use NACLs for additional defense in depth
- Document allowed traffic flows
```

### Operations - Mandatory

```markdown
### ALWAYS: Infrastructure as Code

- Define infrastructure in CDK, Terraform, or CloudFormation
- Store IaC in version control
- Deploy via CI/CD pipelines
- Maintain drift detection

### ALWAYS: Documentation

- Document architecture decisions
- Maintain runbooks for operations
- Keep deployment documentation current
- Record change rationale

### ALWAYS: Backup and Recovery

- Automated backups for databases
- Snapshot critical EBS volumes
- Test recovery procedures quarterly
- Document RPO/RTO for each service
```

---

## Environment-Specific Policies

### Sandbox

```markdown
## Sandbox Environment

Permissions:
- AWS CLI mutations: Allowed
- Direct console changes: Allowed
- Approval required: None

Restrictions:
- No production data
- Budget capped at $X/month
- Resources may be auto-terminated
- No connectivity to other environments
```

### Development

```markdown
## Development Environment

Permissions:
- AWS CLI mutations: Allowed with tagging
- Direct console changes: Discouraged
- Approval required: Destructive operations only

Restrictions:
- No production data
- Budget alerts at 80%
- Scheduled scaling down after hours (optional)
```

### Staging

```markdown
## Staging Environment

Permissions:
- AWS CLI mutations: Via IaC preferred
- Direct console changes: Emergency only
- Approval required: All mutations

Restrictions:
- No production data (use anonymized)
- Configuration must match production
- Change windows may apply
```

### Production

```markdown
## Production Environment

Permissions:
- AWS CLI mutations: Prohibited (except discovery)
- Direct console changes: Emergency only with ticket
- Approval required: CAB for significant changes

Requirements:
- All changes via CI/CD pipeline
- Change ticket required
- Rollback plan documented
- Post-deployment validation
```

---

## Validation Rules

### Pre-Execution Checks

```markdown
## Guardrail Validation Checklist

### Tagging
- [ ] Required tags present (Environment, Owner, CostCenter)
- [ ] Tag values match allowed patterns
- [ ] DataClassification if data-storing resource

### Security
- [ ] Encryption enabled (at rest)
- [ ] TLS/SSL configured (in transit)
- [ ] Security groups least-privilege
- [ ] No public access unless intentional
- [ ] IAM follows least privilege

### Network
- [ ] Correct VPC and subnet placement
- [ ] Security group rules documented
- [ ] No 0.0.0.0/0 to sensitive ports

### Compliance
- [ ] Logging enabled
- [ ] Backup configured
- [ ] Matches environment policies
- [ ] Change management followed
```

### Automated Checks

```bash
# AWS Config Rules (examples)
- s3-bucket-public-read-prohibited
- s3-bucket-ssl-requests-only
- encrypted-volumes
- rds-storage-encrypted
- ec2-imdsv2-check
- iam-user-no-policies-check
- root-account-mfa-enabled
- cloudtrail-enabled

# Custom Rules
- required-tags-check
- security-group-ingress-check
- vpc-flow-logs-enabled
```

---

## Exception Process

### Requesting an Exception

```markdown
## Exception Request Template

### Finding
[What policy is being excepted]

### Justification
[Why exception is necessary]

### Duration
[Temporary (with date) or permanent]

### Compensating Controls
[Alternative security measures in place]

### Risk Acceptance
[Who is accepting the risk]

### Approval
- [ ] Technical Lead
- [ ] Security Team (if security-related)
- [ ] Documented in change ticket
```

### Exception Documentation

All exceptions must be:
1. Documented in writing
2. Approved by appropriate authority
3. Time-limited where possible
4. Reviewed periodically
5. Tracked for eventual remediation

---

## Compliance Reporting

### Regular Reviews

| Review | Frequency | Owner |
|--------|-----------|-------|
| Tagging compliance | Weekly | Platform team |
| Security posture | Weekly | Security team |
| IAM access review | Quarterly | Security team |
| Policy effectiveness | Quarterly | Governance team |
| Exception review | Monthly | Governance team |

### Compliance Metrics

```markdown
## Key Compliance Indicators

- % of resources with required tags
- # of open security findings
- # of non-compliant resources
- # of active exceptions
- Mean time to remediate findings
```

---

## Customization Guide

**To customize this skill for your organization:**

1. Update tagging requirements in the "Always Do" section
2. Add organization-specific security policies
3. Define environment-specific rules for your tiers
4. Document your exception process
5. Add compliance framework requirements (HIPAA, PCI, SOX, etc.)

Store policy details in:
- `policies/iam-policies.md`
- `policies/network-policies.md`
- `policies/data-policies.md`
- `policies/tagging-policies.md`

---

## Related Skills

- `aws-org-strategy` — Organizational context
- `aws-well-architected` — Security pillar alignment
- `aws-observability-setup` — Logging requirements
- `aws-cli-playbook` — Validation commands
