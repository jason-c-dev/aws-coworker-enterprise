# Data Protection Policies

## Overview
Data protection policies enforce encryption, access controls, and compliance standards for all data stored in AWS services. These policies prevent data breaches, unauthorized access, and ensure regulatory compliance (GDPR, HIPAA, PCI-DSS, SOC2). **Enforcement Level: MANDATORY** - All data protection violations are immediately escalated to security team.

## Mandatory Rules (NEVER Violate)

### Rule: S3 Bucket Encryption Must Be Enabled
- **Severity:** CRITICAL
- **Description:** All S3 buckets must have default encryption enabled using either AWS-managed keys (SSE-S3) or customer-managed keys (SSE-KMS). Encryption must be enabled before any objects are stored.
- **Rationale:** Encryption prevents data exposure in case of unauthorized S3 access or AWS infrastructure compromise.
- **Validation:**
  - `aws s3api get-bucket-encryption --bucket <bucket-name>`
  - Verify `Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm` is set to `AES256` or `aws:kms`
  - Check all buckets: `aws s3api list-buckets --query 'Buckets[*].Name' | jq -r '.[]' | while read b; do echo "$b:"; aws s3api get-bucket-encryption --bucket $b 2>/dev/null || echo "Not configured"; done`
- **Remediation:**
  - Enable S3 encryption: `aws s3api put-bucket-encryption --bucket <bucket-name> --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'`
  - For sensitive data, use KMS: `aws s3api put-bucket-encryption --bucket <bucket-name> --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": "<key-id>"}}]}'`

### Rule: S3 Bucket Versioning and MFA Delete Must Be Enabled
- **Severity:** CRITICAL
- **Description:** All S3 buckets storing critical data must have versioning and MFA Delete enabled to prevent accidental or malicious deletion of data.
- **Rationale:** Versioning with MFA Delete protects against ransomware attacks that delete backups or critical data.
- **Validation:**
  - `aws s3api get-bucket-versioning --bucket <bucket-name>`
  - Verify `Status: Enabled` and `MFADelete: Enabled`
  - Check via AWS CLI: `aws s3api head-bucket --bucket <bucket> && echo "OK"`
- **Remediation:**
  - Enable versioning: `aws s3api put-bucket-versioning --bucket <bucket-name> --versioning-configuration Status=Enabled`
  - Enable MFA Delete: `aws s3api put-bucket-versioning --bucket <bucket-name> --versioning-configuration Status=Enabled,MFADelete=Enabled --mfa "<mfa-device-serial-number> <mfa-token-code>"`
  - Note: Requires root account credentials with MFA

### Rule: S3 Buckets Must Block Public Access
- **Severity:** CRITICAL
- **Description:** S3 Block Public Access must be enabled on all S3 buckets. All four settings (IgnorePublicAcls, BlockPublicAcls, BlockPublicPolicy, RestrictPublicBuckets) must be set to true.
- **Rationale:** Public S3 buckets are common source of data breaches and compliance violations. Automatic blocking prevents accidental public exposure.
- **Validation:**
  - `aws s3api get-public-access-block --bucket <bucket-name>`
  - Verify all settings are true:
    - BlockPublicAcls: true
    - BlockPublicPolicy: true
    - IgnorePublicAcls: true
    - RestrictPublicBuckets: true
- **Remediation:**
  - Enable Block Public Access: `aws s3api put-public-access-block --bucket <bucket-name> --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"`

### Rule: RDS Database Encryption Must Be Enabled
- **Severity:** CRITICAL
- **Description:** All RDS instances (including Aurora) must have encryption at rest enabled using either AWS-managed keys (default) or customer-managed KMS keys.
- **Rationale:** Encryption at rest protects data if storage media is accessed outside of AWS.
- **Validation:**
  - `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, StorageEncrypted]'`
  - Verify all instances show `StorageEncrypted: true`
  - Check KMS key: `aws rds describe-db-instances --db-instance-identifier <id> --query 'DBInstances[0].KmsKeyId'`
- **Remediation:**
  - Create encrypted RDS snapshot: `aws rds create-db-snapshot --db-instance-identifier <old-id> --db-snapshot-identifier <snapshot-id>`
  - Restore from snapshot with encryption: `aws rds restore-db-instance-from-db-snapshot --db-instance-identifier <new-id> --db-snapshot-identifier <snapshot-id> --storage-encrypted --kms-key-id <key-arn>`

### Rule: RDS Database Backup Encryption Must Match Instance
- **Severity:** CRITICAL
- **Description:** All RDS automated backups and manual snapshots must be encrypted using the same encryption key as the instance.
- **Rationale:** Backups are often target for attackers. Matching encryption ensures recovery data is protected.
- **Validation:**
  - `aws rds describe-db-snapshots --query 'DBSnapshots[*].[DBSnapshotIdentifier, StorageEncrypted, KmsKeyId]'`
  - Compare KMS keys between instance and snapshots
  - Check backup retention: `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, BackupRetentionPeriod]'`
- **Remediation:**
  - Enable backup encryption: `aws rds modify-db-instance --db-instance-identifier <id> --backup-retention-period 30` (if currently 0)
  - Ensure snapshots use same key as instance
  - Update auto-backup KMS key if needed via modify-db-instance

### Rule: All Data in Transit Must Use TLS 1.2 Minimum
- **Severity:** CRITICAL
- **Description:** All data transmissions must use TLS 1.2 or higher. TLS 1.0 and 1.1 are prohibited. Database connections, API calls, and application traffic must be encrypted.
- **Rationale:** TLS 1.0/1.1 have known vulnerabilities. TLS 1.2+ provides strong encryption for data in transit.
- **Validation:**
  - For RDS: `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, IamDatabaseAuthenticationEnabled]'`
  - Check SSL/TLS parameter group: `aws rds describe-db-parameter-groups --query 'DBParameterGroups[*].Parameters[?ParameterName==`ssl`]'`
  - For Elasticsearch: `aws es describe-elasticsearch-domains --query 'DomainStatusList[*].[DomainName, TLSSecurityPolicy]'`
- **Remediation:**
  - For RDS MySQL: Set `require_secure_transport` to 1 in parameter group
  - For RDS PostgreSQL: Set `rds.force_ssl` to 1 in parameter group
  - For Elasticsearch: Update domain TLS policy to TLS 1.2+
  - Enforce HTTPS for all application endpoints (ALB listener)

### Rule: EBS Volume Encryption Must Be Enabled
- **Severity:** CRITICAL
- **Description:** All EBS volumes must have encryption enabled at creation time. Encryption cannot be added to existing unencrypted volumes (requires copy).
- **Rationale:** Unencrypted volumes can be accessed if AWS account is compromised or infrastructure is physically breached.
- **Validation:**
  - `aws ec2 describe-volumes --query 'Volumes[*].[VolumeId, Encrypted, VolumeType]'`
  - Identify unencrypted volumes: `aws ec2 describe-volumes --filters Name=encrypted,Values=false --query 'Volumes[*].VolumeId'`
  - Check default encryption: `aws ec2 get-ebs-encryption-by-default`
- **Remediation:**
  - Enable default EBS encryption: `aws ec2 enable-ebs-encryption-by-default`
  - For existing unencrypted volumes: Create encrypted snapshot, restore to new encrypted volume
  - Create new instances with encrypted root volumes

### Rule: Database Backups Must Be Retained and Encrypted
- **Severity:** CRITICAL
- **Description:** All production databases must have automated backups enabled with minimum 30-day retention. Backups must be encrypted and cross-region replicated.
- **Rationale:** Backups are critical for disaster recovery and ransomware protection. Retention prevents data loss from delays in detection.
- **Validation:**
  - `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, BackupRetentionPeriod, StorageEncrypted]'`
  - Verify retention >= 30 days
  - Check backup destination: `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, PreferredBackupWindow]'`
- **Remediation:**
  - Set backup retention: `aws rds modify-db-instance --db-instance-identifier <id> --backup-retention-period 30 --apply-immediately`
  - Enable cross-region backup: `aws rds modify-db-instance --db-instance-identifier <id> --enable-copy-tags-to-snapshot --apply-immediately`

### Rule: Secrets Manager Secrets Must Have Rotation Enabled
- **Severity:** CRITICAL
- **Description:** All database credentials and API keys stored in Secrets Manager must have automatic rotation enabled with maximum 90-day rotation cycle.
- **Rationale:** Automatic rotation limits exposure window if credentials are compromised. Long-lived credentials are high-risk.
- **Validation:**
  - `aws secretsmanager list-secrets --query 'SecretList[*].[Name, RotationEnabled]'`
  - Check rotation lambda: `aws secretsmanager describe-secret --secret-id <secret> --query 'RotationRules'`
  - Verify last rotation date: `aws secretsmanager describe-secret --secret-id <secret> --query 'LastRotatedDate'`
- **Remediation:**
  - Enable rotation: `aws secretsmanager rotate-secret --secret-id <secret> --rotation-rules AutomaticallyAfterDays=30`
  - Configure rotation lambda function for custom secrets
  - Test rotation before enabling automatic rotation

### Rule: KMS Key Policies Must Be Least Privilege
- **Severity:** CRITICAL
- **Description:** KMS key policies must grant minimum required permissions. No KMS key should allow DescribeKey or GenerateDataKey from "*" principal.
- **Rationale:** Overly permissive KMS policies enable data decryption by unauthorized users.
- **Validation:**
  - `aws kms list-keys --query 'Keys[*].KeyId' | jq -r '.[]' | while read key; do echo "=== $key ==="; aws kms get-key-policy --key-id $key --policy-name default | jq '.Statement[] | select(.Principal=="*")'done`
  - Check for wildcard principals in key policy
- **Remediation:**
  - Update key policy to restrict to specific roles/users
  - Use condition statements for principal ARNs (no wildcard)
  - Example: `"Principal": {"AWS": "arn:aws:iam::ACCOUNT:role/service-role"}`

## Recommended Practices (SHOULD Follow)

### Practice: Use Customer-Managed KMS Keys for Sensitive Data
- **Severity:** HIGH
- **Description:** Sensitive data (PII, financial records, health information) should be encrypted with customer-managed KMS keys, not AWS-managed keys.
- **Rationale:** Customer-managed keys provide better audit trail and control over encryption/decryption operations.
- **Exceptions:** Non-sensitive data and development environments may use AWS-managed keys.

### Practice: Implement Field-Level Encryption
- **Severity:** HIGH
- **Description:** Highly sensitive fields (SSN, credit card numbers, medical records) should use application-level encryption in addition to database encryption.
- **Rationale:** Field-level encryption protects data even if database is compromised or accessed directly.

### Practice: Enable Access Logging for S3 and Databases
- **Severity:** HIGH
- **Description:** All S3 buckets and databases must have access logging enabled to track who accessed what data and when.
- **Rationale:** Access logs enable forensic analysis and compliance auditing.

### Practice: Implement Data Lifecycle Policies
- **Severity:** HIGH
- **Description:** S3 buckets should have lifecycle policies that transition old data to Glacier after defined periods for cost optimization and compliance.
- **Rationale:** Lifecycle policies reduce costs while maintaining compliance retention requirements.

## Environment-Specific Rules

### Production
- Encryption mandatory for all data at rest and in transit
- KMS customer-managed keys required for sensitive data
- Backup retention minimum 30 days, encrypted and cross-region replicated
- Secrets rotation required every 30 days maximum
- Access logging mandatory for all data services
- Database audit logging enabled

### Non-Production (Dev/Test)
- Encryption recommended (AWS-managed keys acceptable)
- Backup retention minimum 7 days for critical systems
- Secrets rotation required every 60 days
- Access logging not required (but recommended)
- Test data must not contain production PII

## Validation Commands

```bash
# Check S3 encryption status
aws s3api list-buckets --query 'Buckets[*].Name' | jq -r '.[]' | while read b; do
  echo "=== $b ==="; aws s3api get-bucket-encryption --bucket $b 2>&1 | grep -i "SSEAlgorithm" || echo "Not encrypted";
done

# Verify S3 Block Public Access
aws s3api get-public-access-block --bucket <bucket-name> | jq '.PublicAccessBlockConfiguration'

# Check RDS encryption
aws rds describe-db-instances --query 'DBInstances[?StorageEncrypted==false].[DBInstanceIdentifier, Engine]'

# List unencrypted EBS volumes
aws ec2 describe-volumes --filters Name=encrypted,Values=false --query 'Volumes[*].[VolumeId, Size, State]' --output table

# Check Secrets Manager rotation
aws secretsmanager list-secrets --query 'SecretList[*].[Name, RotationEnabled, LastRotatedDate]' --output table

# Verify KMS key policies
aws kms list-keys | jq -r '.Keys[].KeyId' | while read key; do
  echo "=== $key ==="; aws kms get-key-policy --key-id $key --policy-name default | jq '.Statement[] | select(.Principal=="*")';
done

# Check database backup retention
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, BackupRetentionPeriod]' --output table

# Verify TLS policy on Elasticsearch
aws es describe-elasticsearch-domains --query 'DomainStatusList[*].[DomainName, TLSSecurityPolicy]' --output table
```

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| S3 bucket not encrypted | CRITICAL | Enable encryption with SSE-S3 or SSE-KMS |
| S3 bucket not blocking public access | CRITICAL | Enable Block Public Access, check bucket policy |
| S3 bucket versioning disabled | CRITICAL | Enable versioning and MFA Delete |
| RDS not encrypted | CRITICAL | Create snapshot, restore encrypted instance |
| EBS volume not encrypted | CRITICAL | Create snapshot, restore to encrypted volume |
| Backup retention less than 30 days | CRITICAL | Modify to minimum 30-day retention |
| Database using TLS 1.1 or lower | CRITICAL | Update parameter group to require TLS 1.2+ |
| Secrets Manager rotation disabled | CRITICAL | Enable automatic rotation with 30-day cycle |
| KMS key policy allows wildcard principal | CRITICAL | Update policy to restrict to specific ARNs |
| Unencrypted snapshots | HIGH | Copy to new encrypted snapshot, delete unencrypted |
| No access logging on S3 | HIGH | Enable access logging to separate logging bucket |
| No database audit logging | HIGH | Enable database audit logs, send to CloudWatch |

## Exception Process

Data protection exceptions are exceptionally rare and require highest-level approval:

1. **Justification Document**
   - Specific business requirement for exception
   - Risk assessment indicating acceptable risk
   - Compliance implications (regulatory review required)
   - Proposed compensating controls

2. **Multi-Level Approval**
   - CISO review (required)
   - Compliance/Legal review (required for data handling)
   - CFO approval (for cost implications)
   - Executive sponsor sign-off

3. **Mandatory Controls**
   - Time-limited exception (maximum 30 days)
   - Daily confirmation exception is valid
   - Enhanced monitoring and alerting
   - Escalation procedures if conditions change

4. **Post-Exception**
   - Mandatory remediation plan with timeline
   - Weekly status updates
   - Automatic revocation if not remediated within deadline

Data protection exceptions do not auto-renew - full re-approval process required.
