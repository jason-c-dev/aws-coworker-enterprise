# Tagging Policies

## Overview
Tagging policies enforce consistent metadata labeling across all AWS resources to enable cost allocation, resource discovery, compliance auditing, and automated governance. Tags are critical for organizational structure, access control, and operational management. **Enforcement Level: MANDATORY** - All resources must be tagged at creation time. Guardrails will prevent resource creation without required tags.

## Mandatory Rules (NEVER Violate)

### Rule: All Resources Must Have Required Core Tags
- **Severity:** CRITICAL
- **Description:** Every AWS resource (EC2, RDS, S3, Lambda, etc.) must have the following tags at creation:
  - `Environment`: dev, test, staging, or prod
  - `Owner`: Email or team name responsible for resource
  - `CostCenter`: Cost center ID for billing allocation (format: CC-XXXXX)
  - `Application`: Application name or identifier
  - `CreatedBy`: IAM user or service that created resource
  - `CreatedDate`: ISO 8601 format (YYYY-MM-DD)
- **Rationale:** Core tags enable cost tracking, ownership clarity, compliance auditing, and automated resource management. Missing tags break cost allocation and governance automation.
- **Validation:**
  - `aws resourcegroupstaggingapi list-resources --query 'ResourceTagMappingList[?Tags[?Key==`Environment`].Value] | .[0]'`
  - Check each resource for required tags: `aws ec2 describe-instances --query 'Reservations[*].Instances[*].{ID:InstanceId, Tags:Tags[*].{Key:Key,Value:Value}}'`
  - Use tag compliance script to identify missing tags (see Common Violations section)
- **Remediation:**
  - Tag existing resource: `aws ec2 create-tags --resources <resource-id> --tags Key=Environment,Value=prod Key=Owner,Value=admin@company.com`
  - Batch tag resources: `aws resourcegroupstaggingapi tag-resource --resource-arn-list <arn-list> --tags Environment=prod`
  - Implement tag enforcement in Terraform/CloudFormation templates

### Rule: Tag Values Must Match Allowed Values
- **Severity:** CRITICAL
- **Description:** Tags must use predefined values only. No free-form tag values allowed. Allowed values:
  - `Environment`: dev, test, staging, prod (lowercase, no spaces)
  - `Owner`: Must be email (user@company.com) or team name (TeamName-Engineering)
  - `CostCenter`: Must match CC-XXXXX pattern where XXXXX is 5 digits
  - `Application`: Must match application registry (predefined list maintained by DevOps)
  - `CreatedBy`: IAM user name or service name (automated-deployer, jenkins-build)
  - `Confidentiality`: public, internal, confidential, restricted (if PII/sensitive data present)
- **Rationale:** Inconsistent tag values break automation, cost allocation, and compliance queries. Standardization ensures data consistency.
- **Validation:**
  - `aws ec2 describe-instances --query 'Reservations[*].Instances[*].{ID:InstanceId, Env:Tags[?Key==`Environment`].Value}'`
  - Check for tag values not in approved list
  - Query for misspelled or non-standard values: `aws resourcegroupstaggingapi list-resources --tag-filter Key=Environment | jq '.ResourceTagMappingList[*].Tags[] | select(.Value | test("^(dev|test|staging|prod)$") | not)'`
- **Remediation:**
  - Update tag with correct value: `aws ec2 create-tags --resources <resource-id> --tags Key=Environment,Value=prod`
  - Bulk update: Use AWS Resource Groups Tagging API
  - Remove non-compliant tag: `aws ec2 delete-tags --resources <resource-id> --tags Key=BadTag`

### Rule: No Empty Tag Values
- **Severity:** CRITICAL
- **Description:** All tags must have non-empty values. Tags with empty strings ("") or null values are not permitted.
- **Rationale:** Empty tag values break queries and automation that depends on tag values. Every tag should carry meaningful information.
- **Validation:**
  - Query for empty tags: `aws ec2 describe-instances --query 'Reservations[*].Instances[*].{ID:InstanceId, Tags:Tags[?Value==``]}'`
  - Check all services: `aws resourcegroupstaggingapi list-resources | jq '.ResourceTagMappingList[] | select(.Tags[] | select(.Value == ""))'`
- **Remediation:**
  - Delete empty tag: `aws ec2 delete-tags --resources <resource-id> --tags Key=<tag-key>`
  - Re-apply tag with proper value: `aws ec2 create-tags --resources <resource-id> --tags Key=<tag-key>,Value=<value>`

### Rule: CostCenter Tag Must Be Accurate
- **Severity:** CRITICAL
- **Description:** The CostCenter tag must match an active cost center in the organization's accounting system (format: CC-XXXXX). Invalid cost centers prevent proper billing allocation.
- **Rationale:** Cost allocation depends on accurate cost center tags. Invalid tags orphan costs and break chargeback processes.
- **Validation:**
  - Validate against cost center database: Query company HR/Finance system for valid cost centers
  - Check pattern: `aws ec2 describe-instances --query 'Reservations[*].Instances[*].Tags[?Key==`CostCenter`].Value[]' | grep -v "^CC-[0-9]\{5\}$"`
  - Generate cost allocation report: `aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity DAILY --filter 'Tags' --metrics BlendedCost`
- **Remediation:**
  - Verify valid cost center from Finance team
  - Update tag: `aws ec2 create-tags --resources <resource-id> --tags Key=CostCenter,Value=CC-12345`
  - Suspend billing for resources with invalid cost centers pending correction

### Rule: Confidentiality Tag Required for Data-Containing Resources
- **Severity:** CRITICAL
- **Description:** Any resource that stores, processes, or transmits data must have a Confidentiality tag indicating data sensitivity level:
  - `public`: Data publicly available, no protection needed
  - `internal`: Internal company data, basic protection (backups, encryption)
  - `confidential`: Sensitive business data, full protection (encryption, access logs, audit)
  - `restricted`: PII, PHI, payment card data, full protection + compliance controls
- **Rationale:** Confidentiality tagging enables automated enforcement of protection policies. Mislabeled data may not receive required protections.
- **Validation:**
  - Check RDS instances: `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, TagList[?Key==`Confidentiality`]]'`
  - Check S3 buckets: `aws s3api list-buckets --query 'Buckets[*].Name' | jq -r '.[]' | while read b; do echo "$b: $(aws s3api get-bucket-tagging --bucket $b 2>/dev/null | jq '.TagSet[] | select(.Key=="Confidentiality")')"; done`
  - Check if data-containing resources have tag: `aws resourcegroupstaggingapi list-resources --resource-type-filters 'rds:db' 'ec2:instance' 's3' --filters 'Key=Confidentiality,Values=' | wc -l`
- **Remediation:**
  - Determine data sensitivity: Review data classification policy
  - Apply appropriate tag: `aws ec2 create-tags --resources <resource-id> --tags Key=Confidentiality,Value=restricted`
  - For missing tags on PII systems: Classify as 'restricted' until review completed

### Rule: Environment Tag Must Match Resource Location
- **Severity:** CRITICAL
- **Description:** The Environment tag value must accurately reflect the resource's purpose:
  - Resources in development VPCs/AWS accounts must be tagged `dev`
  - Resources in staging must be tagged `staging`
  - Resources in production must be tagged `prod`
  - No mixed environments (e.g., prod resources in dev account must still be tagged `prod`)
- **Rationale:** Misaligned environment tags break operational procedures, prevent correct security policies, and complicate cost allocation.
- **Validation:**
  - Check account-specific environments: `aws ec2 describe-instances --query 'Reservations[*].Instances[*].{ID:InstanceId, Env:Tags[?Key==`Environment`].Value, Account:OwnerId}'`
  - List resources with mismatched environment: Query all resources and compare tag value to account classification
- **Remediation:**
  - Update tag to match actual environment: `aws ec2 create-tags --resources <resource-id> --tags Key=Environment,Value=prod`
  - If resource truly belongs in different environment, migrate to correct account/VPC

### Rule: Application Tag Must Match Business Application Registry
- **Severity:** CRITICAL
- **Description:** Application tag values must reference valid applications in the organization's application registry maintained by architecture/DevOps team. Unknown applications are not permitted.
- **Rationale:** Application tagging enables tracking of application dependencies, business alignment, and cost per application.
- **Validation:**
  - Maintain approved application list in `/sessions/pensive-great-shannon/mnt/aws-coworker-enterprise/skills/org/aws-governance-guardrails/config/approved-applications.json`
  - Query against approved list: `aws resourcegroupstaggingapi list-resources --query 'ResourceTagMappingList[*].Tags[?Key==`Application`].Value | unique' | sort`
  - Identify unapproved applications: Cross-reference against approved list
- **Remediation:**
  - Request new application registration if legitimate business application
  - Update tag to valid application: `aws ec2 create-tags --resources <resource-id> --tags Key=Application,Value=<approved-app>`
  - Consolidate with existing application if duplicate

## Recommended Practices (SHOULD Follow)

### Practice: Add Business Unit and Department Tags
- **Severity:** HIGH
- **Description:** Resources should be additionally tagged with BusinessUnit and Department for organizational structure:
  - `BusinessUnit`: Engineering, Sales, Marketing, Operations, etc.
  - `Department`: Specific team owning the resource
- **Rationale:** Business alignment tags enable organizational reporting and chargeback allocation.
- **Exceptions:** Shared resources may omit business-specific tags if tagged with owning team.

### Practice: Add Project Tag for Temporary Resources
- **Severity:** HIGH
- **Description:** Resources created for temporary projects or initiatives should be tagged with:
  - `Project`: Project identifier
  - `ProjectEndDate`: Target completion date (YYYY-MM-DD)
  - `ProjectManager`: Email of project lead
- **Rationale:** Project tracking enables automated cleanup and progress monitoring.

### Practice: Use Consistent Naming Convention with Tags
- **Severity:** HIGH
- **Description:** Resource names should be predictable and include key tag values (environment, application):
  - EC2: `<app>-<env>-<number>` (web-prod-01)
  - RDS: `<app>-<env>-db` (myapp-prod-db)
  - S3: `<company>-<app>-<env>-<purpose>` (company-myapp-prod-logs)
- **Rationale:** Naming conventions improve resource discovery and reduce tagging dependency.

### Practice: Tag Lambda Functions and ECS Services
- **Severity:** HIGH
- **Description:** Containerized and serverless workloads must be tagged the same as EC2/RDS to enable consistent governance.
- **Rationale:** Gaps in tagging coverage for modern services break compliance and cost allocation.

### Practice: Implement Auto-Tagging for Certain Resources
- **Severity:** HIGH
- **Description:** Use event-based rules (EventBridge) to automatically apply tags when resources are created:
  - Set `CreatedBy` and `CreatedDate` automatically via Lambda
  - Enforce Environment tag based on account/VPC
- **Rationale:** Automation reduces manual tagging errors and ensures 100% compliance at creation time.

## Environment-Specific Rules

### Production
- All core tags MANDATORY at creation
- Confidentiality tag REQUIRED for all resources
- CostCenter tag REQUIRED (must match Finance system)
- Environment tag MUST be "prod" (no exceptions)
- Application tag MUST be in approved registry
- Owner tag MUST be email (team@company.com)
- Monthly tag compliance audit required
- Non-compliant resources may be stopped/terminated

### Non-Production (Dev/Test)
- All core tags REQUIRED at creation
- Confidentiality tag RECOMMENDED (default to "internal")
- CostCenter tag REQUIRED (same as production)
- Environment tag MUST be "dev" or "test"
- Owner tag REQUIRED but may be individual developer
- Quarterly tag compliance review
- Non-compliant resources may be stopped after warning period

## Validation Commands

```bash
# Find resources missing required tags
aws resourcegroupstaggingapi list-resources \
  --query 'ResourceTagMappingList[?Tags[?Key==`Environment`].Value | length(@) == `0`].[ResourceARN]' \
  --output table

# List all tag keys and values in use
aws resourcegroupstaggingapi list-resources \
  --query 'ResourceTagMappingList[*].Tags[*].[Key, Value]' | jq -r '.[][]' | sort | uniq -c

# Check for resources with empty tag values
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].{ID:InstanceId, Tags:Tags[?Value==``]}' \
  --output table

# Find resources with non-standard Environment values
aws resourcegroupstaggingapi list-resources \
  --filter-list 'Key=tag:Environment' \
  --query 'ResourceTagMappingList[*].{ARN:ResourceARN, Env:Tags[?Key==`Environment`].Value[0]}' \
  --output table

# Generate cost by cost center (requires Cost Explorer)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter 'Tags:{Key:{Values:[CostCenter]}}' \
  --group-by Type=TAG,Key=CostCenter

# Audit Application tags against approved list
aws resourcegroupstaggingapi list-resources \
  --filter-list 'Key=tag:Application' \
  --query 'ResourceTagMappingList[*].Tags[?Key==`Application`].Value[]' | jq -s 'unique[]' | sort

# Find recently created resources (past 24 hours)
aws resourcegroupstaggingapi list-resources \
  --filter-list 'Key=tag:CreatedDate,Values=[2024-01-30]' \
  --query 'ResourceTagMappingList[*].[ResourceARN, Tags]' \
  --output table

# Check Confidentiality tag on sensitive resources
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier, TagList[?Key==`Confidentiality`].Value[0]]' \
  --output table
```

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Missing Environment tag | CRITICAL | Apply correct tag (dev/test/staging/prod) |
| Missing Owner tag | CRITICAL | Identify owner and apply email tag |
| Missing CostCenter tag | CRITICAL | Verify cost center with Finance, apply CC-XXXXX |
| Invalid CostCenter format | CRITICAL | Correct to CC-XXXXX pattern, verify with Finance |
| Empty tag value | CRITICAL | Delete empty tag and reapply with value |
| Environment tag doesn't match account | CRITICAL | Update tag or migrate resource to correct account |
| Non-standard Environment value (e.g., "production" instead of "prod") | CRITICAL | Standardize to approved value |
| Missing Confidentiality tag on database | CRITICAL | Classify data sensitivity, apply tag |
| Confidentiality tag incorrect for data type | CRITICAL | Review data classification, update to correct level |
| Application tag not in registry | CRITICAL | Register application or update to valid app name |
| CreatedBy missing or invalid | HIGH | Update with actual creator or service name |
| CreatedDate missing or invalid format | HIGH | Update with ISO 8601 format (YYYY-MM-DD) |
| BusinessUnit tag missing | HIGH | Add organizational structure tag for chargeback |
| ProjectEndDate in past (completed projects) | HIGH | Archive resources or remove Project tags |
| Resource name doesn't match tag values | HIGH | Rename resource to match or update tags |

## Exception Process

Tag policy exceptions are granted only for temporary situations:

1. **Justification Document**
   - Business requirement for tag value deviation
   - Timeline for remediation to compliance
   - Compensating controls (manual tracking, separate billing, etc.)
   - Stakeholder approval (owner, cost center manager)

2. **Approval**
   - DevOps/Architecture team review
   - Finance team approval (if cost center impact)
   - Maximum duration: 30 days (auto-expiration)

3. **Tracking**
   - Non-compliant resource tagged with `ExceptionEndDate`
   - Daily monitoring to ensure not forgotten
   - Escalation if approaching deadline without remediation plan
   - Automatic notification 7 days before expiration

4. **Resolution**
   - Resource must be brought into compliance or decommissioned
   - Exception cannot be renewed - full reapproval required
   - Cost impact of exception tracked separately for reporting

## Tag Governance Automation

### CloudFormation Template Example
```yaml
Resources:
  MyEC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      Tags:
        - Key: Environment
          Value: prod
        - Key: Owner
          Value: admin@company.com
        - Key: CostCenter
          Value: CC-12345
        - Key: Application
          Value: web-service
        - Key: CreatedBy
          Value: terraform-automation
        - Key: CreatedDate
          Value: !Sub '${AWS::StackName}'
        - Key: Confidentiality
          Value: internal
```

### Terraform Module Example
```hcl
locals {
  common_tags = {
    Environment  = var.environment
    Owner        = var.owner_email
    CostCenter   = var.cost_center
    Application  = var.application_name
    CreatedBy    = "terraform"
    CreatedDate  = formatdate("YYYY-MM-DD", timestamp())
    Confidentiality = var.data_classification
  }
}

resource "aws_instance" "example" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"
  tags          = merge(local.common_tags, { Name = "${var.application_name}-${var.environment}" })
}
```
