# Lambda CLI Reference

## Overview
AWS Lambda is a serverless compute service that lets you run code without provisioning or managing servers. Use these commands to create and manage Lambda functions, manage layers, configure event sources, set environment variables, and manage permissions.

## Discovery Commands (Read-Only)

```bash
# List all Lambda functions
aws lambda list-functions

# Get function details
aws lambda get-function --function-name my-function

# Get function configuration
aws lambda get-function-configuration --function-name my-function

# Get function code
aws lambda get-function --function-name my-function --query 'Code.Location'

# List function versions
aws lambda list-versions-by-function --function-name my-function

# List function aliases
aws lambda list-aliases --function-name my-function

# Get alias details
aws lambda get-alias --function-name my-function --name my-alias

# List event source mappings (triggers)
aws lambda list-event-source-mappings --function-name my-function

# Get event source mapping details
aws lambda get-event-source-mapping --uuid mapping-uuid

# List function layers
aws lambda list-layers

# Get layer version info
aws lambda get-layer-version --layer-name my-layer --version-number 1

# List function permissions (resource-based policy)
aws lambda get-policy --function-name my-function

# Get reserved concurrent executions
aws lambda get-function-concurrency --function-name my-function

# Get function code signing config
aws lambda get-function-code-signing-config --function-name my-function

# List available runtimes
aws lambda list-runtimes

# Get Lambda account settings
aws lambda get-account-settings

# List functions by tag
aws lambda list-functions --query 'Functions[?Tags.Environment==`production`]'

# Check function state (Active, Inactive, Failed)
aws lambda get-function-configuration --function-name my-function --query 'State'

# Get function's CloudWatch logs group
aws lambda get-function-configuration --function-name my-function --query 'LoggingConfig'

# List provisioned concurrency configurations
aws lambda get-provisioned-concurrency-config \
  --function-name my-function \
  --provisioned-concurrent-executions 100
```

## Common Operations

```bash
# Create a Lambda function (from ZIP)
aws lambda create-function \
  --function-name my-function \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip

# Create function with inline code
aws lambda create-function \
  --function-name my-function \
  --runtime nodejs18.x \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler index.handler \
  --zip-file fileb://index.zip

# Create function with environment variables
aws lambda create-function \
  --function-name my-function \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip \
  --environment Variables={DB_HOST=localhost,API_KEY=secret}

# Create function with VPC configuration
aws lambda create-function \
  --function-name my-function \
  --runtime python3.11 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip \
  --vpc-config SubnetIds=subnet-12345678,SecurityGroupIds=sg-12345678

# Update function code (from ZIP file)
aws lambda update-function-code \
  --function-name my-function \
  --zip-file fileb://updated-function.zip

# Update function code from S3
aws lambda update-function-code \
  --function-name my-function \
  --s3-bucket my-bucket \
  --s3-key path/to/function.zip

# Update function configuration
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 60 \
  --memory-size 512

# Update environment variables
aws lambda update-function-configuration \
  --function-name my-function \
  --environment Variables={DB_HOST=prod-db,API_KEY=new-secret}

# Add permission for S3 to invoke function
aws lambda add-permission \
  --function-name my-function \
  --principal s3.amazonaws.com \
  --action lambda:InvokeFunction \
  --statement-id AllowS3Bucket \
  --source-arn arn:aws:s3:::my-bucket

# Add permission for API Gateway
aws lambda add-permission \
  --function-name my-function \
  --principal apigateway.amazonaws.com \
  --action lambda:InvokeFunction \
  --statement-id AllowAPIGateway \
  --source-arn arn:aws:execute-api:us-east-1:123456789012:api-id/*/*

# Add permission for SNS topic
aws lambda add-permission \
  --function-name my-function \
  --principal sns.amazonaws.com \
  --action lambda:InvokeFunction \
  --statement-id AllowSNS \
  --source-arn arn:aws:sns:us-east-1:123456789012:my-topic

# Create event source mapping (DynamoDB Streams)
aws lambda create-event-source-mapping \
  --event-source-arn arn:aws:dynamodb:us-east-1:123456789012:table/my-table/stream/2024-01-01T00:00:00.000 \
  --function-name my-function \
  --enabled \
  --batch-size 100 \
  --starting-position LATEST

# Create event source mapping (SQS)
aws lambda create-event-source-mapping \
  --event-source-arn arn:aws:sqs:us-east-1:123456789012:my-queue \
  --function-name my-function \
  --batch-size 10

# Publish function version
aws lambda publish-version \
  --function-name my-function \
  --description "Production release v1.0"

# Create function alias
aws lambda create-alias \
  --function-name my-function \
  --name PROD \
  --function-version 5

# Update alias to point to new version
aws lambda update-alias \
  --function-name my-function \
  --name PROD \
  --function-version 6

# Create Lambda layer
aws lambda publish-layer-version \
  --layer-name my-layer \
  --description "Common libraries" \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11

# Tag Lambda function
aws lambda tag-resource \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --tags Environment=production,Owner=admin

# Set reserved concurrency (max 100 concurrent executions)
aws lambda put-function-concurrency \
  --function-name my-function \
  --reserved-concurrent-executions 100

# Set provisioned concurrency (pre-warmed instances)
aws lambda put-provisioned-concurrency-config \
  --function-name my-function \
  --provisioned-concurrent-executions 10 \
  --qualifier my-alias

# Invoke function synchronously
aws lambda invoke \
  --function-name my-function \
  --payload '{"key":"value"}' \
  response.json

# Invoke function asynchronously
aws lambda invoke \
  --function-name my-function \
  --invocation-type Event \
  --payload '{"key":"value"}' \
  response.json

# Test function with sample event
aws lambda test-function \
  --function-name my-function \
  --payload file://test-event.json
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete Lambda function
aws lambda delete-function --function-name my-function

# ⚠️ Delete function version
aws lambda delete-function \
  --function-name my-function \
  --qualifier 5

# ⚠️ Delete function alias
aws lambda delete-alias \
  --function-name my-function \
  --name my-alias

# ⚠️ Delete layer version
aws lambda delete-layer-version \
  --layer-name my-layer \
  --version-number 1

# ⚠️ Delete event source mapping
aws lambda delete-event-source-mapping --uuid mapping-uuid

# ⚠️ Remove permission
aws lambda remove-permission \
  --function-name my-function \
  --statement-id AllowS3Bucket

# ⚠️ Update function environment variables (may require redeployment)
aws lambda update-function-configuration \
  --function-name my-function \
  --environment Variables={DELETED_VAR=}

# ⚠️ Delete reserved concurrency (allows unlimited concurrent executions)
aws lambda delete-function-concurrency --function-name my-function

# ⚠️ Delete provisioned concurrency
aws lambda delete-provisioned-concurrency-config \
  --function-name my-function \
  --qualifier my-alias

# ⚠️ Untag function
aws lambda untag-resource \
  --resource arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --tag-keys Environment Owner

# ⚠️ Update function code (breaking change if handler signature changes)
aws lambda update-function-code \
  --function-name my-function \
  --s3-bucket new-bucket \
  --s3-key path/to/new-function.zip

# ⚠️ Update function timeout (very short timeout can break functionality)
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 3

# ⚠️ Remove VPC configuration
aws lambda update-function-configuration \
  --function-name my-function \
  --vpc-config SubnetIds=,SecurityGroupIds=

# ⚠️ Update event source mapping batch size
aws lambda update-event-source-mapping \
  --uuid mapping-uuid \
  --batch-size 1

# ⚠️ Disable event source mapping
aws lambda update-event-source-mapping \
  --uuid mapping-uuid \
  --state Disabled
```

## Best Practices

- **Handler Naming**: Use clear handler names; avoid lambda_handler collisions in layered dependencies
- **Timeout Configuration**: Set appropriate timeout (default 3s); consider cold start times
- **Memory Allocation**: Higher memory means more CPU; monitor CloudWatch metrics to optimize cost
- **Environment Variables**: Use for configuration; use Secrets Manager for sensitive data
- **VPC Configuration**: Only place in VPC if accessing RDS or other private resources
- **Cold Starts**: Use provisioned concurrency for critical paths; keep dependencies minimal
- **Logging**: Use CloudWatch Logs; structure logs as JSON for easier parsing and analysis
- **Permissions**: Grant minimum required permissions via IAM roles; avoid overly broad policies
- **Versioning**: Publish versions for production; use aliases to avoid hardcoding function versions
- **Layers**: Use layers for shared libraries; keep layers under 250MB total unzipped size
- **Reserved Concurrency**: Set on production functions to prevent throttling; monitor utilization
- **Error Handling**: Implement retry logic for async invocations; use dead-letter queues for failures

## Related Skills

- IAM - Create execution roles for Lambda functions
- S3 - Trigger Lambda from S3 events
- API Gateway - Invoke Lambda from HTTP endpoints
- DynamoDB - Use streams to trigger Lambda functions
- SQS/SNS - Queue events for Lambda processing
- CloudWatch - Monitor Lambda metrics and logs
- Secrets Manager - Store sensitive data for Lambda functions
