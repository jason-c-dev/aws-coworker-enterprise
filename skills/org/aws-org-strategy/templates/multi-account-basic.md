# Multi-Account Basic Strategy

## When to Use
This strategy is ideal for:
- Growing organizations with multiple teams
- Organizations needing environment isolation (dev/test/prod)
- Companies requiring cost tracking per team or project
- Teams that need independent resource management
- Organizations avoiding AWS Control Tower complexity

**Advantages:**
- Clear environment separation and isolation
- Cost allocation per account/team
- Independent security policies per account
- Reduced blast radius for security incidents
- Easier compliance auditing per environment

**Limitations:**
- Requires manual account provisioning and management
- More operational overhead than single-account
- Requires manual implementation of cross-account roles
- Limited guardrails compared to Control Tower
- Manual propagation of security policies

## Architecture Overview
```
┌──────────────────────────────────────────────────────────────┐
│             AWS Organization (Root Account)                  │
│                                                              │
│  • Organization management                                  │
│  • Consolidated billing                                     │
│  • CloudTrail aggregation                                   │
└──────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────┐
         │                                             │
    ┌────▼────────┐  ┌──────────────┐  ┌──────────────┐
    │  Management │  │  Production  │  │ Development  │
    │   Account   │  │   Account    │  │   Account    │
    └────────────┘  └──────────────┘  └──────────────┘
         │                │                    │
    • Billing         • EC2 Instances     • Dev Workloads
    • Logging         • RDS (prod)        • Testing
    • IAM Audit       • ALB                • Staging
    • CloudTrail      • CloudFront         • Ephemeral
                      • S3 (data)          • S3 (dev)
```

## Account Structure

### Management Account (Root)
- **Purpose:** Organization management, billing, and centralized logging
- **Environment:** Production-grade security
- **Key services:** AWS Organizations, Consolidated Billing, CloudTrail, VPC (for logs only)
- **Owner:** Finance and Security teams
- **Root email:** organization-billing@company.com
- **IAM Access:** Limited to security and operations teams
- **Workloads:** None - governance and logging only

### Production Account
- **Purpose:** Customer-facing and mission-critical workloads
- **Environment:** Production
- **Key services:** EC2, RDS, S3, CloudFront, ALB, VPC, KMS
- **Owner:** Production operations team
- **Root email:** prod-account@company.com
- **Backup Strategy:** Daily automated backups, cross-region replication
- **Cost Center:** Revenue-generating applications

### Development Account
- **Purpose:** Development and testing workloads
- **Environment:** Dev and Test combined (can separate later)
- **Key services:** EC2, RDS, S3, Lambda, VPC
- **Owner:** Development team lead
- **Root email:** dev-account@company.com
- **Backup Strategy:** Weekly backups (optional)
- **Cost Center:** Engineering or R&D

## Naming Conventions
| Resource Type | Pattern | Example |
|--------------|---------|---------|
| AWS Account Name | `{org}-{account-type}-account` | `acme-production-account` |
| AWS Account ID | (managed by AWS) | `123456789012` |
| VPC | `{org}-{account}-{env}-vpc` | `acme-prod-prod-vpc` |
| Subnet | `{org}-{account}-{tier}-subnet-{az}` | `acme-prod-public-subnet-1a` |
| Security Group | `{org}-{env}-{component}-sg` | `acme-prod-web-sg` |
| IAM Role | `{org}-{account}-{service}-role` | `acme-prod-lambda-role` |
| S3 Bucket | `{org}-{account}-{purpose}-{region}-{id}` | `acme-prod-data-us-east-1-logs` |
| EC2 Instance | `{org}-{env}-{component}-{num}` | `acme-prod-web-001` |
| RDS Instance | `{org}-{env}-{db-type}-{num}` | `acme-prod-mysql-001` |
| Cross-Account Role | `{source}-{dest}-role` | `dev-prod-deploy-role` |

## Tagging Strategy

### Required Tags (All Resources)
- `Environment`: prod, dev, test, staging
- `Account`: account-name (production, development, etc.)
- `Owner`: team-name or person-email
- `CostCenter`: cost-center-id
- `Project`: project-name
- `Application`: application-name or workload-id
- `CreatedDate`: YYYY-MM-DD
- `BackupPolicy`: daily, weekly, never
- `ManagedBy`: terraform, manual, cloudformation
- `DataClassification`: public, internal, confidential, restricted

### Cost Allocation Tags
Tag all resources for cost allocation:
- `Environment`: For environment-based chargeback
- `CostCenter`: For organizational unit chargeback
- `Team`: For team-based tracking
- `Project`: For project-based tracking

**Example Tag Set:**
```json
{
  "Environment": "prod",
  "Account": "production",
  "Owner": "platform-team",
  "CostCenter": "1001",
  "Project": "e-commerce-platform",
  "Application": "api-gateway",
  "CreatedDate": "2024-01-15",
  "BackupPolicy": "daily",
  "ManagedBy": "terraform",
  "DataClassification": "confidential"
}
```

## Security Baseline

### Service Control Policies (SCPs)
Apply SCPs to organize root to enforce baseline controls:

**Deny Unencrypted Uploads to S3:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "s3:PutObject",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    }
  ]
}
```

**Deny Root Account Usage:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "NotAction": [
        "iam:CreateVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:ListMFADevices",
        "iam:ListUsers",
        "iam:ListVirtualMFADevices",
        "iam:ResyncMFADevice",
        "sts:GetSessionToken"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    }
  ]
}
```

**Restrict EC2 Instance Types (Prod Account):**
Only allow cost-efficient instances in production.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotLike": {
          "ec2:InstanceType": ["t3.*", "m5.*", "m6.*", "c5.*", "c6.*"]
        }
      }
    }
  ]
}
```

### IAM Best Practices
- **Root Account:** Enable MFA, store credentials in vault, never use for operations
- **Admin Users:** Create via IAM Identity Center or dedicated admin role
- **Developer Access:** Use temporary STS credentials, enforce MFA
- **Cross-Account Access:** Use IAM roles with trust relationships
- **Service Roles:** Least-privilege per service (EC2, Lambda, ECS, RDS)
- **Key Rotation:** Rotate IAM access keys every 90 days

### GuardDuty Setup
- Enable in all accounts and regions
- Create aggregated findings in management account
- Set up SNS notifications for high-severity findings
- Configure automated response for known threats (optional)
- Review findings weekly by security team

### AWS Config Rules (Per Account)
Minimum set for each account:
- `root-account-mfa-enabled`
- `iam-policy-no-statements-with-admin-access`
- `rds-encryption-enabled`
- `s3-bucket-public-read-prohibited`
- `s3-bucket-public-write-prohibited`
- `cloudtrail-enabled`
- `ec2-security-group-ssh-restricted`
- `ec2-instances-in-vpc`
- `kms-key-rotation-enabled` (prod only)
- `rds-backup-enabled` (prod only)

### Logging & Auditing
- **CloudTrail:** Enable in management account for all accounts
- **VPC Flow Logs:** Enable on all subnets
- **S3 Bucket Logging:** Enable on all buckets
- **ALB/NLB Logs:** Enable for all load balancers
- **RDS Logs:** Enable enhanced monitoring

## Network Design

### VPC Strategy
- **Separate VPC per account** to ensure blast radius isolation
- **CIDR Planning:** Use /16 networks, document all ranges
- **Connectivity:** Use AWS VPN or Direct Connect for on-premises (future)

### VPC CIDR Blocks
```
Management Account:
  VPC: 10.0.0.0/16

Production Account:
  VPC: 10.1.0.0/16

Development Account:
  VPC: 10.2.0.0/16

(Reserve 10.3.0.0 - 10.255.0.0 for future accounts)
```

### Subnet Design (Per Account)
```
VPC: 10.x.0.0/16

Public Subnets (Internet Gateway, NAT):
  - 10.x.1.0/24  (AZ-1)
  - 10.x.2.0/24  (AZ-2)

Application Subnets (EC2, ECS):
  - 10.x.10.0/24 (AZ-1)
  - 10.x.11.0/24 (AZ-2)

Database Subnets (RDS):
  - 10.x.20.0/24 (AZ-1)
  - 10.x.21.0/24 (AZ-2)

(Reserve 10.x.30.0 - 10.x.254.0 for future use)
```

### DNS Strategy
- Use Route 53 hosted zone per account (private zones)
- Route 53 Resolver for hybrid DNS
- Management account owns primary Route 53 zone
- Sub-accounts reference via cross-account roles (future)

### Cross-Account Networking
- **VPN (Future):** Establish site-to-site VPN between management account and others
- **AWS VPC Peering (Not Recommended):** Creates complex mesh topology
- **Transit Gateway (Future):** Recommended for 4+ accounts

## Cost Management

### Budget Setup Per Account
- **Production Account:** Alert at 80% monthly budget
- **Development Account:** Alert at 80% monthly budget
- **Management Account:** Consolidated budget for entire organization

### Cost Allocation
Use account-level cost allocation:
```
Cost Center Mapping:
  - Management Account: Engineering (shared)
  - Production Account: Revenue (100% chargeback)
  - Development Account: Engineering (50% R&D, 50% project)
```

### Billing Approach
- **Consolidated Billing:** Management account consolidates all charges
- **AWS Cost Explorer:** Track costs by account, service, tag
- **AWS Budgets:** Set alerts per account
- **Monthly Review:** Finance and engineering review costs
- **Chargeback Model:** (Optional) Allocate dev costs to teams

### Cost Optimization
- **Production:**
  - Reserved Instances for stable workloads (30-40% discount)
  - Savings Plans for variable workloads
  - Regular cost reviews (weekly)

- **Development:**
  - Use smaller instance types (t3.small, t3.medium)
  - Schedule environments (turn off outside work hours)
  - Spot instances for batch processing
  - Automatic cleanup of old resources (30-day policy)

## Migration Path

### Scaling to Multiple Team Accounts
Evolve to team-based accounts when:
- You have 4+ independent teams
- Teams need separate budgets and cost allocation
- Teams require completely isolated environments
- You need to scale development capacity

### Path Forward
1. **Current State:** 3 accounts (management, production, development)
2. **Next Phase:** Add team-specific accounts as needed
3. **Future State:** Consider AWS Control Tower for governance automation

## Cross-Account Access

### Cross-Account Deploy Role (Dev to Prod)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": "arn:aws:iam::PROD_ACCOUNT_ID:role/deploy-role"
    }
  ]
}
```

### Deploy Role Trust Policy (In Prod Account)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::DEV_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Related Skills
- [aws-iam-identity-center](../aws-iam-identity-center) - For SSO across accounts
- [aws-vpc-networking](../aws-vpc-networking) - For multi-account network design
- [aws-security-baseline](../aws-security-baseline) - For hardening per account
- [aws-cost-optimization](../aws-cost-optimization) - For cost tracking
- [aws-terraform-infrastructure](../aws-terraform-infrastructure) - For automated provisioning
- [aws-control-tower-setup](../aws-control-tower-setup) - For future centralized governance
