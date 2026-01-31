# Single Account Strategy

## When to Use
This strategy is ideal for:
- Early-stage startups and small businesses
- Proof of concept (PoC) and pilot projects
- Development teams with limited AWS workloads
- Organizations just beginning their AWS journey
- Non-production environments or testing only

**Advantages:**
- Minimal operational overhead
- Straightforward billing and cost tracking
- Simple IAM management
- Faster onboarding for small teams

**Limitations:**
- No environment isolation (dev/test/prod in same account)
- Blast radius for security incidents affects all workloads
- Limited cost allocation between teams
- Difficult to enforce separate security policies
- Does not scale beyond initial growth phase

## Architecture Overview
```
┌─────────────────────────────────────────┐
│        AWS Account                      │
│  (Single - Development + Testing)       │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   VPC (Primary)                  │  │
│  │                                  │  │
│  │  ┌──────────────────────────────┐│  │
│  │  │  Public Subnets              ││  │
│  │  │  - ALB/NAT Gateway           ││  │
│  │  │  - Bastion Host (optional)   ││  │
│  │  └──────────────────────────────┘│  │
│  │                                  │  │
│  │  ┌──────────────────────────────┐│  │
│  │  │  Private Subnets             ││  │
│  │  │  - EC2 instances             ││  │
│  │  │  - RDS/Databases             ││  │
│  │  │  - Application servers       ││  │
│  │  └──────────────────────────────┘│  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                         │
│  AWS Services:                          │
│  - EC2, RDS, S3, Lambda, CloudFront    │
│  - CloudWatch, SNS, SQS                │
└─────────────────────────────────────────┘
```

## Account Structure

### Single AWS Account
- **Purpose:** Centralized platform for all development and testing workloads
- **Environment:** Development, Testing, and Staging (shared)
- **Key services:** EC2, RDS, S3, Lambda, VPC, CloudWatch, CloudFormation
- **Owner:** Platform team or DevOps team
- **Root email:** account-owner@company.com

## Naming Conventions
| Resource Type | Pattern | Example |
|--------------|---------|---------|
| AWS Account | `{org}-{env}-account` | `acme-dev-account` |
| VPC | `{org}-{env}-vpc` | `acme-dev-vpc` |
| Subnet | `{org}-{env}-{tier}-subnet-{az}` | `acme-dev-public-subnet-1a` |
| Security Group | `{org}-{env}-{component}-sg` | `acme-dev-web-sg` |
| IAM Role | `{org}-{env}-{service}-role` | `acme-dev-lambda-role` |
| S3 Bucket | `{org}-{region}-{purpose}-{account-id}` | `acme-us-east-1-logs-123456789012` |
| EC2 Instance | `{org}-{env}-{component}-{number}` | `acme-dev-web-001` |

## Tagging Strategy
**Required Tags (All Resources):**
- `Environment`: dev or test
- `Owner`: team-name or person-email
- `CostCenter`: cost-center-id
- `Project`: project-name
- `Application`: application-name
- `CreatedDate`: YYYY-MM-DD
- `BackupPolicy`: daily, weekly, never
- `ManagedBy`: terraform, manual, cloudformation

**Example:**
```
{
  "Environment": "dev",
  "Owner": "platform-team",
  "CostCenter": "1001",
  "Project": "web-app",
  "Application": "api-service",
  "CreatedDate": "2024-01-15",
  "BackupPolicy": "daily",
  "ManagedBy": "terraform"
}
```

## Security Baseline

### Service Control Policies (SCPs)
Not applicable for single account - focus on IAM policies instead.

### IAM Best Practices
- **Root Account Protection:**
  - Enable MFA on root account
  - Do not use root account for daily operations
  - Create an admin IAM user with MFA
  - Store root credentials in secure location

- **User Access Management:**
  - Create IAM users per team member
  - Group users by role (developer, devops, readonly)
  - Enforce MFA for all human users
  - Rotate access keys every 90 days
  - Use temporary credentials (STS) where possible

- **Service Roles:**
  - Create least-privilege roles for EC2, Lambda, ECS
  - Use inline policies only for temporary workarounds
  - Document all role permissions

### GuardDuty Setup
- Enable GuardDuty in primary region
- Create CloudWatch Events rule to trigger SNS notification on findings
- Set up daily digest of findings
- Review high-severity findings immediately
- Archive false positives to reduce noise

### AWS Config Rules
Enable these core rules:
- `root-account-mfa-enabled`: Ensure MFA on root
- `iam-policy-no-statements-with-admin-access`: Detect overly permissive policies
- `rds-encryption-enabled`: Enforce database encryption
- `s3-bucket-public-read-prohibited`: Prevent public S3 buckets
- `s3-bucket-public-write-prohibited`: Prevent public write access
- `cloudtrail-enabled`: Ensure API logging
- `ec2-security-group-ssh-restricted`: Restrict SSH access
- `restricted-ssh`: Limit SSH source IPs

### Logging & Auditing
- Enable CloudTrail in all regions
- Store CloudTrail logs in S3 with versioning enabled
- Enable S3 MFA delete protection
- Enable VPC Flow Logs for all subnets
- Enable ELB access logs

## Network Design

### VPC Strategy
- **Single VPC:** 1 primary VPC for all workloads
- **CIDR Block:** /16 network (e.g., 10.0.0.0/16) with room for future expansion
- **High Availability:** Deploy across 2-3 availability zones

### Subnet Layout
```
VPC: 10.0.0.0/16

Public Subnets (NAT Gateway, ALB):
- 10.0.1.0/24   (us-east-1a)
- 10.0.2.0/24   (us-east-1b)

Private Subnets (Applications):
- 10.0.10.0/24  (us-east-1a)
- 10.0.11.0/24  (us-east-1b)

Database Subnets (RDS):
- 10.0.20.0/24  (us-east-1a)
- 10.0.21.0/24  (us-east-1b)
```

### DNS Approach
- Use Route 53 for DNS management (optional)
- Or use AWS-provided DNS (vpc-ip-address.region.compute.internal)
- For external domains, point to Route 53 name servers

### Internet Connectivity
- Single NAT Gateway in public subnet (cost-effective, but single point of failure)
- Internet Gateway for public subnet egress
- Security group rules to restrict traffic flows

## Cost Management

### Budget Setup
- Set up AWS Budgets for account-level monitoring
- Alert threshold: 80% of monthly budget
- Create custom cost allocation dashboard in CloudWatch

### Cost Allocation Tags
Enforce these tags for cost allocation:
- `CostCenter`: For chargeback
- `Project`: For project tracking
- `Environment`: For environment separation
- `Owner`: For team assignment

### Billing Approach
- Enable Cost Explorer to track spending trends
- Review costs weekly as part of team standup
- Use EC2 Reserved Instances for predictable workloads (optional for dev)
- Identify unused resources monthly (unattached EBS, orphaned security groups)

### Cost Optimization Tips
- Use t3.micro or t3.small for non-production workloads
- Schedule non-essential resources (turn off dev/test environments outside work hours)
- Use S3 Intelligent-Tiering for automatic cost optimization
- Delete old snapshots and AMIs regularly

## Migration Path

### When to Evolve to Multi-Account Strategy
Consider upgrading to multi-account when:
- You have multiple teams requiring access isolation
- You need separate dev/test/production environments
- You exceed budget thresholds for single account
- You require different security policies per environment
- You need to limit blast radius for security incidents
- You are preparing for compliance requirements (SOC2, PCI-DSS, HIPAA)

### Evolution Path
1. **Assess Workload Growth:** Review current resource usage and growth trajectory
2. **Identify Team Structure:** Map teams to account ownership
3. **Choose Multi-Account Model:** Basic multi-account vs. Control Tower
4. **Plan Migrations:** Identify workloads to move to new accounts
5. **Automate Provisioning:** Use Terraform or AWS CloudFormation to provision new accounts
6. **Implement Governance:** Enable SCPs and centralized logging
7. **Monitor Transition:** Track costs and performance during migration

## Related Skills
- [aws-iam-identity-center](../aws-iam-identity-center) - For SSO setup when multi-account
- [aws-vpc-networking](../aws-vpc-networking) - For advanced VPC design
- [aws-security-baseline](../aws-security-baseline) - For hardening configurations
- [aws-cost-optimization](../aws-cost-optimization) - For reducing costs
- [aws-terraform-infrastructure](../aws-terraform-infrastructure) - For IaC automation
