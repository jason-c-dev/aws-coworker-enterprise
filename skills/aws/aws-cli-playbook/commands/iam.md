# IAM CLI Reference

## Overview
AWS Identity and Access Management (IAM) allows you to manage user identities, roles, policies, and permissions across AWS. Use these commands to create users, manage access keys, define roles and policies, and control who can access what resources.

## Discovery Commands (Read-Only)

```bash
# List all IAM users
aws iam list-users

# List all IAM roles
aws iam list-roles

# List all managed policies
aws iam list-policies --scope Local

# Get details about a specific user
aws iam get-user --user-name username

# List inline policies attached to a user
aws iam list-user-policies --user-name username

# List managed policies attached to a user
aws iam list-attached-user-policies --user-name username

# Get a specific policy document
aws iam get-user-policy --user-name username --policy-name policy-name

# List access keys for a user
aws iam list-access-keys --user-name username

# List groups
aws iam list-groups

# List users in a group
aws iam get-group --group-name group-name

# Get role details
aws iam get-role --role-name role-name

# List policies attached to a role
aws iam list-attached-role-policies --role-name role-name

# Get role trust policy
aws iam get-role --role-name role-name --query 'Role.AssumeRolePolicyDocument'

# List account summary (quotas and usage)
aws iam get-account-summary

# List all user tags
aws iam list-user-tags --user-name username

# Get login profile status for user
aws iam get-login-profile --user-name username
```

## Common Operations

```bash
# Create a new IAM user
aws iam create-user --user-name newuser --tags Key=Department,Value=Engineering

# Attach a managed policy to a user
aws iam attach-user-policy --user-name username --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

# Create an access key for a user
aws iam create-access-key --user-name username

# Create a new IAM role (for EC2 service)
aws iam create-role \
  --role-name my-ec2-role \
  --assume-role-policy-document file://trust-policy.json

# Attach a managed policy to a role
aws iam attach-role-policy --role-name role-name --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

# Create an instance profile (for EC2 role)
aws iam create-instance-profile --instance-profile-name my-instance-profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name my-instance-profile \
  --role-name my-ec2-role

# Create a custom inline policy
aws iam put-user-policy \
  --user-name username \
  --policy-name custom-policy \
  --policy-document file://policy.json

# Create an IAM group
aws iam create-group --group-name group-name

# Add user to group
aws iam add-user-to-group --group-name group-name --user-name username

# Update user tags
aws iam tag-user --user-name username --tags Key=Environment,Value=Production

# Enable MFA for a user (create virtual device)
aws iam enable-mfa-device \
  --user-name username \
  --serial-number arn:aws:iam::123456789012:mfa/my-mfa \
  --authentication-code1 123456 \
  --authentication-code2 234567

# List all policies affecting a user (managed + inline)
aws iam list-attached-user-policies --user-name username
aws iam list-user-policies --user-name username
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete an IAM user (must delete access keys and attached policies first)
aws iam delete-user --user-name username

# ⚠️ Delete access key
aws iam delete-access-key --user-name username --access-key-id key-id

# ⚠️ Delete login profile (removes password)
aws iam delete-login-profile --user-name username

# ⚠️ Detach a managed policy from user
aws iam detach-user-policy --user-name username --policy-arn arn:aws:iam::aws:policy/PolicyName

# ⚠️ Delete an inline policy from user
aws iam delete-user-policy --user-name username --policy-name policy-name

# ⚠️ Remove user from group
aws iam remove-user-from-group --group-name group-name --user-name username

# ⚠️ Delete a role (must delete instance profile and detach policies first)
aws iam delete-role --role-name role-name

# ⚠️ Detach policy from role
aws iam detach-role-policy --role-name role-name --policy-arn arn:aws:iam::aws:policy/PolicyName

# ⚠️ Remove role from instance profile
aws iam remove-role-from-instance-profile \
  --instance-profile-name profile-name \
  --role-name role-name

# ⚠️ Delete instance profile
aws iam delete-instance-profile --instance-profile-name profile-name

# ⚠️ Delete a group (must remove all users first)
aws iam delete-group --group-name group-name

# ⚠️ Update access key status (deactivate/activate)
aws iam update-access-key-status \
  --user-name username \
  --access-key-id key-id \
  --status Inactive

# ⚠️ Create a custom managed policy (versioned, can be attached to multiple principals)
aws iam create-policy \
  --policy-name custom-policy \
  --policy-document file://policy.json

# ⚠️ Delete a custom managed policy
aws iam delete-policy --policy-arn arn:aws:iam::123456789012:policy/custom-policy

# ⚠️ Update an inline policy
aws iam put-user-policy \
  --user-name username \
  --policy-name policy-name \
  --policy-document file://updated-policy.json

# ⚠️ Untag a user
aws iam untag-user --user-name username --tag-keys Environment Department
```

## Best Practices

- **Principle of Least Privilege**: Grant only the minimum permissions required for each user/role
- **Use Roles for EC2**: Attach roles to EC2 instances instead of storing credentials
- **MFA for Console Users**: Enable MFA for all users with AWS Management Console access
- **Rotate Access Keys**: Regularly rotate access keys (at least every 90 days)
- **Use Groups**: Manage permissions through groups rather than per-user policies
- **Tag Resources**: Use tags to organize users and track department/cost center
- **Monitor Access**: Regularly review IAM Access Analyzer findings and CloudTrail logs
- **Avoid Root Account**: Never use root account for daily operations; create IAM users instead
- **Use Managed Policies**: Prefer AWS managed policies and versioned custom policies over inline policies
- **Service Roles**: Use service roles for applications to assume temporary credentials

## Related Skills

- AWS Organizations - Manage multiple AWS accounts
- EC2 Instance Management - Attach IAM roles to instances
- Lambda Execution - Grant permissions to Lambda functions
- S3 Bucket Policies - Control access to S3 resources
- CloudFormation - Infrastructure as code with IAM resources
