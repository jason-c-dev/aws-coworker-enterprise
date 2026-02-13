# RDS — MVA Baseline

## Overview

Amazon Relational Database Service (RDS) provides managed relational databases (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, and Aurora).

**MNA (Minimum Needed Architecture):** A DB instance with an engine, instance class, and storage allocation.
**MVA (Minimum Viable Architecture):** Encryption at rest, no public accessibility, restricted security groups, automated backups, governance tagging, and appropriate instance sizing.

**Service Appropriateness Warning:** RDS is frequently chosen when a simpler, cheaper, or more appropriate service would suffice. Before evaluating RDS MVA, the orchestrator MUST check whether RDS is the right service for the use case (see Service Appropriateness Check in SKILL.md). Common misuses include: simple key-value lookups (use DynamoDB), intermittent/unpredictable workloads (use Aurora Serverless v2), read-heavy caching (use ElastiCache), document storage (use DocumentDB or DynamoDB).

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Storage encryption enabled (at rest) | Critical | Unencrypted databases are the most common RDS compliance violation |
| Security | Public accessibility disabled (`PubliclyAccessible: false`) | Critical | Databases must never be directly accessible from the internet |
| Security | VPC security group restricts ingress to application ports only (no 0.0.0.0/0) | High | Wide-open database ports are a critical security exposure |
| Security | Master user password managed (not hardcoded, use Secrets Manager or IAM auth) | High | Hardcoded credentials are a security risk |
| Operational Excellence | Governance tags applied (7 core tags) | High | Untagged resources violate governance compliance |

---

## Sandbox

No additional items beyond Common. Sandbox prioritises experimentation.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| — | No additional items | — | Sandbox prioritises experimentation |

---

## Development

Additional items beyond Common for development environments.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Reliability | Automated backups enabled (retention >= 1 day) | Medium | Enables point-in-time recovery for accidental data loss |
| Security | DB subnet group uses private subnets only | Medium | Database instances should not be in public subnets |
| Cost Optimization | Instance class appropriate for workload (not over-provisioned) | Low | Dev workloads rarely need large instance classes |
| Operational Excellence | Parameter group customised (not using default) | Low | Custom parameter groups allow engine-specific tuning |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Encryption with KMS (customer-managed or AWS-managed key) | High | KMS provides key management and audit trail |
| Reliability | Multi-AZ deployment enabled | High | Staging should validate high-availability configuration before production |
| Reliability | Automated backup retention >= 7 days | High | Sufficient retention for staging validation and recovery testing |
| Performance Efficiency | Enhanced Monitoring enabled (60s or lower granularity) | High | OS-level metrics required for performance validation |
| Performance Efficiency | Performance Insights enabled | Medium | Query-level performance analysis for staging validation |
| Reliability | Deletion protection enabled | Medium | Prevents accidental deletion of staging databases |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Encryption with KMS customer-managed key | High | Full key management control for production data |
| Security | IAM database authentication enabled | Medium | Eliminates password-based access for application connections |
| Reliability | Automated backup retention >= 14 days | High | Production data must have sufficient recovery window |
| Reliability | Cross-region read replica or automated snapshot copy for DR | High | Production databases must survive regional outages |
| Performance Efficiency | Performance Insights enabled with retention >= 7 days | High | Production query performance must be tracked |
| Cost Optimization | Reserved Instances or Savings Plan evaluated for steady-state workloads | Medium | On-demand pricing for 24/7 databases is wasteful |
| Operational Excellence | Audit logging enabled (CloudWatch Logs for slow query, error, general logs) | High | Production databases must have audit and diagnostic logging |
| Operational Excellence | CloudWatch alarms for CPU, memory, connections, replication lag, and storage | High | Production must have monitoring and alerting |
| Operational Excellence | Deployed via IaC (CDK/Terraform/CloudFormation), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | Storage encryption at rest | R | R | R | R | Critical |
| Security | Public accessibility disabled | R | R | R | R | Critical |
| Security | Security group restricts ingress | R | R | R | R | High |
| Security | Master password managed | R | R | R | R | High |
| Security | DB subnet group in private subnets | - | R | R | R | Medium |
| Security | Encryption with KMS | - | - | R | R | High |
| Security | KMS customer-managed key | - | - | - | R | High |
| Security | IAM database authentication | - | - | - | R | Medium |
| Reliability | Automated backups (>= 1 day) | - | R | R | R | Medium |
| Reliability | Multi-AZ deployment | - | - | R | R | High |
| Reliability | Backup retention >= 7 days | - | - | R | R | High |
| Reliability | Backup retention >= 14 days | - | - | - | R | High |
| Reliability | Cross-region replica or snapshot copy | - | - | - | R | High |
| Reliability | Deletion protection | - | - | R | R | Medium |
| Performance Efficiency | Enhanced Monitoring | - | - | R | R | High |
| Performance Efficiency | Performance Insights | - | - | R | R | Medium/High |
| Cost Optimization | Instance class appropriate | - | R | R | R | Low |
| Cost Optimization | Reserved Instances / Savings Plan | - | - | - | R | Medium |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | Custom parameter group | - | R | R | R | Low |
| Operational Excellence | Audit logging (CloudWatch) | - | - | - | R | High |
| Operational Excellence | CloudWatch alarms | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Storage Encryption at Rest

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].StorageEncrypted'`
- **Gap condition:** Returns `false`
- **Severity:** Critical
- **Remediation:** Encryption cannot be enabled on an existing unencrypted instance. Create an encrypted snapshot and restore from it, or create a new encrypted instance and migrate data.
- **Remediation description:** Ensures data at rest is encrypted (note: requires instance recreation if not set at creation)

### Public Accessibility

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].PubliclyAccessible'`
- **Gap condition:** Returns `true`
- **Severity:** Critical
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --no-publicly-accessible --apply-immediately`
- **Remediation description:** Disables public accessibility so the instance is only reachable within the VPC

### Security Group Ingress

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].VpcSecurityGroups[*].VpcSecurityGroupId'` then `aws ec2 describe-security-groups --group-ids {sg_ids} --query 'SecurityGroups[*].IpPermissions'`
- **Gap condition:** Any ingress rule allows `0.0.0.0/0` or `::/0`
- **Severity:** High
- **Remediation:** `aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port {db_port} --cidr 0.0.0.0/0`
- **Remediation description:** Removes wide-open ingress and restricts to known application CIDRs

### Automated Backups

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].BackupRetentionPeriod'`
- **Gap condition:** Returns `0` (backups disabled) or less than required retention for tier
- **Severity:** Medium (dev), High (staging/prod)
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --backup-retention-period {days} --apply-immediately`
- **Remediation description:** Enables automated backups with specified retention period

### Multi-AZ Deployment

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].MultiAZ'`
- **Gap condition:** Returns `false`
- **Severity:** High (staging/prod)
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --multi-az --apply-immediately`
- **Remediation description:** Enables Multi-AZ for automatic failover to standby instance

### Enhanced Monitoring

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].MonitoringInterval'`
- **Gap condition:** Returns `0` (disabled)
- **Severity:** High (staging/prod)
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --monitoring-interval 60 --monitoring-role-arn {role_arn}`
- **Remediation description:** Enables Enhanced Monitoring for OS-level metrics at 60-second granularity

### Performance Insights

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].PerformanceInsightsEnabled'`
- **Gap condition:** Returns `false`
- **Severity:** Medium (staging), High (prod)
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --enable-performance-insights --performance-insights-retention-period {days}`
- **Remediation description:** Enables Performance Insights for query-level performance analysis

### Deletion Protection

- **Check command:** `aws rds describe-db-instances --db-instance-identifier {instance_id} --query 'DBInstances[0].DeletionProtection'`
- **Gap condition:** Returns `false`
- **Severity:** Medium (staging), High (prod)
- **Remediation:** `aws rds modify-db-instance --db-instance-identifier {instance_id} --deletion-protection`
- **Remediation description:** Prevents accidental deletion of the database instance

### Governance Tags

- **Check command:** `aws rds list-tags-for-resource --resource-name {db_arn}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws rds add-tags-to-resource --resource-name {db_arn} --tags Key=...,Value=...`
- **Remediation description:** Applies required governance tags for compliance

### CloudWatch Alarms

- **Check command:** `aws cloudwatch describe-alarms --alarm-name-prefix {instance_id}`
- **Gap condition:** No alarms exist for CPUUtilization, FreeableMemory, DatabaseConnections, ReplicaLag, or FreeStorageSpace
- **Severity:** High (production only)
- **Remediation:** Create CloudWatch alarms using RDS metrics
- **Remediation description:** Alerts on elevated resource usage, connection saturation, replication issues, and storage exhaustion

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- RDS encryption MUST be set at creation time — it cannot be enabled on an existing unencrypted instance without recreation
- Multi-AZ modifications can cause a brief outage during failover configuration
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/rds.md` for CLI command reference
