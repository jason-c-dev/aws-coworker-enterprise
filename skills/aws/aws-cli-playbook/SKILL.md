---
name: aws-cli-playbook
description: Canonical AWS CLI patterns for discover, plan, deploy, validate, and rollback
version: 1.0.0
category: aws
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-executor]
tools: [Bash, Read]
---

# AWS CLI Playbook

## Purpose

This skill provides canonical AWS CLI patterns for safe, effective AWS interactions. It covers discovery, planning, deployment, validation, and rollback patterns across major AWS services.

## When to Use

- Discovering AWS resources and current state
- Planning AWS operations and changes
- Executing approved changes via CLI
- Validating changes and outcomes
- Rolling back failed or unwanted changes

## When NOT to Use

- Production changes (use IaC via CI/CD instead)
- Complex multi-resource deployments (prefer CDK/Terraform)
- One-off scripts that should be IaC

---

## Core Principles

### 1. Always Specify Profile and Region

```bash
# Always explicit - never rely on defaults
aws ec2 describe-instances \
  --profile dev-admin \
  --region us-east-1
```

### 2. Use Output Formatting

```bash
# JSON for parsing
aws ec2 describe-instances --output json

# Table for human review
aws ec2 describe-instances --output table

# Text for scripting
aws ec2 describe-instances --output text

# JMESPath queries for specific data
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

### 3. Use Dry Run When Available

```bash
# Test before execute
aws ec2 run-instances --dry-run ...
aws ec2 terminate-instances --dry-run ...
```

### 4. Capture Output for Validation

```bash
# Capture and verify
RESULT=$(aws ec2 run-instances ... --output json)
INSTANCE_ID=$(echo $RESULT | jq -r '.Instances[0].InstanceId')
echo "Created instance: $INSTANCE_ID"
```

---

## Discovery Patterns

### Identity and Access

```bash
# Who am I?
aws sts get-caller-identity --profile {profile}

# What permissions do I have? (simulate)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/myuser \
  --action-names ec2:DescribeInstances ec2:RunInstances \
  --profile {profile}

# List my roles
aws iam list-roles --profile {profile}
```

### EC2

```bash
# All instances
aws ec2 describe-instances \
  --profile {profile} \
  --region {region}

# Running instances only
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --profile {profile} \
  --region {region}

# Instances by tag
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=production" \
  --profile {profile} \
  --region {region}

# Instance summary table
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
  --output table \
  --profile {profile} \
  --region {region}
```

### VPC and Networking

```bash
# All VPCs
aws ec2 describe-vpcs \
  --profile {profile} \
  --region {region}

# Subnets with details
aws ec2 describe-subnets \
  --query 'Subnets[*].[SubnetId,VpcId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' \
  --output table \
  --profile {profile} \
  --region {region}

# Security groups
aws ec2 describe-security-groups \
  --profile {profile} \
  --region {region}

# Security groups with risky rules (0.0.0.0/0)
aws ec2 describe-security-groups \
  --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].[GroupId,GroupName,Description]' \
  --output table \
  --profile {profile} \
  --region {region}
```

### S3

```bash
# All buckets
aws s3 ls --profile {profile}

# Bucket details
aws s3api get-bucket-location --bucket {bucket} --profile {profile}
aws s3api get-bucket-versioning --bucket {bucket} --profile {profile}
aws s3api get-bucket-encryption --bucket {bucket} --profile {profile}
aws s3api get-public-access-block --bucket {bucket} --profile {profile}

# Bucket size (can be slow for large buckets)
aws s3 ls s3://{bucket} --recursive --summarize --profile {profile}
```

### RDS

```bash
# All DB instances
aws rds describe-db-instances \
  --profile {profile} \
  --region {region}

# DB instance summary
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceClass,Engine,DBInstanceStatus]' \
  --output table \
  --profile {profile} \
  --region {region}

# DB clusters (Aurora)
aws rds describe-db-clusters \
  --profile {profile} \
  --region {region}
```

### Lambda

```bash
# All functions
aws lambda list-functions \
  --profile {profile} \
  --region {region}

# Function details
aws lambda get-function \
  --function-name {function-name} \
  --profile {profile} \
  --region {region}

# Function summary
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Runtime,MemorySize,Timeout]' \
  --output table \
  --profile {profile} \
  --region {region}
```

### IAM

```bash
# All users
aws iam list-users --profile {profile}

# All roles
aws iam list-roles \
  --query 'Roles[*].[RoleName,Arn,CreateDate]' \
  --output table \
  --profile {profile}

# Role policy
aws iam list-attached-role-policies --role-name {role} --profile {profile}
aws iam list-role-policies --role-name {role} --profile {profile}
aws iam get-role-policy --role-name {role} --policy-name {policy} --profile {profile}
```

### CloudFormation

```bash
# All stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --profile {profile} \
  --region {region}

# Stack details
aws cloudformation describe-stacks \
  --stack-name {stack} \
  --profile {profile} \
  --region {region}

# Stack resources
aws cloudformation list-stack-resources \
  --stack-name {stack} \
  --profile {profile} \
  --region {region}

# Stack events (useful for debugging)
aws cloudformation describe-stack-events \
  --stack-name {stack} \
  --profile {profile} \
  --region {region}
```

---

## Safe Mutation Patterns

### EC2 Instance Management

```bash
# Start instance
aws ec2 start-instances \
  --instance-ids i-xxxxxxxxx \
  --profile {profile} \
  --region {region}

# Stop instance (data preserved)
aws ec2 stop-instances \
  --instance-ids i-xxxxxxxxx \
  --profile {profile} \
  --region {region}

# Terminate instance (DESTRUCTIVE)
aws ec2 terminate-instances \
  --instance-ids i-xxxxxxxxx \
  --profile {profile} \
  --region {region}
# WARNING: Instance and non-persistent storage deleted
```

### Security Group Rules

```bash
# Add ingress rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 10.0.0.0/8 \
  --profile {profile} \
  --region {region}

# Remove ingress rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --profile {profile} \
  --region {region}
```

### S3 Operations

```bash
# Copy file
aws s3 cp local-file.txt s3://{bucket}/path/ --profile {profile}

# Sync directory
aws s3 sync ./local-dir s3://{bucket}/path/ --profile {profile}

# Delete object (DESTRUCTIVE)
aws s3 rm s3://{bucket}/path/file.txt --profile {profile}

# Delete bucket contents (VERY DESTRUCTIVE)
aws s3 rm s3://{bucket} --recursive --profile {profile}
# WARNING: All objects deleted, cannot be undone unless versioning enabled
```

### Tags

```bash
# Add/update tags
aws ec2 create-tags \
  --resources i-xxxxxxxxx \
  --tags Key=Environment,Value=production Key=Owner,Value=platform-team \
  --profile {profile} \
  --region {region}

# Remove tags
aws ec2 delete-tags \
  --resources i-xxxxxxxxx \
  --tags Key=Temporary \
  --profile {profile} \
  --region {region}
```

---

## IaC Deployment Patterns

### CloudFormation

```bash
# Create stack
aws cloudformation create-stack \
  --stack-name {stack-name} \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --capabilities CAPABILITY_IAM \
  --tags Key=Environment,Value=dev \
  --profile {profile} \
  --region {region}

# Update stack (creates change set)
aws cloudformation create-change-set \
  --stack-name {stack-name} \
  --change-set-name {change-set-name} \
  --template-body file://template.yaml \
  --profile {profile} \
  --region {region}

# Review change set
aws cloudformation describe-change-set \
  --stack-name {stack-name} \
  --change-set-name {change-set-name} \
  --profile {profile} \
  --region {region}

# Execute change set
aws cloudformation execute-change-set \
  --stack-name {stack-name} \
  --change-set-name {change-set-name} \
  --profile {profile} \
  --region {region}

# Wait for completion
aws cloudformation wait stack-update-complete \
  --stack-name {stack-name} \
  --profile {profile} \
  --region {region}
```

### CDK

```bash
# Synthesize (preview CloudFormation)
cdk synth --profile {profile}

# Diff (show changes)
cdk diff --profile {profile}

# Deploy (with approval)
cdk deploy --profile {profile} --require-approval broadening

# Deploy specific stack
cdk deploy MyStack --profile {profile}
```

### Terraform

```bash
# Initialize
terraform init

# Plan (preview)
terraform plan -var-file={env}.tfvars -out=plan.tfplan

# Apply plan
terraform apply plan.tfplan

# Apply with auto-approve (use with caution)
terraform apply -var-file={env}.tfvars -auto-approve
```

---

## Rollback Patterns

### CloudFormation Rollback

```bash
# Automatic rollback on failure (default)
# Stack returns to previous state

# Manual rollback via update
aws cloudformation update-stack \
  --stack-name {stack-name} \
  --use-previous-template \
  --parameters ParameterKey=SomeParam,UsePreviousValue=true \
  --profile {profile} \
  --region {region}

# Delete failed stack
aws cloudformation delete-stack \
  --stack-name {stack-name} \
  --profile {profile} \
  --region {region}

# Cancel update in progress
aws cloudformation cancel-update-stack \
  --stack-name {stack-name} \
  --profile {profile} \
  --region {region}
```

### EC2 Recovery

```bash
# From snapshot (EBS)
aws ec2 create-volume \
  --snapshot-id snap-xxxxxxxxx \
  --availability-zone {az} \
  --profile {profile} \
  --region {region}

# Restore from AMI
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type {type} \
  --profile {profile} \
  --region {region}
```

### S3 Recovery

```bash
# List object versions (if versioning enabled)
aws s3api list-object-versions \
  --bucket {bucket} \
  --prefix {key} \
  --profile {profile}

# Restore previous version
aws s3api copy-object \
  --bucket {bucket} \
  --copy-source {bucket}/{key}?versionId={version-id} \
  --key {key} \
  --profile {profile}
```

---

## Related Files

Detailed service-specific commands are in:
- `commands/iam.md` - IAM patterns
- `commands/organizations.md` - Organizations patterns
- `commands/ec2.md` - EC2 patterns
- `commands/vpc.md` - VPC/networking patterns
- `commands/s3.md` - S3 patterns
- `commands/rds.md` - RDS patterns
- `commands/ecs.md` - ECS patterns
- `commands/eks.md` - EKS patterns
- `commands/lambda.md` - Lambda patterns
- `commands/cloudformation.md` - CloudFormation patterns

---

## Related Skills

- `aws-well-architected` — Architectural alignment
- `aws-governance-guardrails` — Policy compliance
- `aws-org-strategy` — Multi-account context
