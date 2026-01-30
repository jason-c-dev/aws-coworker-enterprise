# Common Workflows

This guide covers common AWS Coworker workflows with detailed examples.

> **Note:** All examples in this guide—whether explicit commands (starting with `/aws-coworker-`) or free-form prompts—are automatically routed through AWS Coworker commands. The [CLAUDE.md](../../CLAUDE.md) configuration enforces this safety model regardless of how you phrase your request.

---

## Discovery Workflows

### Account Inventory

Get a comprehensive view of resources in an account:

```
User: "Give me an inventory of this AWS account"

AWS Coworker will:
1. Announce profile/region
2. Query major services:
   - EC2 instances
   - S3 buckets
   - RDS databases
   - Lambda functions
   - VPCs and subnets
3. Summarize findings
```

### Security Posture Check

Review security configuration:

```
User: "Check the security posture of this account"

AWS Coworker will:
1. Check for public S3 buckets
2. Review security group rules
3. Audit IAM policies
4. Check CloudTrail status
5. Review encryption settings
6. Report findings with severity
```

### Cost Overview

Understand spending patterns:

```
User: "Show me cost breakdown for this account"

AWS Coworker will:
1. Query Cost Explorer
2. Show spend by service
3. Identify top cost drivers
4. Highlight recent changes
5. Suggest optimization opportunities
```

---

## Planning Workflows

### Plan a Resource Creation

```
User: /aws-coworker-plan-interaction

"I need to create a new VPC for our development environment"

AWS Coworker will:
1. Gather requirements:
   - CIDR range
   - Availability zones
   - Public/private subnets
   - NAT gateway needs
2. Check against governance policies
3. Generate detailed plan with:
   - Proposed configuration
   - CLI commands or IaC
   - Tagging requirements
   - Estimated costs
4. Present for approval
```

### Plan a Migration

```
User: /aws-coworker-plan-interaction

"Plan migrating our EC2 instances from us-east-1 to us-west-2"

AWS Coworker will:
1. Inventory source resources
2. Identify dependencies
3. Plan migration sequence
4. Consider:
   - AMI copying
   - EBS snapshot transfer
   - Security group recreation
   - DNS updates
5. Generate rollback plan
6. Estimate downtime
```

---

## Execution Workflows

### Execute in Non-Production

```
User: /aws-coworker-execute-nonprod

"Execute the VPC creation plan we discussed"

AWS Coworker will:
1. Confirm environment is non-prod
2. Restate profile/region
3. Show commands to execute
4. Request explicit approval
5. Execute commands sequentially
6. Validate each step
7. Report completion or errors
```

### Prepare Production Change

```
User: /aws-coworker-prepare-prod-change

"Prepare the VPC changes for production"

AWS Coworker will:
1. Confirm this is for production
2. Generate IaC templates (CDK/TF/CFN)
3. Create PR with changes
4. Include:
   - Change description
   - Impact assessment
   - Rollback instructions
   - Testing checklist
5. Report PR ready for review
```

---

## Compliance Workflows

### Tag Compliance Check

```
User: "Check tag compliance across all EC2 instances"

AWS Coworker will:
1. Load tagging policy from governance
2. Query all EC2 instances
3. Check each against required tags
4. Report:
   - Compliant resources
   - Non-compliant resources
   - Missing tags per resource
5. Suggest remediation
```

### Security Group Audit

```
User: "Audit security groups for risky rules"

AWS Coworker will:
1. Query all security groups
2. Check for:
   - 0.0.0.0/0 ingress
   - Overly permissive port ranges
   - Unused security groups
   - Overlapping rules
3. Classify risk levels
4. Generate findings report
```

---

## Maintenance Workflows

### Resource Cleanup

```
User: "Find unused resources that could be cleaned up"

AWS Coworker will:
1. Check for:
   - Unattached EBS volumes
   - Unused Elastic IPs
   - Old snapshots
   - Idle load balancers
   - Orphaned ENIs
2. Estimate cost savings
3. Generate cleanup plan
4. Wait for approval before any deletion
```

### Update Tags in Bulk

```
User: /aws-coworker-plan-interaction

"Add the CostCenter tag to all EC2 instances in development"

AWS Coworker will:
1. Query target instances
2. Show current tag state
3. Generate tagging commands
4. Present plan for approval
5. Execute via /aws-coworker-execute-nonprod
```

---

## Troubleshooting Workflows

### Investigate an Issue

```
User: "Our application in the dev environment is having connectivity issues"

AWS Coworker will:
1. Gather context:
   - Which resources?
   - What symptoms?
2. Check:
   - Security groups
   - NACLs
   - Route tables
   - VPC flow logs
   - Load balancer health
3. Identify likely causes
4. Suggest remediation
```

### Review Recent Changes

```
User: "What changed in this account in the last 24 hours?"

AWS Coworker will:
1. Query CloudTrail
2. Filter for write events
3. Summarize:
   - Who made changes
   - What resources affected
   - Change types
4. Highlight unusual activity
```

---

## Meta Workflows

### Create a New Skill

```
User: /aws-coworker-new-skill-from-session

"Create a skill based on the EKS patterns we've been using"

AWS Coworker will:
1. Analyze recent EKS interactions
2. Identify patterns and best practices
3. Create skill structure:
   - SKILL.md with frontmatter
   - Examples directory
4. Create Git branch
5. Present for review
```

### Audit the Library

```
User: /aws-coworker-audit-library

AWS Coworker will:
1. Inventory all components
2. Check structural validity
3. Identify:
   - Missing documentation
   - Inconsistent naming
   - Orphaned files
   - Coverage gaps
4. Generate audit report
5. Recommend improvements
```

---

## Always-Agent Mode Workflows

AWS Coworker operates in **Always-Agent Mode**: every request spawns at least one agent. Thresholds (configurable in `.claude/config/orchestration-config.md`) determine whether to use single or parallel agents.

### Simple Workflow (Below Thresholds)

```
User: "List my S3 buckets"

AWS Coworker:
  [Single agent executes]

  Found 12 buckets in us-east-1:
  - my-app-data (private)
  - my-logs (private)
  - my-static-assets (public-read)
  ...
```

Even simple tasks use the same agent-based execution path — just with a single agent.

### Complex Workflow (Above Thresholds)

When scope exceeds configured thresholds, AWS Coworker spawns parallel agents.

#### Multi-Region Audit

```
User: "Audit all S3 buckets for public access across all regions"

AWS Coworker:
1. [Single agent performs discovery]
   "Found 847 buckets across 8 regions."

2. [Threshold evaluation]
   - Resources: 847 >= 50 (parallel threshold) ✓
   - Regions: 8 > 3 (parallel threshold) ✓

3. [User advisement]
   "Estimated audit time: 8-10 minutes.
    I'll use 8 parallel agents (one per region). Proceed?"

4. [After approval: parallel execution]
   Starting audit with 8 parallel agents...
   ├── us-east-1: Scanning 150 buckets... ✓
   ├── us-west-2: Scanning 120 buckets... ✓
   ├── eu-west-1: Scanning 100 buckets... ✓
   ... (5 more regions)

5. [Aggregation]
   Audit complete (3m 45s). Found 12 buckets with public access.
```

#### Multi-Account Compliance Check

```
User: "Check compliance across all our AWS accounts"

AWS Coworker:
1. [Discovery] Identifies 12 accounts in scope
2. [Threshold evaluation]
   - Accounts: 12 >= 10 (parallel_required) ✓
3. [User advisement]
   "This spans 12 accounts. Estimated time: 12-15 minutes.
    I'll use 10 parallel agents. Proceed?"
4. [Parallel execution] Sub-agents per account
5. [Aggregation] Organization-wide report
```

#### Bulk Remediation

```
User: "Tag all untagged EC2 instances with Owner=platform-team"

AWS Coworker:
1. [Discovery] Found 234 untagged instances across 4 regions
2. [Threshold evaluation]
   - Resources: 234 >= 200 (parallel_required) ✓
3. [User advisement]
   "This is a mutation affecting 234 instances.
    I'll use 5 parallel agents (batches of 50). Proceed?"
4. [Mutation approval] Explicit confirmation required
5. [Parallel execution] Batched tagging
6. [Report] Success/failure per resource
```

### Progress During Parallel Operations

```
Starting compliance audit with 10 parallel agents...

Progress:
├── account-a (us-east-1): Scanning 45 resources... ✓
├── account-b (us-east-1): Scanning 120 resources... ✓
├── account-c (us-west-2): Scanning 89 resources... [in progress]
├── account-d (eu-west-1): Scanning 67 resources... [queued]
...

Completed: 8/12 accounts (67%)
Estimated remaining: 3 minutes
```

### Configuring Thresholds

Edit `.claude/config/orchestration-config.md` to adjust:

| Setting | Default | Effect |
|---------|---------|--------|
| `resources.single_agent` | 50 | Below this: single agent |
| `regions.single_agent` | 3 | At or below this: single agent |
| `limits.max_parallel_agents` | 10 | Cap on concurrent agents |

Lower thresholds = more parallelization (faster but more overhead)
Higher thresholds = less parallelization (simpler but slower for large tasks)

---

## Workflow Best Practices

### Start with Discovery

Always understand current state before making changes:

```
1. Run discovery queries
2. Review current configuration
3. Identify dependencies
4. Then plan changes
```

### Use Planning Before Execution

Never skip the planning step:

```
1. /aws-coworker-plan-interaction
2. Review the plan
3. /aws-coworker-execute-nonprod (if non-prod)
4. Or /aws-coworker-prepare-prod-change (if prod)
```

### Verify After Execution

Always validate changes:

```
1. Execute the change
2. Run verification commands
3. Check application behavior
4. Monitor for issues
```

### Document Decisions

Keep a record of significant decisions:

```
1. Note why a particular approach was chosen
2. Document any deviations from standard patterns
3. Update relevant skills if patterns evolve
```

---

## Next Steps

- [Customization Guide](../customization/README.md) — Adapt AWS Coworker to your organization
- [Design Document](../DESIGN.md) — Deep dive into architecture
