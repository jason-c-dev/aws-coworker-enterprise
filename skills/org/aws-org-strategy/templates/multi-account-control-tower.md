# Multi-Account Control Tower Strategy

## When to Use
This strategy is ideal for:
- Enterprise organizations with 10+ AWS accounts
- Organizations with strict compliance and security requirements
- Teams wanting automated account provisioning and governance
- Companies needing centralized logging and security monitoring
- Organizations requiring pre-built guardrails and best practices

**Advantages:**
- Fully automated account creation and setup
- Pre-built guardrails (mandatory and elective)
- Centralized logging and security monitoring
- Automated compliance checking via Config and Security Hub
- Self-service account provisioning via Account Factory
- Dashboard for multi-account security posture
- Built-in landing zone with best practices
- Reduced manual configuration and human error

**Limitations:**
- Higher operational cost (Control Tower management overhead)
- Less flexibility for non-standard configurations
- Requires upfront investment in setup and training
- Guardrails may conflict with custom configurations
- Limited customization of core landing zone components

## Architecture Overview
```
┌────────────────────────────────────────────────────────────┐
│         AWS Control Tower Landing Zone                     │
│  (Automated governance and account management)             │
└────────────────────────────────────────────────────────────┘
         │
    ┌────┴─────┬──────────────┬──────────────┬──────────────┐
    │           │              │              │              │
┌───▼───┐  ┌───▼─────┐  ┌───▼─────┐  ┌───▼──────┐  ┌───▼──────┐
│  Mgmt │  │  Audit  │  │  Log    │  │  Prod    │  │  Dev     │
│       │  │ Account │  │ Account │  │ Account  │  │ Account  │
└───────┘  └─────────┘  └─────────┘  └──────────┘  └──────────┘
    │          │            │            │            │
Billing    Compliance   CloudTrail   Workloads    Workloads
Config     Review       Config       Applications Testing
SSO        AWS          GuardDuty    Production   Dev/Staging
Org        Config       Security Hub  RDS, EC2    Ephemeral
API        SecurityHub  VPC Logs      ALB         Resources

Guardrails Applied Across All Accounts:
  ├─ Mandatory (always enabled)
  │   ├─ Disallow Policy Changes to Logging
  │   ├─ Disallow Bucket Policy Changes
  │   ├─ Disallow Changes to CloudTrail
  │   └─ Detect CloudTrail Deactivation
  ├─ Strongly Recommended (enabled)
  │   ├─ Disallow Amazon VPC Flow Logs Disablement
  │   ├─ Disallow Deletion of Log Group
  │   ├─ Require MFA
  │   └─ Enable CloudTrail in All AWS Regions
  └─ Elective (choose as needed)
      ├─ Restrict EC2 Instance Types
      ├─ Restrict EBS Volume Types
      ├─ Disallow Public S3 Bucket Access
      └─ Require IMDSv2 on EC2
```

## Account Structure

### Management Account (Control Tower Master)
- **Purpose:** Control Tower administration, AWS Organizations, consolidated billing
- **Environment:** Production-grade security
- **Key services:** AWS Control Tower, Organizations, Billing, CloudFormation (landing zone)
- **Owner:** Cloud governance and security teams
- **Root email:** control-tower-management@company.com
- **Special Role:** All Control Tower administration happens here
- **VPC:** Shared VPC only for aggregated logging and monitoring

### Audit Account
- **Purpose:** Compliance auditing, security review, log aggregation
- **Environment:** Restricted production access
- **Key services:** AWS Config, Security Hub, CloudTrail logs (aggregated), GuardDuty findings
- **Owner:** Security and compliance teams
- **Root email:** audit-account@company.com
- **Access Level:** Read-only to other accounts via cross-account roles
- **Workloads:** None - security monitoring only

### Log Archive Account
- **Purpose:** Centralized logging and compliance log retention
- **Environment:** Write-once, immutable logs
- **Key services:** S3 (CloudTrail, VPC logs, ALB logs), CloudWatch Logs aggregation
- **Owner:** Security and operations teams
- **Root email:** log-archive@company.com
- **Data Retention:** 7 years (compliance requirement)
- **Access Level:** Highly restricted, audit trail enabled
- **S3 Policies:** MFA delete, versioning, access logging enabled

### Production Account(s)
- **Purpose:** Customer-facing and mission-critical workloads
- **Environment:** Production
- **Key services:** EC2, RDS, S3, CloudFront, ALB, Lambda, ECS, Kinesis
- **Owner:** Production operations team
- **Root email:** prod-account-N@company.com
- **Account Count:** One or more (scale as business grows)
- **Guardrails:** Mandatory + strongly recommended + selective elective
- **Cost Center:** Revenue-generating applications

### Development Account(s)
- **Purpose:** Development, testing, and staging environments
- **Environment:** Non-production
- **Key services:** EC2, RDS, S3, Lambda, VPC
- **Owner:** Development team leads
- **Root email:** dev-account-N@company.com
- **Account Count:** One per team or shared by 2-3 teams
- **Guardrails:** Mandatory + strongly recommended (relaxed elective)
- **Ephemeral Resources:** Automatic cleanup of unused resources

### Team-Specific Accounts (Optional)
- **Purpose:** Isolated environments per team (as organization scales)
- **Environment:** Team-specific, typically non-production
- **Owner:** Individual team leads
- **Created via:** Account Factory (self-service)
- **Guardrails:** Inherited from OU policies
- **Cost Allocation:** Team-specific cost center

## Naming Conventions
| Resource Type | Pattern | Example |
|--------------|---------|---------|
| AWS Account | `{org}-{purpose}-account` | `acme-prod-account-01` |
| OU (Organization Unit) | `{org}-{tier}-ou` | `acme-production-ou` |
| VPC | `{org}-{account}-{env}-vpc` | `acme-prod-01-prod-vpc` |
| Subnet | `{org}-{az}-{tier}-subnet` | `acme-1a-public-subnet` |
| Security Group | `{org}-{env}-{component}-sg` | `acme-prod-web-sg` |
| IAM Role | `{org}-{purpose}-role` | `acme-prod-deploy-role` |
| Config Rule | `{org}-{control}-rule` | `acme-disallow-public-s3` |
| Guardrail | `{org}-{guardrail-name}` | `acme-require-mfa` |
| S3 Bucket | `{org}-{account}-{purpose}-{region}` | `acme-logs-us-east-1-archive` |
| Nested Account | `{org}-{ou}-{env}-{team}` | `acme-platform-prod-api` |

## Tagging Strategy

### Required Control Tower Tags
Control Tower applies these system tags automatically:
- `aws:cloudformation:stack-name`: Stack managing resource
- `aws:cloudformation:stack-id`: Stack ID
- `aws:cloudformation:logical-id`: Logical ID in template
- `aws:OrganizationalUnit`: OU path

### Required Business Tags (All Resources)
Enforce via SCPs and IAM policies:
- `Environment`: prod, staging, dev, test
- `Account`: account-name or number
- `Owner`: team-name or email
- `CostCenter`: cost-center-id (for chargeback)
- `Project`: project-name
- `Application`: application-name
- `CreatedDate`: YYYY-MM-DD
- `BackupPolicy`: daily, weekly, never
- `ManagedBy`: terraform, cloudformation, manual
- `DataClassification`: public, internal, confidential, restricted
- `Compliance`: yes/no (for compliance tracking)
- `CostAllocation`: team, project, or cost center

**Tag Enforcement Example:**
```json
{
  "Environment": "prod",
  "Account": "production-01",
  "Owner": "platform-team",
  "CostCenter": "1001",
  "Project": "ecommerce-platform",
  "Application": "order-service",
  "CreatedDate": "2024-01-15",
  "BackupPolicy": "daily",
  "ManagedBy": "terraform",
  "DataClassification": "confidential",
  "Compliance": "yes"
}
```

## Security Baseline

### Mandatory Guardrails (Always Enabled)
These cannot be disabled and apply to all accounts:

1. **Disallow Policy Changes to CloudTrail Bucket**
   - Prevents accidental or malicious deletion of logs

2. **Disallow Bucket Policy Changes**
   - Protects critical S3 buckets from unauthorized access

3. **Disallow CloudTrail Deactivation**
   - Ensures audit trail is never disabled

4. **Disallow Changes to Logging Configuration**
   - Locks down logging settings in all accounts

### Strongly Recommended Guardrails (Enabled by Default)
Enable in Control Tower to improve security posture:

1. **Detect CloudTrail Deactivation** - Alerts on logging disablement
2. **Disallow Amazon VPC Flow Logs Disablement** - Locks VPC logging
3. **Disallow Deletion of Log Group** - Protects CloudWatch Logs
4. **Require MFA for Console Access** - Enforces MFA on human users
5. **Enable AWS CloudTrail in All Regions** - Global audit trail

### Elective Guardrails (Choose Based on Needs)
Enable specific guardrails for your organization:

**Production OU:**
- Restrict EC2 Instance Types (cost control)
- Restrict Unencrypted Object Uploads to S3
- Disallow Public S3 Bucket Access
- Require IMDSv2 on EC2 Instances
- Require EBS Encryption
- Disallow Deletion of CloudWatch Logs

**Development OU:**
- Restrict EBS Volume Types (cost control)
- (Fewer restrictions for developer agility)

### Service Control Policies (SCPs)
Control Tower manages SCPs automatically. Add custom SCPs to OUs:

**Example: Restrict AWS Regions**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "organizations:*",
        "sts:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2",
            "eu-west-1"
          ]
        }
      }
    }
  ]
}
```

### Centralized Security Monitoring

**AWS Security Hub:**
- Aggregates findings from GuardDuty, Config, Inspector
- Centralized in Audit account
- Cross-account findings enabled
- Standard (AWS Foundational Security) enabled
- PCI DSS and CIS benchmarks enabled

**GuardDuty:**
- Enabled in all accounts
- Findings aggregated to Audit account
- Auto-remediation for common threats (optional)
- Malware Protection enabled (optional)

**AWS Config:**
- Enabled in all accounts
- Aggregated in Audit account
- Config Rules per guardrail
- Configuration history retention: 1 year

### IAM Identity Center Integration
- Centralized user and group management
- SSO across all accounts
- Permission sets per role type
- MFA enforcement for all users

### Logging & Auditing
- **CloudTrail:** Management account aggregates for all accounts
- **VPC Flow Logs:** Sent to Log Archive account
- **Application Logs:** CloudWatch Logs to centralized group
- **S3 Access Logs:** Bucket logging enabled on all buckets
- **Log Retention:** Production 2 years, Dev/Test 90 days

## Network Design

### Landing Zone Network Architecture
```
Control Tower creates:
  - Shared VPC in management account (for logs)
  - VPC in each account deployed by Account Factory

CIDR Planning (enterprise-ready):
  Management Account:    10.0.0.0/16
  Audit Account:         10.1.0.0/16
  Log Archive Account:   10.2.0.0/16

  Production Accounts:   10.100.0.0 - 10.149.0.0 (/16 each)
  Development Accounts:  10.200.0.0 - 10.249.0.0 (/16 each)

  Reserved:              10.250.0.0 - 10.255.0.0
```

### Subnet Design Per Account
```
VPC: 10.x.0.0/16

Public Subnets:
  - 10.x.1.0/24   (us-east-1a) - ALB, NAT
  - 10.x.2.0/24   (us-east-1b) - ALB, NAT
  - 10.x.3.0/24   (us-east-1c) - ALB, NAT

Application Subnets:
  - 10.x.10.0/24  (us-east-1a)
  - 10.x.11.0/24  (us-east-1b)
  - 10.x.12.0/24  (us-east-1c)

Database Subnets:
  - 10.x.20.0/24  (us-east-1a)
  - 10.x.21.0/24  (us-east-1b)
  - 10.x.22.0/24  (us-east-1c)
```

### Hybrid Connectivity (Future)
- AWS Direct Connect for on-premises connectivity
- Transit Gateway in management account
- Hub-and-spoke topology with each account as spoke
- ExpressRoute/VPN for disaster recovery

### DNS Strategy
- Route 53 in management account owns primary domain
- Route 53 Resolver for hybrid DNS resolution
- Private hosted zones per account
- Cross-account zone delegation (future)

## Cost Management

### Budget Strategy By Account Type
- **Management:** Shared cost (operations)
- **Audit:** Shared cost (compliance)
- **Log Archive:** Shared cost (infrastructure)
- **Production:** Revenue chargeback (100%)
- **Development:** Shared engineering cost or team chargeback

### Cost Allocation via Tags
Use these tags for cost allocation and reporting:
- `CostCenter`: For organizational unit billing
- `Team`: For team-level tracking
- `Project`: For project-level tracking
- `Environment`: For environment separation

### AWS Cost Explorer Reports
Create custom reports:
- Costs by account and tag
- Costs by service per team
- Spend trends over time
- Budget vs. actual costs

### Billing Approach
- **Consolidated Billing:** Aggregated in management account
- **Cost Anomaly Detection:** Automated alerts for unusual spending
- **Savings Plans:** Purchase for predictable production workloads
- **Reserved Instances:** Prod accounts (30-40% discount)
- **Spot Instances:** Dev/test accounts for batch jobs

### Cost Optimization Practices
- Quarterly cost reviews by finance and engineering
- Automatic cleanup of dev resources (30+ days unused)
- Instance right-sizing recommendations from Compute Optimizer
- Lambda power tuning for cost and performance
- Reserved capacity for databases in production

## Organizational Unit (OU) Structure

### Recommended OU Hierarchy
```
Root
├── Security OU
│   ├── Management Account
│   ├── Audit Account
│   └── Log Archive Account
├── Production OU
│   ├── Production Account 01
│   ├── Production Account 02
│   └── Production Account 03 (future)
├── Development OU
│   ├── Development Account
│   ├── Staging Account
│   └── Team Accounts (created via Account Factory)
└── Quarantine OU (suspended accounts, future)
```

### OU Policies

**Security OU:**
- All guardrails mandatory + strongly recommended
- Restrict access to non-security personnel
- Enhanced logging requirements

**Production OU:**
- Mandatory + strongly recommended guardrails
- Restrict instance types to cost-optimized options
- Require encryption for all data
- Restrict regions to approved list

**Development OU:**
- Mandatory + most strongly recommended
- Allow broader instance type selection
- Relaxed encryption requirements (optional)
- Allow Spot instances for cost savings

## Account Factory

### Self-Service Account Provisioning
Enable teams to request new accounts via Account Factory:

**Account Factory Parameters:**
```
- Account Name: (required)
- Account Email: (required, must be unique)
- Organizational Unit: (dropdown, pre-selected)
- Name for IAM Role: (default: AWSControlTowerExecution)
```

**Process:**
1. Team lead requests account via Service Catalog
2. Account Factory provisions account with landing zone
3. Guardrails apply automatically
4. Team notified when ready (15-20 minutes)
5. Team assumes role via SSO

## Migration Path

### Deploying Control Tower
1. **Preparation:**
   - Review current account structure
   - Plan OU hierarchy
   - Identify guardrails needed
   - Plan tagging strategy

2. **Deployment:**
   - Enable Control Tower on management account
   - Confirm landing zone setup
   - Deploy Account Factory
   - Integrate IAM Identity Center

3. **Migration of Existing Accounts:**
   - Register existing accounts to Control Tower
   - Apply guardrails incrementally
   - Monitor for conflicts
   - Complete in 2-4 weeks per account

4. **Optimization:**
   - Enable Security Hub
   - Configure CIS/PCI benchmarks
   - Implement automated remediation
   - Establish operational runbooks

### Scaling from Basic Multi-Account
If upgrading from basic multi-account:
1. Enable Control Tower on existing management account
2. Register production and development accounts
3. Create audit and log accounts
4. Migrate logging to new log account
5. Enable guardrails gradually to avoid conflicts
6. Decommission manual security checks

## Related Skills
- [aws-control-tower-setup](../aws-control-tower-setup) - Detailed Control Tower deployment
- [aws-iam-identity-center](../aws-iam-identity-center) - SSO and federated access
- [aws-security-hub-config](../aws-security-hub-config) - Compliance monitoring
- [aws-vpc-networking](../aws-vpc-networking) - Multi-account network design
- [aws-cost-optimization](../aws-cost-optimization) - Cost tracking and optimization
- [aws-terraform-infrastructure](../aws-terraform-infrastructure) - IaC for account provisioning
- [aws-account-factory-automation](../aws-account-factory-automation) - Self-service provisioning
