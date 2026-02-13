# IAM — MVA Baseline

## Overview

AWS Identity and Access Management (IAM) controls authentication and authorisation across all AWS services. IAM is foundational infrastructure — every AWS operation requires IAM permissions.

**MNA (Minimum Needed Architecture):** An IAM entity (user, role, or federated identity) with permissions to perform the required actions.
**MVA (Minimum Viable Architecture):** Least-privilege policies, no wildcard permissions, MFA enforcement, no long-lived credentials where avoidable, governance tagging, and audit logging.

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | No wildcard actions (`Action: "*"`) in custom policies | Critical | Wildcard permissions are the most common IAM security failure |
| Security | No wildcard resources (`Resource: "*"`) without justification | Critical | Overly broad resource scope exposes unrelated resources |
| Security | No inline policies on IAM users (use groups or roles instead) | High | Inline policies on users prevent centralised management |
| Security | No root account access keys | High | Root credentials should never be used for programmatic access |
| Operational Excellence | Governance tags applied to roles and users (7 core tags) | High | Untagged IAM resources violate governance compliance |

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
| Security | Service roles follow least privilege (scoped to specific services and resources) | Medium | Even dev roles should not have broader access than needed |
| Security | Access keys rotated within 90 days | Medium | Long-lived credentials increase exposure window |
| Security | MFA enabled for all console users | Medium | Prevents credential theft from granting console access |
| Security | IAM users for human access use groups with managed policies (not direct policy attachment) | Low | Groups simplify permission management and auditing |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Permission boundaries applied to roles that create other roles | High | Prevents privilege escalation through role creation |
| Security | No long-lived credentials for application access (use STS/assume-role) | High | Applications should use temporary credentials |
| Security | IAM Access Analyzer enabled | High | Detects unintended external access to resources |
| Operational Excellence | CloudTrail logging enabled for IAM events | High | All IAM changes must be auditable |
| Operational Excellence | Credential report reviewed (no unused credentials > 90 days) | Medium | Stale credentials increase attack surface |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Service Control Policies (SCPs) for guardrails (if using Organizations) | High | SCPs provide account-level permission boundaries |
| Security | Cross-account roles use external IDs | High | Prevents confused deputy attacks |
| Security | No human IAM users for application access (use roles and federation) | High | Human credentials must not be embedded in applications |
| Security | MFA enforced for all privileged operations | High | Critical actions require second factor |
| Reliability | Break-glass procedure documented for emergency access | Medium | Must have emergency access path that doesn't rely on normal IAM |
| Operational Excellence | IAM policies deployed via IaC (CDK/Terraform/CloudFormation), not console or direct CLI | High | Production IAM must be reproducible and reviewable |
| Operational Excellence | Regular access reviews (quarterly minimum) | Medium | Permissions drift over time and must be re-validated |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | No wildcard actions | R | R | R | R | Critical |
| Security | No wildcard resources | R | R | R | R | Critical |
| Security | No inline policies on users | R | R | R | R | High |
| Security | No root access keys | R | R | R | R | High |
| Security | Service roles least privilege | - | R | R | R | Medium |
| Security | Access keys rotated (90 days) | - | R | R | R | Medium |
| Security | MFA for console users | - | R | R | R | Medium |
| Security | Users in groups (not direct policies) | - | R | R | R | Low |
| Security | Permission boundaries on role-creating roles | - | - | R | R | High |
| Security | No long-lived app credentials (use STS) | - | - | R | R | High |
| Security | IAM Access Analyzer | - | - | R | R | High |
| Security | SCPs for guardrails | - | - | - | R | High |
| Security | Cross-account external IDs | - | - | - | R | High |
| Security | No human users for app access | - | - | - | R | High |
| Security | MFA for privileged operations | - | - | - | R | High |
| Reliability | Break-glass procedure documented | - | - | - | R | Medium |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | CloudTrail for IAM events | - | - | R | R | High |
| Operational Excellence | Credential report reviewed | - | - | R | R | Medium |
| Operational Excellence | IAM via IaC | - | - | - | R | High |
| Operational Excellence | Regular access reviews | - | - | - | R | Medium |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Wildcard Actions in Policies

- **Check command:** `aws iam get-policy-version --policy-arn {policy_arn} --version-id {version_id} --query 'PolicyVersion.Document'`
- **Gap condition:** Any statement contains `"Action": "*"` or `"Action": ["*"]`
- **Severity:** Critical
- **Remediation:** Replace wildcard actions with specific service actions (e.g., `s3:GetObject`, `ec2:DescribeInstances`)
- **Remediation description:** Scopes policy to only the actions the entity actually needs

### Wildcard Resources in Policies

- **Check command:** `aws iam get-policy-version --policy-arn {policy_arn} --version-id {version_id} --query 'PolicyVersion.Document'`
- **Gap condition:** Any statement contains `"Resource": "*"` without clear justification (e.g., `sts:GetCallerIdentity` legitimately requires `*`)
- **Severity:** Critical
- **Remediation:** Replace wildcard resources with specific ARNs or ARN patterns
- **Remediation description:** Scopes policy to only the resources the entity actually needs

### Inline Policies on Users

- **Check command:** `aws iam list-user-policies --user-name {user_name}`
- **Gap condition:** Returns any inline policy names
- **Severity:** High
- **Remediation:** Create a managed policy, attach to a group, add user to the group, then `aws iam delete-user-policy --user-name {user_name} --policy-name {policy_name}`
- **Remediation description:** Migrates inline policies to managed policies on groups for centralised management

### Root Account Access Keys

- **Check command:** `aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'`
- **Gap condition:** Returns `1` (root access keys exist)
- **Severity:** High
- **Remediation:** Log in as root, navigate to Security Credentials, delete access keys
- **Remediation description:** Removes root account access keys (must be done via console as root)

### MFA for Console Users

- **Check command:** `aws iam list-users --query 'Users[*].UserName'` then for each: `aws iam list-mfa-devices --user-name {user_name}`
- **Gap condition:** Any console user has no MFA devices
- **Severity:** Medium
- **Remediation:** User must enable MFA via console or CLI (`aws iam enable-mfa-device`)
- **Remediation description:** Enables multi-factor authentication for console access

### Access Key Age

- **Check command:** `aws iam list-access-keys --user-name {user_name} --query 'AccessKeyMetadata[*].{AccessKeyId:AccessKeyId,CreateDate:CreateDate,Status:Status}'`
- **Gap condition:** Any active access key is older than 90 days
- **Severity:** Medium
- **Remediation:** Create new key, update applications, deactivate old key, delete old key
- **Remediation description:** Rotates access keys to limit exposure window from compromised credentials

### IAM Access Analyzer

- **Check command:** `aws accessanalyzer list-analyzers --query 'analyzers[*].{name:name,status:status,type:type}'`
- **Gap condition:** No active analyzer of type `ACCOUNT` (or `ORGANIZATION` for org-level)
- **Severity:** High (staging/prod)
- **Remediation:** `aws accessanalyzer create-analyzer --analyzer-name {name} --type ACCOUNT`
- **Remediation description:** Creates an IAM Access Analyzer to detect unintended external resource access

### Governance Tags

- **Check command:** `aws iam list-role-tags --role-name {role_name}` or `aws iam list-user-tags --user-name {user_name}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws iam tag-role --role-name {role_name} --tags Key=...,Value=...`
- **Remediation description:** Applies required governance tags for compliance

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- IAM is global (not regional) — policies, users, and roles exist across all regions
- Root account access should be secured with MFA and used only for account-level operations
- Prefer IAM roles over IAM users for all application and service access
- For AWS Coworker itself: discovery agents (Haiku) should use read-only IAM roles; mutation agents (Sonnet) should use scoped write roles — this is a future improvement (see blog Part 3)
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/iam.md` for CLI command reference
