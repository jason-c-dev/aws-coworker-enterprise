# CloudFormation CLI Reference

## Overview
AWS CloudFormation is an infrastructure as code service that models and provisions AWS resources. Use these commands to create and manage stacks, create and execute change sets, manage stack policies, monitor stack events, and perform stack operations like rollbacks and updates.

## Discovery Commands (Read-Only)

```bash
# List all stacks
aws cloudformation list-stacks

# List active stacks only
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get stack details
aws cloudformation describe-stacks --stack-name my-stack

# Get specific stack information
aws cloudformation describe-stacks --stack-name my-stack --query 'Stacks[0].StackStatus'

# List stack resources
aws cloudformation list-stack-resources --stack-name my-stack

# Get details about a specific resource in stack
aws cloudformation describe-stack-resources --stack-name my-stack --logical-resource-id MyResource

# Get stack events (creation/update history)
aws cloudformation describe-stack-events --stack-name my-stack

# Describe stack resource details
aws cloudformation describe-stack-resource \
  --stack-name my-stack \
  --logical-resource-id MySecurityGroup

# Get stack outputs
aws cloudformation describe-stacks --stack-name my-stack --query 'Stacks[0].Outputs'

# List change sets for stack
aws cloudformation list-change-sets --stack-name my-stack

# Get change set details
aws cloudformation describe-change-set \
  --change-set-name my-changeset \
  --stack-name my-stack

# Get stack template
aws cloudformation get-template --stack-name my-stack

# Get template summary (number of resources, etc.)
aws cloudformation get-template-summary --template-body file://template.yaml

# List stack drift detections
aws cloudformation list-stack-drift-detection-statuses --stack-name my-stack

# Get stack drift status
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id drift-detection-id

# Check stack capability requirements
aws cloudformation get-template-summary --template-body file://template.yaml --query 'Capabilities'

# Validate template syntax
aws cloudformation validate-template --template-body file://template.yaml

# List stacks with specific tag
aws cloudformation list-stacks --query 'StackSummaries[?Tags[?Key==`Environment` && Value==`production`]]'

# Get stack creation time
aws cloudformation describe-stacks --stack-name my-stack --query 'Stacks[0].CreationTime'

# List parameter values used in stack
aws cloudformation describe-stacks --stack-name my-stack --query 'Stacks[0].Parameters'

# Get IAM capabilities required by template
aws cloudformation get-template-summary \
  --template-body file://template.yaml \
  --query 'Capabilities'
```

## Common Operations

```bash
# Create stack from template file
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml

# Create stack from S3 template
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-url https://s3.amazonaws.com/my-bucket/template.yaml

# Create stack with parameters
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters ParameterKey=EnvironmentName,ParameterValue=production ParameterKey=InstanceType,ParameterValue=t3.large

# Create stack with IAM permissions
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Create stack with tags
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --tags Key=Environment,Value=production Key=Owner,Value=admin Key=CostCenter,Value=engineering

# Create stack with notifications
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --notification-arns arn:aws:sns:us-east-1:123456789012:my-topic

# Create stack with rollback on failure
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --on-failure ROLLBACK

# Disable rollback on creation failure (for debugging)
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --on-failure DO_NOTHING

# Update stack with new template
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://updated-template.yaml

# Update stack parameters only (no template change)
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --parameters ParameterKey=InstanceType,ParameterValue=t3.large

# Update with specific resource replacement
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --parameters UsePreviousValue=true

# Create change set (preview changes before executing)
aws cloudformation create-change-set \
  --stack-name my-stack \
  --change-set-name my-changeset \
  --template-body file://updated-template.yaml

# Create change set for new stack
aws cloudformation create-change-set \
  --stack-name my-new-stack \
  --change-set-name my-changeset \
  --change-set-type CREATE \
  --template-body file://template.yaml

# Describe change set (see what will change)
aws cloudformation describe-change-set \
  --change-set-name my-changeset \
  --stack-name my-stack

# Execute change set
aws cloudformation execute-change-set \
  --change-set-name my-changeset \
  --stack-name my-stack

# Estimate template cost
aws cloudformation estimate-template-cost --template-body file://template.yaml

# Set stack policy (prevent accidental updates)
aws cloudformation set-stack-policy \
  --stack-name my-stack \
  --stack-policy-body file://stack-policy.json

# Set stack policy during update
aws cloudformation set-stack-policy \
  --stack-name my-stack \
  --stack-policy-during-update-body file://update-policy.json

# Continue update rollback (if stack is stuck)
aws cloudformation continue-update-rollback --stack-name my-stack

# Detect stack drift (check if resources match template)
aws cloudformation detect-stack-drift --stack-name my-stack

# Detect drift on specific resources
aws cloudformation detect-stack-resource-drift \
  --stack-name my-stack \
  --logical-resource-id MyResource

# List non-compliant resources
aws cloudformation list-stacks \
  --query 'StackSummaries[?DriftInformation.StackDriftStatus==`DRIFTED`]'

# Tag stack
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --tags Key=NewTag,Value=NewValue

# Get stack waiter (wait for operation to complete)
aws cloudformation wait stack-create-complete --stack-name my-stack
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete stack (deletes all resources)
aws cloudformation delete-stack --stack-name my-stack

# ⚠️ Cancel stack creation/update
aws cloudformation cancel-update-stack --stack-name my-stack

# ⚠️ Delete change set
aws cloudformation delete-change-set \
  --change-set-name my-changeset \
  --stack-name my-stack

# ⚠️ Rollback stack to previous state
aws cloudformation continue-update-rollback --stack-name my-stack

# ⚠️ Update stack with breaking changes
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://breaking-template.yaml

# ⚠️ Update stack policy (allows deletion of protected resources)
aws cloudformation set-stack-policy \
  --stack-name my-stack \
  --stack-policy-body file://permissive-policy.json

# ⚠️ Cancel update in progress
aws cloudformation cancel-update-stack --stack-name my-stack

# ⚠️ Delete all stack resources (before deleting stack)
aws cloudformation delete-stack --stack-name my-stack

# ⚠️ Force delete stack (ignores deletion policies)
aws cloudformation delete-stack \
  --stack-name my-stack \
  --query 'StackId'

# ⚠️ Update stack parameters (may force resource replacement)
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --parameters ParameterKey=DBMasterPassword,ParameterValue=NewPassword123!

# ⚠️ Change termination protection status
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --enable-termination-protection

# ⚠️ Disable termination protection (allows deletion)
aws cloudformation update-stack \
  --stack-name my-stack \
  --use-previous-template \
  --no-enable-termination-protection

# ⚠️ Execute change set that removes resources
aws cloudformation execute-change-set \
  --change-set-name destructive-changeset \
  --stack-name my-stack

# ⚠️ Update stack with auto rollback disabled
aws cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --disable-rollback
```

## Best Practices

- **Version Control**: Store templates in Git; use CI/CD pipelines for deployments
- **Parameter Validation**: Define parameter constraints; use parameter groups for organization
- **Stack Naming**: Use consistent naming conventions; include environment prefix
- **Modular Design**: Break large stacks into nested stacks for reusability
- **Change Sets**: Always use change sets to preview changes before executing in production
- **Stack Policies**: Set policies to prevent accidental deletion of critical resources
- **Drift Detection**: Regularly run drift detection to ensure resources match template
- **Outputs**: Use outputs to reference resources created by stack (cross-stack references)
- **Conditions**: Use conditions to deploy resources based on parameters/mappings
- **Metadata**: Add CloudFormation metadata to resources for organization and documentation
- **Error Handling**: Implement proper error handling in custom resources and stack creation
- **Testing**: Test templates in dev environment before deploying to production
- **Documentation**: Document parameters, outputs, and resource relationships in templates
- **Deletion Policy**: Explicitly set DeletionPolicy for databases and persistent data

## Related Skills

- IAM - Grant permissions for CloudFormation to create/manage resources
- S3 - Store CloudFormation templates and artifacts
- Systems Manager - Use Parameter Store for template parameters
- CodePipeline - Automate CloudFormation deployments
- Lambda - Create custom resources for CloudFormation
- SNS - Receive notifications about stack events
- CloudWatch - Monitor stack events and metrics
