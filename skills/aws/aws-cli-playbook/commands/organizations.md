# AWS Organizations CLI Reference

## Overview
AWS Organizations allows you to manage multiple AWS accounts centrally. Use these commands to create accounts, organize them into organizational units (OUs), apply Service Control Policies (SCPs), and manage consolidated billing. Essential for enterprise multi-account strategies.

## Discovery Commands (Read-Only)

```bash
# Describe the organization
aws organizations describe-organization

# List all AWS accounts in the organization
aws organizations list-accounts

# List only active accounts
aws organizations list-accounts --query 'Accounts[?Status==`ACTIVE`]'

# Get details about a specific account
aws organizations describe-account --account-id 123456789012

# List all organizational units (OUs)
aws organizations list-roots

# List all OUs under a parent
aws organizations list-organizational-units-for-parent --parent-id r-abcd

# Get details about an OU
aws organizations describe-organizational-unit --organizational-unit-id ou-abcd-12345678

# List accounts in an OU
aws organizations list-accounts-for-parent --parent-id ou-abcd-12345678

# List all policies (SCPs, tag policies, backup policies, AI opt-out policies)
aws organizations list-policies --filter SERVICE_CONTROL_POLICY

# List SCPs attached to a target
aws organizations list-policies-for-target --target-id ou-abcd-12345678 --filter SERVICE_CONTROL_POLICY

# Get a specific SCP
aws organizations describe-policy --policy-id p-abcd1234

# Get policy details and content
aws organizations describe-policy --policy-id p-abcd1234 --query 'Policy.Content' | jq .

# List parent entities of an account
aws organizations list-parents --child-id 123456789012

# Check if organization has all features enabled
aws organizations describe-organization --query 'Organization.FeatureSet'

# List create account status (for async account creation)
aws organizations list-create-account-status

# Get status of account creation request
aws organizations describe-create-account-status --create-account-request-id car-abcd1234

# List root accounts and OUs in tree format
aws organizations list-children --parent-id r-abcd --child-type ORGANIZATIONAL_UNIT
```

## Common Operations

```bash
# Create a new AWS account (asynchronous)
aws organizations create-account \
  --account-name "Production" \
  --email prod-account@example.com

# Get the account creation request ID and check status
aws organizations list-create-account-status --query 'CreateAccountStatuses[0].CreateAccountRequestId'

# Create an organizational unit
aws organizations create-organizational-unit \
  --parent-id r-abcd \
  --name "Production"

# Move an account to an OU
aws organizations move-account \
  --account-id 123456789012 \
  --source-parent-id r-abcd \
  --destination-parent-id ou-prod-12345678

# Enable AWS Organizations features
aws organizations enable-all-features

# Create a Service Control Policy
aws organizations create-policy \
  --content file://scp-policy.json \
  --description "Restrict high-risk services" \
  --name "RestrictHighRiskServices" \
  --type SERVICE_CONTROL_POLICY

# Attach an SCP to an OU
aws organizations attach-policy \
  --policy-id p-abcd1234 \
  --target-id ou-prod-12345678

# Attach an SCP to an account
aws organizations attach-policy \
  --policy-id p-abcd1234 \
  --target-id 123456789012

# List all policies of a type attached to a root
aws organizations list-policies-for-target --target-id r-abcd --filter SERVICE_CONTROL_POLICY

# Enable CloudTrail across the organization
aws organizations register-delegated-administrator \
  --account-id 123456789012 \
  --service-principal cloudtrail.amazonaws.com

# Register a delegated administrator (for AWS Config, Security Hub, etc.)
aws organizations register-delegated-administrator \
  --account-id 123456789012 \
  --service-principal config.amazonaws.com

# List delegated administrators
aws organizations list-delegated-administrators
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Create a new AWS account
aws organizations create-account \
  --account-name "Staging" \
  --email staging@example.com

# ⚠️ Close an AWS account (must be standalone member, not can be reversed after 90 days)
aws organizations close-account --account-id 123456789012

# ⚠️ Delete an organizational unit (must be empty of accounts)
aws organizations delete-organizational-unit --organizational-unit-id ou-abcd-12345678

# ⚠️ Detach an SCP from a target
aws organizations detach-policy \
  --policy-id p-abcd1234 \
  --target-id ou-prod-12345678

# ⚠️ Delete an SCP (must detach from all targets first)
aws organizations delete-policy --policy-id p-abcd1234

# ⚠️ Update an SCP
aws organizations update-policy \
  --policy-id p-abcd1234 \
  --content file://updated-policy.json \
  --description "Updated policy description"

# ⚠️ Rename an OU
aws organizations update-organizational-unit \
  --organizational-unit-id ou-abcd-12345678 \
  --name "NewName"

# ⚠️ Rename an account
aws organizations update-account \
  --account-id 123456789012 \
  --name "NewAccountName"

# ⚠️ Move account back to root (dangerous - breaks OU structure)
aws organizations move-account \
  --account-id 123456789012 \
  --source-parent-id ou-prod-12345678 \
  --destination-parent-id r-abcd

# ⚠️ Deregister delegated administrator
aws organizations deregister-delegated-administrator \
  --account-id 123456789012 \
  --service-principal config.amazonaws.com

# ⚠️ Leave an organization (for member account)
aws organizations leave-organization

# ⚠️ Remove member account from organization
aws organizations remove-account-from-organization --account-id 123456789012
```

## Best Practices

- **Account Structure**: Design OUs to match your organizational structure (environment, function, project)
- **SCPs by Layer**: Apply SCPs at root for organizational defaults, then at OUs for specific controls
- **Avoid FullAWSAccess Denial**: Don't attach SCPs that deny FullAWSAccess to production OUs without testing
- **Delegated Administrators**: Use delegated admins for centralized compliance tools (Security Hub, Config, CloudTrail)
- **Tagging Strategy**: Tag accounts and OUs to track cost center, environment, and owner
- **Account Email**: Use DL or templated emails for account creation (easier to manage than personal emails)
- **Consolidated Billing**: Use the management account for billing and cost allocation
- **CloudTrail Integration**: Enable organization CloudTrail to log API calls across all accounts
- **Avoid Account Closure**: Close accounts with caution; 90-day recovery window exists but account is unusable
- **Policy Testing**: Test SCPs in non-production OUs before applying to critical accounts
- **Regular Audits**: Review account structure and SCP attachments quarterly

## Related Skills

- IAM - Manage user and role permissions within accounts
- CloudTrail - Audit API calls across organization
- AWS Config - Monitor compliance across accounts
- Security Hub - Centralized security findings across accounts
- Cost Management - Track spending across organization
