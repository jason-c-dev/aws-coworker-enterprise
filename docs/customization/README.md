# Customization & Governance Guide

This guide explains how to customize AWS Coworker for your organization while maintaining upgrade compatibility and governance standards.

---

## Customization Philosophy

AWS Coworker uses a layered architecture:

```
┌─────────────────────────────────────────┐
│         Your Customizations             │
│    (Organization/BU-specific rules)     │
├─────────────────────────────────────────┤
│         Core Framework                  │
│    (Batteries-included baseline)        │
└─────────────────────────────────────────┘
```

**Key Principles:**

1. **Extend, don't modify** — Add to core, don't change it
2. **Layer specificity** — More specific rules override general ones
3. **Preserve upgradeability** — Keep customizations in designated areas
4. **Document decisions** — Explain why customizations exist

---

## Customization Areas

### Where to Customize

| Location | Purpose | Safe to Modify |
|----------|---------|----------------|
| `skills/org/` | Organization policies | ✅ Yes |
| `config/org-config/` | Organization configuration | ✅ Yes |
| `config/profiles/` | Profile classifications | ✅ Yes |
| `config/environments/` | Environment definitions | ✅ Yes |
| `skills/aws/` | AWS service patterns | ⚠️ Extend only |
| `skills/core/` | Foundational patterns | ⚠️ Extend only |
| `skills/meta/` | Meta-design patterns | ❌ Avoid |
| `.claude/agents/` | Agent definitions | ⚠️ Add new only |
| `.claude/commands/` | Slash commands | ⚠️ Add new only |

### What to Customize

Common customization needs:

- **Tagging policies** — Required tags, allowed values
- **Naming conventions** — Resource naming patterns
- **IAM policies** — Role patterns, permission boundaries
- **Network rules** — CIDR allocations, security group standards
- **Cost policies** — Budget thresholds, instance type restrictions
- **Compliance rules** — Industry-specific requirements

---

## Adding Organization Skills

### Step 1: Create the Skill Directory

```bash
mkdir -p skills/org/your-skill-name
```

### Step 2: Create SKILL.md

```markdown
---
name: your-skill-name
description: Description of your organization-specific skill
version: 1.0.0
category: org
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-guardrail]
tools: [Read]
---

# Your Skill Name

## Purpose

[Why your organization needs this skill]

## When to Use

- [Org-specific scenario 1]
- [Org-specific scenario 2]

## When NOT to Use

- [When core skills suffice]

---

## Guidance

### Your Organization's Standards

[Detailed organizational policies and patterns]

### Examples

[Organization-specific examples]
```

### Step 3: Reference in Governance

If this skill contains mandatory policies, reference it in `skills/org/aws-governance-guardrails/SKILL.md`.

---

## Configuring Governance Guardrails

### Structure

The `skills/org/aws-governance-guardrails/` directory should contain:

```
skills/org/aws-governance-guardrails/
├── SKILL.md                 # Main guardrails skill
└── policies/
    ├── iam-policies.md      # IAM rules
    ├── network-policies.md  # Network rules
    ├── data-policies.md     # Data handling rules
    └── tagging-policies.md  # Tagging requirements
```

### Example: Tagging Policies

```markdown
# Tagging Policies

## Required Tags

All AWS resources MUST have these tags:

| Tag | Description | Example Values |
|-----|-------------|----------------|
| Environment | Deployment environment | sandbox, dev, staging, prod |
| Owner | Team or individual owner | platform-team, john.doe |
| CostCenter | Cost allocation code | CC-1234, CC-5678 |

## Conditional Tags

These tags are required based on context:

| Tag | Required When | Values |
|-----|---------------|--------|
| DataClassification | Contains data | public, internal, confidential, restricted |
| Compliance | Regulated workload | hipaa, pci, sox |

## Tag Value Standards

- Use lowercase
- Use hyphens for spaces
- No special characters except hyphen

## Enforcement

The guardrail agent checks these policies before any resource creation.
Non-compliant resources will be flagged for remediation.
```

---

## Configuring Organization Strategy

### Account Structure

Define your account structure in `skills/org/aws-org-strategy/SKILL.md`:

```markdown
## Account Structure

### Management Account
- Account ID: 000000000000
- Purpose: AWS Organizations management, billing

### Security Account
- Account ID: 111111111111
- Purpose: Security tooling, audit logs, GuardDuty

### Shared Services Account
- Account ID: 222222222222
- Purpose: Shared infrastructure, transit gateway

### Workload Accounts
| Account | ID | Purpose |
|---------|-----|---------|
| Development | 333333333333 | Development workloads |
| Staging | 444444444444 | Pre-production testing |
| Production | 555555555555 | Production workloads |
```

### OU Strategy

Document your OU structure:

```markdown
## Organizational Units

```
Root
├── Security OU
│   └── Security Account
├── Infrastructure OU
│   └── Shared Services Account
├── Workloads OU
│   ├── Non-Production OU
│   │   ├── Development Account
│   │   └── Staging Account
│   └── Production OU
│       └── Production Account
└── Sandbox OU
    └── Sandbox Accounts
```

### Workload Placement

Where workloads should go:

| Workload Type | Target Account | Target OU |
|---------------|----------------|-----------|
| Experiments | Sandbox | Sandbox OU |
| Development | Development | Non-Production OU |
| Testing | Staging | Non-Production OU |
| Production | Production | Production OU |
```

---

## Environment Configuration

### Define Environments

Create `config/environments/environments.yaml`:

```yaml
environments:
  sandbox:
    purpose: Experimentation
    account_pattern: "sandbox-*"
    profiles: [sandbox-admin]
    permissions:
      cli: read-write
      approval: none
    restrictions: []

  development:
    purpose: Active development
    account_pattern: "dev-*"
    profiles: [dev-admin, dev-readonly]
    permissions:
      cli: read-write
      approval: destructive-only
    restrictions:
      - no_production_data

  staging:
    purpose: Pre-production validation
    account_pattern: "staging-*"
    profiles: [staging-readonly]
    permissions:
      cli: read-only
      approval: all-mutations
      change_method: iac-only
    restrictions:
      - change_window_required

  production:
    purpose: Live workloads
    account_pattern: "prod-*"
    profiles: [prod-readonly, prod-admin]
    permissions:
      cli: read-only
      approval: via-cicd
      change_method: iac-only
    restrictions:
      - change_window_required
      - cab_approval_required
      - break_glass_only_for_emergencies
```

---

## Multi-Tenant Setup

For organizations with multiple business units:

### Directory Structure

```
skills/
├── org/                      # Organization-wide
│   ├── aws-org-strategy/
│   └── aws-governance-guardrails/
└── bu/                       # Business unit overlays
    ├── finance/
    │   └── compliance-rules/
    ├── engineering/
    │   └── dev-standards/
    └── data-science/
        └── ml-patterns/
```

### BU-Specific Policies

Create BU overlays that extend org policies:

```markdown
---
name: finance-compliance-rules
description: Additional compliance rules for Finance BU
version: 1.0.0
category: org
extends: aws-governance-guardrails
agents: [aws-coworker-guardrail]
tools: [Read]
---

# Finance Compliance Rules

These rules extend the base governance guardrails for Finance BU.

## Additional Requirements

### SOX Compliance

All Finance workloads must:
- Enable detailed CloudTrail logging
- Use encrypted storage (KMS)
- Implement segregation of duties
- Maintain 7-year audit trails

### Data Classification

Finance data classifications:
- All financial data: `confidential` minimum
- PII: `restricted`
- Audit data: `restricted`
```

---

## Governance Integration

### Change Management Integration

Document how AWS Coworker fits your change management:

```markdown
## Change Management Integration

### Ticket Requirements

All changes require:
- Change ticket number in commit message
- Approval from designated approvers
- Risk assessment for production changes

### CAB Process

Production changes follow CAB process:
1. Submit change request
2. AWS Coworker generates impact assessment
3. CAB reviews and approves
4. AWS Coworker executes via CI/CD

### Emergency Changes

Break-glass process:
1. Document emergency in incident ticket
2. Use prod-admin profile with explicit approval
3. Post-incident review within 24 hours
4. Update runbooks if needed
```

### Audit Trail

Configure audit requirements:

```yaml
# config/org-config/audit.yaml
audit:
  retention_days: 2555  # 7 years for SOX

  required_logs:
    - cloudtrail
    - config
    - vpc_flow_logs
    - s3_access_logs

  siem_integration:
    enabled: true
    destination: your-siem-endpoint

  alerting:
    security_events: immediate
    compliance_violations: within_1_hour
    cost_anomalies: daily
```

---

## Maintaining Customizations

### Version Control

Track customizations in Git:

```bash
# Create branch for customizations
git checkout -b org/initial-customization

# Make changes to skills/org/ and config/

# Commit with clear message
git commit -m "org: add initial governance customizations

- Add tagging policies
- Configure account structure
- Define environment rules"

# Open PR for review
gh pr create --title "Initial organization customizations"
```

### Upgrade Process

When upgrading core AWS Coworker:

1. **Review changelog** for breaking changes
2. **Test in sandbox** with your customizations
3. **Verify compatibility** of org policies
4. **Update if needed** any affected customizations
5. **Document** any changes made

### Rollback

If issues occur:

```bash
# Revert to previous baseline
git checkout baseline/before-upgrade

# Or revert specific customization
git revert <commit-hash>
```

---

## Best Practices

### Do

- ✅ Keep customizations in designated directories
- ✅ Document the "why" behind customizations
- ✅ Test customizations in sandbox first
- ✅ Use version control for all changes
- ✅ Review customizations periodically

### Don't

- ❌ Modify core skills directly
- ❌ Add org-specific content to aws/ skills
- ❌ Skip documentation
- ❌ Make undocumented exceptions
- ❌ Ignore upgrade compatibility

---

## Next Steps

- [Adding Organization Skills](adding-org-skills.md) — Detailed skill creation
- [Governance Integration](governance-integration.md) — Deep dive into compliance
- [Multi-Tenant Setup](multi-tenant-setup.md) — BU overlay patterns
