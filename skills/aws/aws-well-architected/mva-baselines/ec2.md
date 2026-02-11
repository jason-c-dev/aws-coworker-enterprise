# EC2 — MVA Baseline

## Overview

Amazon Elastic Compute Cloud (EC2) provides scalable computing capacity in the cloud.

**MNA (Minimum Needed Architecture):** An AMI, an instance type, and a VPC/subnet to launch into.
**MVA (Minimum Viable Architecture):** IAM instance profile, restricted security groups, EBS encryption, monitoring, governance tagging, and appropriate instance sizing.

**Service Appropriateness Warning:** EC2 is frequently chosen when a simpler, cheaper service would be more appropriate. Before evaluating EC2 MVA, the orchestrator MUST check whether EC2 is the right service for the use case (see Service Appropriateness Check in SKILL.md). Common misuses include: static website hosting (use S3 + CloudFront), scheduled scripts (use Lambda + EventBridge), containerized apps with simple scaling (use App Runner or Fargate).

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | No 0.0.0.0/0 ingress on SSH (port 22) or RDP (port 3389) | Critical | Wide-open remote access is the most common EC2 security failure |
| Security | IAM instance profile attached (no long-lived credentials on instance) | High | Credentials on disk are a security risk; use roles |
| Security | EBS volumes encrypted | High | Unencrypted volumes expose data at rest |
| Cost Optimization | Instance type appropriate for workload (not over-provisioned) | Medium | Oversized instances waste money |
| Operational Excellence | Governance tags applied (7 core tags) | High | Untagged resources violate governance compliance |
| Operational Excellence | All supporting resources tagged (EBS volumes, security groups, key pairs) | High | Supporting resources must be tracked for cost allocation and audit |

---

## Sandbox

No additional items beyond Common. Sandbox prioritizes experimentation.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| — | No additional items | — | Sandbox prioritizes experimentation |

---

## Development

Additional items beyond Common for development environments.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Security group ingress restricted to known CIDRs (not 0.0.0.0/0 for any port) | Medium | Dev environments should not be globally accessible |
| Security | Key pair managed (not shared, not committed to git) | Medium | Shared keys prevent accountability |
| Reliability | Instance in a VPC with appropriate subnet (private for non-web workloads) | Medium | Default VPC public subnets expose instances unnecessarily |
| Operational Excellence | CloudWatch basic monitoring enabled | Low | Default monitoring provides CPU, disk, network metrics |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Security group ingress limited to application ports only (no unnecessary open ports) | High | Staging mirrors production security posture |
| Reliability | Instance in private subnet with NAT gateway for outbound | High | Staging should mirror production network topology |
| Reliability | EBS snapshots or backup plan configured | Medium | Data recovery capability required for staging |
| Performance Efficiency | Instance type benchmarked for workload (not default t2.micro) | Medium | Staging should use representative sizing |
| Operational Excellence | CloudWatch detailed monitoring enabled | Medium | 1-minute metrics for staging validation |
| Operational Excellence | Systems Manager agent installed (for patching) | Medium | Patch management should be validated in staging |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Termination protection enabled | High | Prevents accidental deletion of production instances |
| Security | IMDSv2 enforced (disable IMDSv1) | High | IMDSv1 is vulnerable to SSRF attacks |
| Reliability | Multi-AZ deployment (Auto Scaling Group or multiple instances) | High | Single instance is a single point of failure |
| Reliability | Automated backups with tested restore procedure | High | Production data must be recoverable |
| Reliability | Health checks configured (ELB or Auto Scaling) | High | Unhealthy instances must be detected and replaced |
| Performance Efficiency | Right-sized based on actual utilization data | Medium | Production sizing should be data-driven, not guessed |
| Cost Optimization | Reserved Instances or Savings Plan evaluated for steady-state workloads | Medium | On-demand pricing for 24/7 workloads is wasteful |
| Operational Excellence | CloudWatch alarms for CPU, memory, disk, and status checks | High | Production must have monitoring and alerting |
| Operational Excellence | Deployed via IaC (CDK/Terraform/CloudFormation), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | No 0.0.0.0/0 on SSH/RDP | R | R | R | R | Critical |
| Security | IAM instance profile | R | R | R | R | High |
| Security | EBS encryption | R | R | R | R | High |
| Security | SG restricted to known CIDRs | - | R | R | R | Medium |
| Security | Key pair managed | - | R | R | R | Medium |
| Security | SG limited to app ports only | - | - | R | R | High |
| Security | Termination protection | - | - | - | R | High |
| Security | IMDSv2 enforced | - | - | - | R | High |
| Reliability | VPC with appropriate subnet | - | R | R | R | Medium |
| Reliability | Private subnet + NAT | - | - | R | R | High |
| Reliability | EBS snapshots/backup | - | - | R | R | Medium |
| Reliability | Multi-AZ deployment | - | - | - | R | High |
| Reliability | Automated backup + tested restore | - | - | - | R | High |
| Reliability | Health checks | - | - | - | R | High |
| Performance Efficiency | Appropriate instance type | R | R | R | R | Medium |
| Performance Efficiency | Benchmarked sizing | - | - | R | R | Medium |
| Performance Efficiency | Right-sized from utilization data | - | - | - | R | Medium |
| Cost Optimization | Instance type not over-provisioned | R | R | R | R | Medium |
| Cost Optimization | RI/Savings Plan evaluated | - | - | - | R | Medium |
| Operational Excellence | Governance tags (all resources) | R | R | R | R | High |
| Operational Excellence | Basic monitoring | - | R | R | R | Low |
| Operational Excellence | Detailed monitoring | - | - | R | R | Medium |
| Operational Excellence | Systems Manager agent | - | - | R | R | Medium |
| Operational Excellence | CloudWatch alarms | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### No 0.0.0.0/0 on SSH/RDP

- **Check command:** `aws ec2 describe-security-groups --group-ids {sg_id}`
- **Gap condition:** Any `IpPermissions` entry has `FromPort` 22 or 3389 with `IpRanges[].CidrIp` of `0.0.0.0/0` or `Ipv6Ranges[].CidrIpv6` of `::/0`
- **Severity:** Critical
- **Remediation:** `aws ec2 revoke-security-group-ingress` to remove wide-open rule, then `aws ec2 authorize-security-group-ingress` with specific CIDR
- **Remediation description:** Restricts SSH/RDP access to known IP ranges

### IAM Instance Profile

- **Check command:** `aws ec2 describe-instances --instance-ids {instance_id} --query 'Reservations[].Instances[].IamInstanceProfile'`
- **Gap condition:** `IamInstanceProfile` is null or empty
- **Severity:** High
- **Remediation:** Create IAM role and instance profile, then `aws ec2 associate-iam-instance-profile`
- **Remediation description:** Attaches IAM role for secure credential management

### EBS Encryption

- **Check command:** `aws ec2 describe-volumes --filters "Name=attachment.instance-id,Values={instance_id}"`
- **Gap condition:** Any volume has `Encrypted: false`
- **Severity:** High
- **Remediation:** Enable EBS encryption by default (`aws ec2 enable-ebs-encryption-by-default`), then re-create unencrypted volumes from encrypted snapshots
- **Remediation description:** Ensures all EBS volumes are encrypted at rest

### Security Group Ingress

- **Check command:** `aws ec2 describe-security-groups --group-ids {sg_id}`
- **Gap condition:** Any `IpPermissions` entry has `CidrIp` of `0.0.0.0/0` (for any port, not just SSH/RDP)
- **Severity:** Medium (dev), High (staging/prod)
- **Remediation:** Replace `0.0.0.0/0` rules with specific CIDRs
- **Remediation description:** Restricts network access to known sources

### Termination Protection

- **Check command:** `aws ec2 describe-instance-attribute --instance-id {instance_id} --attribute disableApiTermination`
- **Gap condition:** `DisableApiTermination.Value` is `false`
- **Severity:** High (production only)
- **Remediation:** `aws ec2 modify-instance-attribute --instance-id {instance_id} --disable-api-termination`
- **Remediation description:** Prevents accidental termination of production instances

### IMDSv2 Enforcement

- **Check command:** `aws ec2 describe-instances --instance-ids {instance_id} --query 'Reservations[].Instances[].MetadataOptions'`
- **Gap condition:** `HttpTokens` is not `required`
- **Severity:** High (production only)
- **Remediation:** `aws ec2 modify-instance-metadata-options --instance-id {instance_id} --http-tokens required`
- **Remediation description:** Disables IMDSv1 to prevent SSRF credential theft

### Governance Tags

- **Check command:** `aws ec2 describe-tags --filters "Name=resource-id,Values={instance_id}"`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws ec2 create-tags --resources {instance_id} --tags Key=...,Value=...`
- **Remediation description:** Applies required governance tags for compliance

### CloudWatch Alarms

- **Check command:** `aws cloudwatch describe-alarms --alarm-name-prefix {instance-name}`
- **Gap condition:** No alarms exist for CPUUtilization, StatusCheckFailed, or disk/memory metrics
- **Severity:** High (production only)
- **Remediation:** Create CloudWatch alarms for critical metrics
- **Remediation description:** Alerts on instance health and performance degradation

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- EC2 is frequently the wrong service choice — always check service appropriateness first
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/ec2.md` for CLI command reference
