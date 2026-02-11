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

## Minimum Viable Architecture (MVA)

### Concept

MVA defines what the Well-Architected Framework says you **should** have for a service at a given environment tier. It sits above MNA (Minimum Needed Architecture), which is what's technically required for a service to function at all.

| Term | Definition | Example (CloudFront) |
|------|-----------|---------------------|
| **MNA** | What's technically required to function | An origin and a domain |
| **MVA** | What Well-Architected says you should have | Access logging, TLS 1.2+, custom error pages, WAF integration, OAC for S3 |

**The gap between MNA and MVA is where informed decisions live.** For a test deployment, the user might accept the gap. For production, they should not.

### MVA Baseline Structure

MVA baselines are defined per service in `mva-baselines/{service}.md`. Each file contains environment tiers as sections, with production as the superset:

```
mva-baselines/
├── _TEMPLATE.md        # Reference template for adding new services
├── cloudfront.md       # CloudFront MVA baseline
├── ec2.md              # EC2 MVA baseline
└── s3.md               # S3 MVA baseline
```

Each baseline file follows this structure:
- **Common (All Environments)** — Items required regardless of tier
- **Sandbox** — Additional items (typically none)
- **Development** — Additional items beyond Common
- **Staging** — Additional items beyond Development (enforcement-gated)
- **Production** — Additional items beyond Staging (ALL mandatory)
- **Gap Detection Guide** — How to check, what constitutes a gap, severity, remediation

### MVA Extensibility

MVA baselines follow a layered model. Higher layers can ADD requirements but CANNOT lower core safety:

```
Core MVA (per service)        ← Defined here in skills/aws/aws-well-architected/mva-baselines/
        ↓
Org MVA extensions            ← Defined in skills/org/aws-mva-extensions/ (can ADD items)
        ↓
BU MVA extensions             ← Defined in skills/bu/{bu}/mva-extensions/ (can ADD further)
```

Only the user can accept gaps below core MVA, and only for non-production environments.

---

## Service Appropriateness Check

Before evaluating MVA compliance, the orchestrator MUST evaluate whether the **service choice itself** is appropriate for the use case. This catches architectural failures that per-service MVA cannot detect.

### Why This Matters

A perfectly configured EC2 instance is still the wrong architecture for hosting a static HTML file. The original WAR gave a pass for Cost Optimization on EC2 hosting a static game because it only evaluated the *configuration* of the chosen service, not whether the *choice of service* was appropriate.

### How to Evaluate

Ask: **"Given what the user wants to achieve, is this the right AWS service?"**

| User Goal | Wrong Service | Right Service | Why |
|-----------|--------------|---------------|-----|
| Host static HTML/CSS/JS | EC2 | S3 + CloudFront | No compute needed; CDN is cheaper, faster, more reliable |
| Run a scheduled script once/day | EC2 (24/7) | Lambda + EventBridge | Pay-per-execution vs always-on |
| Simple key-value store | RDS | DynamoDB | Relational DB overhead for non-relational data |
| Host a container with no scaling | ECS + ALB | App Runner | Managed container runtime, no ALB needed |

### Severity

Service inappropriateness is always **High** severity for the **Cost Optimization** pillar. It may also affect **Performance Efficiency** and **Operational Excellence**.

### Output Format

```markdown
### Service Appropriateness
- Use case: {what the user wants to achieve}
- Proposed service: {service}
- Assessment: {APPROPRIATE / INAPPROPRIATE}
- If inappropriate: Recommended alternative: {service} — {reason}
```

---

## WAR Evaluation Instructions (For Orchestrator)

**IMPORTANT:** WAR evaluation is performed by the **primary orchestrator (Opus) inline during planning** — NOT delegated to a sub-agent. The orchestrator already has the user's request, discovery results, and skill context. WAR assessment is a reasoning task that belongs at the orchestration layer.

### Evaluation Procedure

When evaluating a proposed change or deployment, follow these steps in order:

1. **Identify service(s)** being deployed or modified
2. **Check service appropriateness** — Is this the right service for the use case? (see above)
3. **Identify environment tier** from the target profile/account classification
4. **Read enforcement level** from `config/environments/environments.yaml` → `well_architected.enforcement`
5. **Load MVA baseline** from `skills/aws/aws-well-architected/mva-baselines/{service}.md`
6. **Load org/BU extensions** if they exist in `skills/org/aws-mva-extensions/` or `skills/bu/`
7. **Compare proposed architecture** against each MVA item for the target environment tier
8. **Generate findings** using the WAR Findings Format below
9. **Apply execution gate** based on enforcement level

### Enforcement Levels

| Level | Behavior | Critical/High Gaps | Medium/Low Gaps |
|-------|----------|-------------------|-----------------|
| `optional` | Informational only | Show findings, proceed | Show findings, proceed |
| `warn` | Present and acknowledge | Warn, let user proceed with acknowledgment | Informational |
| `strict` | Block on critical/high | **Block execution** — user must resolve or modify plan | Warn, let user proceed |
| `enforce` | Block on all gaps | **Block execution** — no override path | **Block execution** — no override path |

### What NOT to Do

- **DO NOT** skip WAR evaluation for any deployment
- **DO NOT** self-certify with green checkmarks — evaluate against actual MVA baselines
- **DO NOT** allow the planner to generate its own WAR assessment — the orchestrator evaluates
- **DO NOT** proceed past a block without the user modifying the proposed architecture
- **DO NOT** gate sandbox/test deployments — optional/warn enforcement means inform, never block
- **DO NOT** defer WAR to execution time — assess during planning, before plan is finalized

---

## WAR Findings Format

All WAR assessments MUST use this structured format. Emoji-only assessments without detail are prohibited.

```markdown
## Well-Architected Assessment

### Summary
- Service(s): {list of services being deployed/modified}
- Environment: {tier}
- Enforcement: {level from environments.yaml}
- Overall: COMPLIANT | GAPS_NOTED | CRITICAL_GAPS

### Service Appropriateness
- Use case: {what the user wants to achieve}
- Proposed service: {service}
- Assessment: APPROPRIATE | INAPPROPRIATE
- If inappropriate: Recommended alternative: {service} — {reason}

### MVA Baseline Comparison

| Pillar | MVA Item | Status | Gap | Severity | Remediation |
|--------|----------|--------|-----|----------|-------------|
| Security | Access logging enabled | PASS / GAP | {description if gap} | Critical/High/Medium/Low | {how to fix} |
| Security | TLS 1.2 minimum | PASS / GAP | ... | ... | ... |
| ... | ... | ... | ... | ... | ... |

### Execution Gate
- Gate: PROCEED | WARN_AND_PROCEED | BLOCKED
- If BLOCKED: The following gaps must be resolved before execution:
  1. {gap description + required remediation}
  2. ...
- If WARN_AND_PROCEED: The following gaps were acknowledged by the user:
  1. {gap description}
  2. ...
```

### Severity Definitions

| Severity | Definition | Examples |
|----------|-----------|---------|
| **Critical** | Security vulnerability or data loss risk | No encryption, public access to sensitive data, no backup |
| **High** | Significant operational or compliance risk | No logging, no monitoring, wide-open security groups |
| **Medium** | Best practice violation with moderate impact | No lifecycle policy, suboptimal instance type |
| **Low** | Minor improvement opportunity | Missing optional tags, no compression |

---

## Using This Skill

### For Planning (Orchestrator-Inline WAR)

The orchestrator performs WAR evaluation during Step 4a of the plan command, BEFORE constructing the plan. This ensures the plan already incorporates WAR findings.

The old template-based assessment is **DEPRECATED** and must not be used:

```
DEPRECATED — DO NOT USE:
| Pillar | Score | Notes |
| ... | emoji-only | |
```

Instead, use the structured WAR Findings Format above with MVA baseline comparisons.

### For Reviews

Use pillar checklists to validate existing infrastructure, then compare against MVA baselines for the environment tier.

---

## Related Files

Detailed pillar guidance in:
- `pillars/operational-excellence.md`
- `pillars/security.md`
- `pillars/reliability.md`
- `pillars/performance-efficiency.md`
- `pillars/cost-optimization.md`
- `pillars/sustainability.md`

MVA baselines per service:
- `mva-baselines/_TEMPLATE.md` — Reference template for adding new services
- `mva-baselines/cloudfront.md` — CloudFront MVA baseline
- `mva-baselines/ec2.md` — EC2 MVA baseline
- `mva-baselines/s3.md` — S3 MVA baseline

---

## Related Skills

- `aws-cli-playbook` — Implementation patterns
- `aws-governance-guardrails` — Policy compliance
- `aws-cost-optimizer` — Detailed cost analysis
- `aws-observability-setup` — Monitoring implementation
