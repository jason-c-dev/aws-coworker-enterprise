---
name: aws-well-architected
description: AWS Well-Architected Framework alignment for planning and review
version: 1.0.0
category: aws
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-guardrail]
tools: [Read]
---

# AWS Well-Architected Framework

## Purpose

This skill encodes the AWS Well-Architected Framework's six pillars as heuristics and checklists for planning and reviewing AWS interactions. Use it to ensure architectural decisions align with AWS best practices.

## When to Use

- Planning new AWS resources or architectures
- Reviewing existing infrastructure
- Validating proposed changes
- Assessing compliance with best practices
- Identifying improvement opportunities

## When NOT to Use

- Emergency fixes (address immediate issue, then review)
- Cost-only analysis (use `aws-cost-optimizer` for detailed cost work)
- Compliance-only validation (use `aws-governance-guardrails`)

---

## The Six Pillars

| Pillar | Focus |
|--------|-------|
| Operational Excellence | Operations, automation, improvement |
| Security | Protection, detection, response |
| Reliability | Recovery, resilience, availability |
| Performance Efficiency | Right resources, optimization |
| Cost Optimization | Cost awareness, efficiency |
| Sustainability | Environmental impact, efficiency |

---

## Quick Assessment Checklist

For any AWS interaction, consider:

```markdown
## Well-Architected Quick Check

### Operational Excellence
- [ ] Can this be automated/codified?
- [ ] Are operations documented?
- [ ] How will we monitor this?

### Security
- [ ] Least privilege applied?
- [ ] Data encrypted?
- [ ] Logging enabled?

### Reliability
- [ ] Multi-AZ/region considered?
- [ ] Backup/recovery defined?
- [ ] Failure modes understood?

### Performance Efficiency
- [ ] Right-sized for workload?
- [ ] Scaling approach defined?
- [ ] Appropriate service type?

### Cost Optimization
- [ ] Cost-aware sizing?
- [ ] Reserved/spot considered?
- [ ] Idle resource risk?

### Sustainability
- [ ] Efficient resource use?
- [ ] Right region for workload?
- [ ] Scaling matches demand?
```

---

## Pillar 1: Operational Excellence

### Principles

1. **Perform operations as code** — Use IaC, automation
2. **Make frequent, small, reversible changes** — Reduce blast radius
3. **Refine operations procedures frequently** — Continuously improve
4. **Anticipate failure** — Pre-mortems, game days
5. **Learn from all operational failures** — Blameless post-mortems

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you deploy changes? | CI/CD pipeline with approvals |
| How do you monitor? | CloudWatch, alarms, dashboards |
| How do you respond to incidents? | Runbooks, on-call rotation |
| How do you improve? | Regular reviews, metrics tracking |

### Best Practices for AWS Coworker

```markdown
## Operational Excellence Checklist

Infrastructure as Code:
- [ ] Changes defined in CDK/Terraform/CloudFormation
- [ ] Version controlled in Git
- [ ] Deployed via CI/CD pipeline

Monitoring:
- [ ] CloudWatch metrics enabled
- [ ] Alarms for critical metrics
- [ ] Dashboard for visibility

Documentation:
- [ ] Runbooks for common operations
- [ ] Architecture documented
- [ ] Change history maintained
```

---

## Pillar 2: Security

### Principles

1. **Implement a strong identity foundation** — Least privilege, centralized identity
2. **Enable traceability** — Logging, monitoring, auditing
3. **Apply security at all layers** — Network, compute, data
4. **Automate security best practices** — Security as code
5. **Protect data in transit and at rest** — Encryption everywhere
6. **Keep people away from data** — Reduce direct access
7. **Prepare for security events** — Incident response ready

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you manage identities? | SSO, IAM roles, no long-lived credentials |
| How do you detect threats? | GuardDuty, Security Hub, CloudTrail |
| How do you protect data? | KMS encryption, TLS 1.2+, access controls |
| How do you respond to incidents? | Documented IR plan, practiced |

### Best Practices for AWS Coworker

```markdown
## Security Checklist

Identity and Access:
- [ ] IAM roles with least privilege
- [ ] No wildcard (*) permissions
- [ ] MFA for human access
- [ ] Service roles for automation

Detection:
- [ ] CloudTrail enabled (all regions)
- [ ] GuardDuty enabled
- [ ] VPC Flow Logs enabled
- [ ] Security Hub findings reviewed

Data Protection:
- [ ] Encryption at rest (KMS)
- [ ] Encryption in transit (TLS 1.2+)
- [ ] S3 bucket policies restrictive
- [ ] No public access unless intentional

Network:
- [ ] Security groups least privilege
- [ ] No 0.0.0.0/0 to sensitive ports
- [ ] Private subnets for data tier
- [ ] NACLs for additional control
```

---

## Pillar 3: Reliability

### Principles

1. **Automatically recover from failure** — Auto-healing, auto-scaling
2. **Test recovery procedures** — Regular DR tests
3. **Scale horizontally** — Distribute load
4. **Stop guessing capacity** — Auto-scale based on demand
5. **Manage change in automation** — Controlled deployments

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you handle failure? | Auto-scaling, health checks, failover |
| How do you backup data? | Automated backups, tested restores |
| What's your RPO/RTO? | Defined and tested |
| How do you test resilience? | Chaos engineering, DR drills |

### Best Practices for AWS Coworker

```markdown
## Reliability Checklist

Availability:
- [ ] Multi-AZ deployment
- [ ] Load balancer health checks
- [ ] Auto-scaling configured
- [ ] No single points of failure

Backup and Recovery:
- [ ] Automated backups enabled
- [ ] Backup retention appropriate
- [ ] Restore tested recently
- [ ] Cross-region backup (if required)

Change Management:
- [ ] Blue/green or rolling deployments
- [ ] Rollback procedure documented
- [ ] Deployment tested in staging
- [ ] Feature flags for gradual rollout

Resilience:
- [ ] Graceful degradation designed
- [ ] Circuit breakers implemented
- [ ] Timeout and retry logic
- [ ] Dependency failures handled
```

---

## Pillar 4: Performance Efficiency

### Principles

1. **Democratize advanced technologies** — Use managed services
2. **Go global in minutes** — Multi-region when needed
3. **Use serverless architectures** — Where appropriate
4. **Experiment more often** — A/B test, measure
5. **Consider mechanical sympathy** — Understand how services work

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you select resources? | Based on workload requirements, benchmarked |
| How do you monitor performance? | Metrics, tracing, profiling |
| How do you optimize? | Regular review, right-sizing |
| How do you stay current? | Evaluate new services regularly |

### Best Practices for AWS Coworker

```markdown
## Performance Efficiency Checklist

Resource Selection:
- [ ] Instance type matches workload
- [ ] Storage type appropriate (gp3, io2, etc.)
- [ ] Network bandwidth sufficient
- [ ] Managed service preferred when suitable

Monitoring:
- [ ] Response time metrics
- [ ] Resource utilization tracked
- [ ] Bottlenecks identified
- [ ] Baseline established

Optimization:
- [ ] Right-sized (not over-provisioned)
- [ ] Caching used appropriately
- [ ] CDN for static content
- [ ] Database queries optimized
```

---

## Pillar 5: Cost Optimization

### Principles

1. **Implement cloud financial management** — Cost awareness culture
2. **Adopt a consumption model** — Pay only for what you use
3. **Measure overall efficiency** — Cost per business outcome
4. **Stop spending money on undifferentiated heavy lifting** — Managed services
5. **Analyze and attribute expenditure** — Tagging, cost allocation

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you track costs? | Cost Explorer, budgets, alerts |
| How do you right-size? | Regular utilization review |
| How do you use pricing models? | Reserved, Savings Plans, Spot |
| How do you manage demand? | Auto-scaling, scheduling |

### Best Practices for AWS Coworker

```markdown
## Cost Optimization Checklist

Visibility:
- [ ] Cost allocation tags applied
- [ ] Budgets configured
- [ ] Cost anomaly alerts set
- [ ] Regular cost review scheduled

Right-Sizing:
- [ ] Utilization metrics reviewed
- [ ] Over-provisioned resources identified
- [ ] Instance type optimization considered
- [ ] Storage tier appropriate

Pricing Models:
- [ ] Reserved capacity for steady-state
- [ ] Savings Plans evaluated
- [ ] Spot instances for fault-tolerant
- [ ] On-demand only for variable

Waste Elimination:
- [ ] Idle resources identified
- [ ] Unused resources terminated
- [ ] Dev/test scaled down off-hours
- [ ] Old snapshots cleaned up
```

---

## Pillar 6: Sustainability

### Principles

1. **Understand your impact** — Measure carbon footprint
2. **Establish sustainability goals** — Targets and metrics
3. **Maximize utilization** — Reduce idle resources
4. **Anticipate and adopt new offerings** — More efficient services
5. **Use managed services** — Shared, optimized infrastructure
6. **Reduce downstream impact** — Efficient data transfer

### Key Questions

| Question | Good Answer |
|----------|-------------|
| How do you measure impact? | Carbon footprint tracking |
| How do you maximize efficiency? | Right-sizing, auto-scaling |
| How do you select services? | Consider sustainability |
| How do you optimize data? | Lifecycle policies, efficient formats |

### Best Practices for AWS Coworker

```markdown
## Sustainability Checklist

Efficiency:
- [ ] Resources right-sized
- [ ] Auto-scaling matches demand
- [ ] Idle resources minimized
- [ ] Efficient instance types (Graviton)

Data:
- [ ] Data lifecycle policies
- [ ] Efficient storage classes
- [ ] Data transfer minimized
- [ ] Compression used

Services:
- [ ] Serverless where appropriate
- [ ] Managed services preferred
- [ ] Region selection considers sustainability
- [ ] Latest generation resources
```

---

## Using This Skill

### For Planning

Before creating a plan, assess against all six pillars:

```markdown
## Well-Architected Assessment: {Resource/Change}

| Pillar | Score | Notes |
|--------|-------|-------|
| Operational Excellence | ✅/⚠️/❌ | |
| Security | ✅/⚠️/❌ | |
| Reliability | ✅/⚠️/❌ | |
| Performance Efficiency | ✅/⚠️/❌ | |
| Cost Optimization | ✅/⚠️/❌ | |
| Sustainability | ✅/⚠️/❌ | |

### Key Findings
[Summary of findings]

### Recommendations
[Actions to improve alignment]
```

### For Reviews

Use pillar checklists to validate existing infrastructure.

---

## Related Files

Detailed pillar guidance in:
- `pillars/operational-excellence.md`
- `pillars/security.md`
- `pillars/reliability.md`
- `pillars/performance-efficiency.md`
- `pillars/cost-optimization.md`
- `pillars/sustainability.md`

---

## Related Skills

- `aws-cli-playbook` — Implementation patterns
- `aws-governance-guardrails` — Policy compliance
- `aws-cost-optimizer` — Detailed cost analysis
- `aws-observability-setup` — Monitoring implementation
