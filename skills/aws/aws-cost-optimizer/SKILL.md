---
name: aws-cost-optimizer
description: Cost-aware AWS interaction and optimization patterns
version: 1.0.0
category: aws
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-observability-cost]
tools: [Read, Bash]
---

# AWS Cost Optimizer

## Purpose

This skill provides patterns for cost-aware AWS interactions, ongoing cost optimization, and financial governance. Use it to understand costs, identify savings opportunities, and implement cost controls.

## When to Use

- Planning resources with cost considerations
- Analyzing current spending
- Identifying optimization opportunities
- Implementing cost controls and budgets
- Reviewing reserved capacity options

## When NOT to Use

- Billing account configuration changes
- AWS Marketplace purchases
- Enterprise agreement negotiations

---

## Cost Visibility

### Cost Explorer Queries

```bash
# Monthly cost by service (last 3 months)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-04-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --profile {profile}

# Daily cost for current month
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics UnblendedCost \
  --profile {profile}

# Cost by tag (e.g., Environment)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=Environment \
  --profile {profile}

# Cost by account (for Organizations)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=LINKED_ACCOUNT \
  --profile {profile}
```

### Cost Forecast

```bash
# 3-month forecast
aws ce get-cost-forecast \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d "+3 months" +%Y-%m-%d) \
  --granularity MONTHLY \
  --metric UNBLENDED_COST \
  --profile {profile}
```

---

## Budgets

### Budget Configuration

```bash
# Create monthly budget with alert
aws budgets create-budget \
  --account-id {account-id} \
  --budget '{
    "BudgetName": "monthly-total",
    "BudgetLimit": {"Amount": "10000", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {"SubscriptionType": "EMAIL", "Address": "alerts@example.com"}
      ]
    }
  ]' \
  --profile {profile}
```

### Budget Types

| Type | Use Case |
|------|----------|
| Cost Budget | Overall or service-specific spending |
| Usage Budget | Resource usage limits (e.g., EC2 hours) |
| RI Utilization | Reserved Instance coverage |
| Savings Plans Utilization | Savings Plans coverage |

### Budget Strategy

```markdown
## Recommended Budgets

### Account Level
- Total monthly budget with 80%, 100%, 120% alerts
- Per-service budgets for top 3-5 services

### Environment Level
- Production budget (track actual vs expected)
- Development budget (cap to prevent waste)
- Sandbox budget (strict limit)

### Team Level
- Cost allocation by CostCenter tag
- Alerts to team owners
```

---

## Right-Sizing

### EC2 Right-Sizing

```bash
# Get right-sizing recommendations
aws ce get-rightsizing-recommendation \
  --service EC2 \
  --configuration '{
    "RecommendationTarget": "SAME_INSTANCE_FAMILY",
    "BenefitsConsidered": true
  }' \
  --profile {profile}

# Detailed instance utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-xxxxxxxxx \
  --start-time $(date -d "7 days ago" -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Average Maximum \
  --profile {profile} \
  --region {region}
```

### Right-Sizing Guidelines

| Utilization | Action |
|-------------|--------|
| < 20% average CPU | Consider smaller instance |
| 20-60% average CPU | Likely right-sized |
| > 80% average CPU | Consider larger instance |
| Spiky usage | Consider auto-scaling |

### RDS Right-Sizing

```bash
# RDS utilization check
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value={db-id} \
  --start-time $(date -d "7 days ago" -u +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Average Maximum \
  --profile {profile} \
  --region {region}
```

---

## Reserved Capacity

### Savings Plans

```bash
# Get Savings Plans recommendations
aws ce get-savings-plans-purchase-recommendation \
  --savings-plans-type COMPUTE_SP \
  --term-in-years ONE_YEAR \
  --payment-option NO_UPFRONT \
  --lookback-period-in-days THIRTY_DAYS \
  --profile {profile}

# Current Savings Plans utilization
aws ce get-savings-plans-utilization \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --profile {profile}
```

### Reserved Instances

```bash
# Get RI recommendations
aws ce get-reservation-purchase-recommendation \
  --service EC2 \
  --term-in-years ONE_YEAR \
  --payment-option NO_UPFRONT \
  --lookback-period-in-days THIRTY_DAYS \
  --profile {profile}

# Current RI utilization
aws ce get-reservation-utilization \
  --time-period Start=2024-01-01,End=2024-02-01 \
  --granularity MONTHLY \
  --profile {profile}
```

### Commitment Strategy

```markdown
## Commitment Decision Framework

### Savings Plans (Preferred)
- Compute Savings Plans: Most flexible, covers EC2, Lambda, Fargate
- EC2 Instance Savings Plans: Larger discount, specific instance family

### Reserved Instances (When Needed)
- Use for RDS, ElastiCache, Redshift
- Use when RI-specific features needed (capacity reservation)

### Commitment Levels
| Commitment | Best For |
|------------|----------|
| 1-year No Upfront | Moderate confidence, cash flow preference |
| 1-year All Upfront | High confidence, maximum savings |
| 3-year | Very stable workloads, largest discount |
```

---

## Idle Resources

### Finding Idle Resources

```bash
# Unattached EBS volumes
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[*].[VolumeId,Size,CreateTime]' \
  --output table \
  --profile {profile} \
  --region {region}

# Unassociated Elastic IPs
aws ec2 describe-addresses \
  --filters Name=association-id,Values="" \
  --query 'Addresses[*].[PublicIp,AllocationId]' \
  --output table \
  --profile {profile} \
  --region {region}

# Unused NAT Gateways (check connections)
aws ec2 describe-nat-gateways \
  --filter Name=state,Values=available \
  --profile {profile} \
  --region {region}

# Old snapshots (> 90 days)
aws ec2 describe-snapshots \
  --owner-ids self \
  --query 'Snapshots[?StartTime<=`2024-01-01`].[SnapshotId,VolumeSize,StartTime,Description]' \
  --output table \
  --profile {profile} \
  --region {region}
```

### Cleanup Actions

```bash
# Delete unattached volume (DESTRUCTIVE - ensure backup)
aws ec2 delete-volume \
  --volume-id vol-xxxxxxxxx \
  --profile {profile} \
  --region {region}

# Release Elastic IP
aws ec2 release-address \
  --allocation-id eipalloc-xxxxxxxxx \
  --profile {profile} \
  --region {region}

# Delete old snapshot
aws ec2 delete-snapshot \
  --snapshot-id snap-xxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Cost-Aware Architecture

### Service Selection

| Use Case | Cost-Effective Choice |
|----------|----------------------|
| Variable compute | Lambda or Fargate Spot |
| Steady-state compute | Reserved EC2 or Savings Plans |
| Data storage | S3 with lifecycle policies |
| Database reads | ElastiCache or read replicas |
| Batch processing | Spot instances |

### Data Transfer Optimization

```markdown
## Data Transfer Cost Reduction

### Within AWS
- Use VPC endpoints for AWS services
- Keep resources in same AZ when possible
- Use private IPs instead of public

### To Internet
- Use CloudFront for static content
- Compress data before transfer
- Cache at edge when possible

### Cross-Region
- Minimize cross-region replication
- Use S3 Transfer Acceleration for large uploads
- Consider regional consolidation
```

### Storage Optimization

```bash
# S3 storage analysis
aws s3api list-buckets --query 'Buckets[*].Name' --output text | \
  xargs -I {} sh -c 'echo "Bucket: {}"; aws s3api get-bucket-location --bucket {} 2>/dev/null'

# Enable S3 Intelligent Tiering
aws s3api put-bucket-lifecycle-configuration \
  --bucket {bucket} \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "IntelligentTiering",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [{
        "Days": 0,
        "StorageClass": "INTELLIGENT_TIERING"
      }]
    }]
  }' \
  --profile {profile}
```

---

## Cost Tags

### Tagging Strategy

```markdown
## Required Cost Tags

| Tag | Purpose | Example |
|-----|---------|---------|
| Environment | Environment allocation | production, development |
| CostCenter | Chargeback/showback | CC-1234 |
| Owner | Responsibility | platform-team |
| Project | Project allocation | project-phoenix |

## Tag Enforcement
- Use AWS Organizations SCP to require tags
- Use AWS Config rules to detect untagged resources
- Regular tag compliance reports
```

### Tag Compliance Check

```bash
# Find untagged EC2 instances
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[?!not_null(Tags[?Key==`CostCenter`].Value)].[InstanceId,State.Name]' \
  --output table \
  --profile {profile} \
  --region {region}
```

---

## Cost Optimization Checklist

```markdown
## Monthly Cost Review Checklist

### Visibility
- [ ] Review Cost Explorer trends
- [ ] Check budget alerts
- [ ] Analyze cost by tag/team
- [ ] Identify anomalies

### Right-Sizing
- [ ] Review EC2 utilization
- [ ] Review RDS utilization
- [ ] Check right-sizing recommendations
- [ ] Implement approved changes

### Idle Resources
- [ ] Identify unattached volumes
- [ ] Check unused Elastic IPs
- [ ] Review old snapshots
- [ ] Clean up approved resources

### Reserved Capacity
- [ ] Review RI/SP utilization
- [ ] Check for new recommendations
- [ ] Plan upcoming purchases
- [ ] Adjust coverage as needed

### Architecture
- [ ] Review data transfer costs
- [ ] Check S3 storage classes
- [ ] Evaluate serverless options
- [ ] Consider Spot for suitable workloads
```

---

## Cost Estimation for Planning

When planning new resources:

```markdown
## Cost Estimate Template

### Resource: {Resource Type}

| Component | Quantity | Unit Cost | Monthly Cost |
|-----------|----------|-----------|--------------|
| EC2 (m5.large) | 2 | $0.096/hr | $140 |
| EBS (gp3, 100GB) | 2 | $0.08/GB | $16 |
| Data Transfer | 100GB | $0.09/GB | $9 |
| **Total** | | | **$165** |

### With Optimization
| Option | Savings | New Monthly |
|--------|---------|-------------|
| 1yr Savings Plan | 30% | $115 |
| Spot (if suitable) | 60-70% | ~$60 |

### Recommendation
{Which option and why}
```

---

## Related Skills

- `aws-cli-playbook` — CLI patterns for cost commands
- `aws-well-architected` — Cost optimization pillar
- `aws-governance-guardrails` — Cost policies
- `aws-observability-setup` — Cost of monitoring
