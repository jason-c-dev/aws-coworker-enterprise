# IAM Policies

## Overview
IAM governance policies establish mandatory identity and access management controls across all AWS accounts and environments. These policies are enforced at the organization level and prevent unauthorized access, privilege escalation, and credential exposure. **Enforcement Level: MANDATORY** - All violations must be remediated immediately.

## Mandatory Rules (NEVER Violate)

### Rule: No Root Account Access Key Creation
- **Severity:** CRITICAL
- **Description:** Root account access keys must never be created or used. All administrative access must be through federated identity or IAM users with MFA.
- **Rationale:** Root access keys cannot be rotated without account compromise and represent the highest privilege level. Their exposure compromises the entire AWS account.
- **Validation:**
  - `aws iam get-credential-report | grep -i "root" | grep "true" | grep "access_key"`
  - Check CloudTrail for any root account API calls
  - Verify MFA is enabled on root account
- **Remediation:**
  - Immediately delete any discovered root access keys from AWS Management Console
  - Enable root account MFA
  - Create IAM user for administrative tasks with appropriate policies

### Rule: Enforce MFA for All IAM Users
- **Severity:** CRITICAL
- **Description:** Every IAM user with AWS Management Console or programmatic access must have MFA enabled. Hardware MFA devices are preferred for administrative users.
- **Rationale:** MFA prevents credential-based attacks. Passwords alone are insufficient for security-sensitive environments.
- **Validation:**
  - `aws iam get-credential-report --query 'Content' --output text | base64 -d | grep -v "true.*true"`
  - Verify MFA device ARN is configured for all users: `aws iam list-mfa-devices --user-name <username>`
  - Check root account: `aws iam get-account-summary | grep MFADevices`
- **Remediation:**
  - Enable virtual MFA device: `aws iam enable-mfa-device --user-name <user> --serial-number <mfa-device-arn> --authentication-code1 <code1> --authentication-code2 <code2>`
  - For console access, enforce MFA in IAM policies
  - Provide user with MFA setup instructions and device

### Rule: No Inline Policies - Use Managed Policies Only
- **Severity:** CRITICAL
- **Description:** IAM roles and users must use AWS managed or customer-managed policies exclusively. Inline policies are prohibited.
- **Rationale:** Managed policies enable version control, reusability, auditing, and easier remediation. Inline policies are difficult to audit across the organization.
- **Validation:**
  - `aws iam list-role-policies --role-name <role-name>` (should return empty)
  - `aws iam list-user-policies --user-name <user>` (should return empty)
  - `aws iam list-group-policies --group-name <group>` (should return empty)
- **Remediation:**
  - Create equivalent customer-managed policy
  - Attach managed policy to role/user/group
  - Remove inline policy: `aws iam delete-role-policy --role-name <role> --policy-name <policy>`

### Rule: No Overly Permissive IAM Policies
- **Severity:** CRITICAL
- **Description:** IAM policies must never grant full resource access using wildcards ("*") or provide full service access. All policies must follow the principle of least privilege with specific resource ARNs.
- **Rationale:** Overly permissive policies increase blast radius of credential compromise and enable unauthorized actions.
- **Validation:**
  - Check for policies with `"Action": "*"`: `aws iam get-role-policy --role-name <role> --policy-name <policy> | grep -i '"Action".*"\*"'`
  - Check for policies with `"Resource": "*"` + unrestricted actions
  - Use AWS Access Analyzer to identify public access: `aws accessanalyzer validate-policy`
- **Remediation:**
  - Review and restrict Action statements to specific services
  - Scope Resource to specific ARNs and environments
  - Example: `"Resource": "arn:aws:s3:::company-bucket-prod/*"`
  - Remove overly broad policies

### Rule: Service Roles Must Have Trust Relationships
- **Severity:** CRITICAL
- **Description:** IAM roles for EC2, Lambda, ECS, and other services must have a trust relationship that limits which services can assume the role.
- **Rationale:** Service roles must be assumable only by their intended services. Unrestricted trust policies allow privilege escalation.
- **Validation:**
  - `aws iam get-role --role-name <role> | jq '.Role.AssumeRolePolicyDocument'`
  - Verify Principal is specific service, not "*"
  - Example valid principal: `"Principal": {"Service": "ec2.amazonaws.com"}`
- **Remediation:**
  - Update trust policy to specific service principal
  - Remove Principal "*" or Principal "AWS": "*"
  - Use condition statements for additional restrictions (account ID, external ID)

### Rule: Rotate Credentials Every 90 Days
- **Severity:** CRITICAL
- **Description:** IAM user access keys must be rotated every 90 days maximum. Console passwords must be rotated every 60 days.
- **Rationale:** Regular rotation limits the window of exposure if credentials are compromised.
- **Validation:**
  - `aws iam get-credential-report` and check AccessKey1Active/AccessKey2Active dates
  - Compare current date against creation date for all keys
  - `aws iam get-login-profile --user-name <user>` to check password age
- **Remediation:**
  - Create new access key: `aws iam create-access-key --user-name <user>`
  - Delete old key after verification of new key: `aws iam delete-access-key --user-name <user> --access-key-id <old-key-id>`
  - Force password change: `aws iam update-login-profile --user-name <user>`

## Recommended Practices (SHOULD Follow)

### Practice: Use IAM Roles Instead of Long-Term Credentials
- **Severity:** HIGH
- **Description:** EC2 instances, Lambda functions, and containers should use IAM roles with temporary security credentials instead of embedding access keys.
- **Rationale:** Temporary credentials are automatically rotated by AWS and cannot be stolen persistently.
- **Exceptions:** Service accounts that cannot assume roles (legacy applications, batch jobs without role assumption capability)

### Practice: Implement Cross-Account Access with External IDs
- **Severity:** HIGH
- **Description:** When allowing cross-account assume role access, always require an external ID in the trust policy.
- **Rationale:** External IDs prevent confused deputy problem and limit who can assume cross-account roles.
- **Example:**
```json
{
  "Principal": {
    "AWS": "arn:aws:iam::123456789012:root"
  },
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "unique-external-id-12345"
    }
  }
}
```

### Practice: Use IAM Permission Boundaries
- **Severity:** HIGH
- **Description:** Implement permission boundaries on all developer-managed roles to limit maximum privileges.
- **Rationale:** Permission boundaries provide an additional layer preventing privilege escalation.

### Practice: Enable CloudTrail for All IAM Actions
- **Severity:** HIGH
- **Description:** Monitor all IAM API calls through CloudTrail for audit and forensic analysis.
- **Rationale:** Complete audit trail enables detection of suspicious activity and compliance verification.

## Environment-Specific Rules

### Production
- MFA is REQUIRED for all console access (no exceptions)
- All service roles must use least-privilege policies with explicit resource ARNs
- Access keys must not be shared between environments
- Cross-account access requires external ID and explicit approval
- Root account must have no access keys and MFA enabled

### Non-Production (Dev/Test)
- MFA is REQUIRED but virtual MFA is acceptable
- Service roles may have broader permissions for development flexibility
- Temporary access keys allowed for development (must rotate every 30 days)
- Cross-account access allowed with documented justification

## Validation Commands

```bash
# Check for root access keys
aws iam get-credential-report | grep -i "root"

# List all users and MFA status
aws iam get-credential-report | awk -F',' '{print $1, $4, $9}'

# Find inline policies
aws iam list-roles --query 'Roles[*].RoleName' | jq -r '.[]' | while read role; do
  echo "=== $role ==="; aws iam list-role-policies --role-name $role;
done

# Validate IAM policy for least privilege
aws accessanalyzer validate-policy --policy-document file://policy.json --policy-type IDENTITY_POLICY

# Check access key age
aws iam get-credential-report | awk -F',' '{print $1, $9, $14}' | column -t

# Find overly permissive policies
aws iam list-policies --scope Local --query 'Policies[*].[PolicyName, Arn]' | jq -r '.[] | "\(.[1])"' | while read arn; do
  aws iam get-policy-version --policy-arn $arn --version-id $(aws iam get-policy --policy-arn $arn --query 'Policy.DefaultVersionId' --output text) | grep -i '"Action".*"\*"' && echo "VIOLATION: $arn";
done
```

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| Root account access keys exist | CRITICAL | Immediately delete keys, regenerate account if compromised |
| User without MFA | CRITICAL | Enable MFA device for user before granting any access |
| Policy with `"Action": "*"` | CRITICAL | Restrict to specific actions, use policy simulator to validate |
| Policy with `"Resource": "*"` + sensitive actions | CRITICAL | Scope to specific resource ARNs |
| Inline policy on user/role/group | CRITICAL | Convert to managed policy, attach to principal |
| Access key older than 90 days | CRITICAL | Rotate immediately, delete old key |
| Service role missing trust policy | CRITICAL | Add service principal to trust relationship |
| Cross-account role without external ID | HIGH | Add external ID condition to trust policy |
| Admin role accessible to developers | HIGH | Restrict to specific users, require additional approval |
| Password never changed or old | HIGH | Force password reset, implement lifecycle policy |

## Exception Process

All exceptions to mandatory IAM rules require:

1. **Justification Document**
   - Business case for exception
   - Why policy cannot be followed
   - Compensating controls (if any)
   - Risk assessment and owner sign-off

2. **Approval Chain**
   - Security team review
   - Infrastructure team review
   - CTO approval (for CRITICAL violations)

3. **Conditions**
   - Maximum duration (typically 30 days)
   - Requirement to report progress toward compliance
   - Mandatory re-review before extension
   - Automatic remediation if not extended

4. **Compensation Controls**
   - Enhanced CloudTrail logging
   - Temporary privilege restrictions
   - Additional MFA requirements
   - Time-limited scope (specific hours/days)

Submit exception requests through AWS Control Tower governance portal with reference ID and approval ticket.
