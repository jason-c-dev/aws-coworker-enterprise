# Bedrock CLI Reference

## Overview

Amazon Bedrock is a fully managed service for building generative AI applications using foundation models. Bedrock has **two CLI namespaces**: `aws bedrock` for management operations (model access, guardrails, logging configuration) and `aws bedrock-runtime` for inference operations (invoking models). Use these commands to manage model access, invoke models, configure guardrails, and set up logging.

## Discovery Commands (Read-Only)

```bash
# List available foundation models
aws bedrock list-foundation-models \
  --profile {profile} \
  --region {region}

# List foundation models by provider
aws bedrock list-foundation-models \
  --by-provider anthropic \
  --profile {profile} \
  --region {region}

# List models by output modality
aws bedrock list-foundation-models \
  --by-output-modality TEXT \
  --profile {profile} \
  --region {region}

# Get specific foundation model details
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-sonnet-4-20250514 \
  --profile {profile} \
  --region {region}

# List custom models
aws bedrock list-custom-models \
  --profile {profile} \
  --region {region}

# Get custom model details
aws bedrock get-custom-model \
  --model-identifier my-custom-model \
  --profile {profile} \
  --region {region}

# List provisioned model throughput
aws bedrock list-provisioned-model-throughputs \
  --profile {profile} \
  --region {region}

# Get provisioned throughput details
aws bedrock get-provisioned-model-throughput \
  --provisioned-model-id my-provisioned-model \
  --profile {profile} \
  --region {region}

# List model access status
aws bedrock list-foundation-model-agreement-offers \
  --profile {profile} \
  --region {region}

# Get model invocation logging configuration
aws bedrock get-model-invocation-logging-configuration \
  --profile {profile} \
  --region {region}

# List guardrails
aws bedrock list-guardrails \
  --profile {profile} \
  --region {region}

# Get guardrail details
aws bedrock get-guardrail \
  --guardrail-identifier my-guardrail-id \
  --profile {profile} \
  --region {region}

# List guardrail versions
aws bedrock list-guardrails \
  --guardrail-identifier my-guardrail-id \
  --profile {profile} \
  --region {region}

# List inference profiles (cross-region inference)
aws bedrock list-inference-profiles \
  --profile {profile} \
  --region {region}

# Get inference profile details
aws bedrock get-inference-profile \
  --inference-profile-identifier us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --profile {profile} \
  --region {region}

# List tags for a Bedrock resource
aws bedrock list-tags-for-resource \
  --resource-arn arn:aws:bedrock:us-east-1:123456789012:guardrail/my-guardrail \
  --profile {profile} \
  --region {region}
```

## Inference Commands

```bash
# Invoke a model (synchronous)
# Note: This is read-only in that it doesn't change infrastructure,
# but it does incur inference costs
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-sonnet-4-20250514 \
  --content-type application/json \
  --accept application/json \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  output.json \
  --profile {profile} \
  --region {region}

# Invoke model with guardrail
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-sonnet-4-20250514 \
  --content-type application/json \
  --accept application/json \
  --guardrail-identifier my-guardrail-id \
  --guardrail-version 1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  output.json \
  --profile {profile} \
  --region {region}

# Invoke model with streaming
aws bedrock-runtime invoke-model-with-response-stream \
  --model-id anthropic.claude-sonnet-4-20250514 \
  --content-type application/json \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  --profile {profile} \
  --region {region}

# Invoke model using cross-region inference profile
aws bedrock-runtime invoke-model \
  --model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --content-type application/json \
  --accept application/json \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
  output.json \
  --profile {profile} \
  --region {region}

# Converse API (simplified multi-turn)
aws bedrock-runtime converse \
  --model-id anthropic.claude-sonnet-4-20250514 \
  --messages '[{"role":"user","content":[{"text":"Hello"}]}]' \
  --profile {profile} \
  --region {region}
```

## Common Operations

```bash
# Enable model access (request access to a foundation model)
# Note: Some models require EULA acceptance via the console
aws bedrock put-foundation-model-entitlement \
  --model-identifier anthropic.claude-sonnet-4-20250514 \
  --profile {profile} \
  --region {region}

# Configure model invocation logging
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{
    "cloudWatchConfig": {
      "logGroupName": "/aws/bedrock/model-invocations",
      "roleArn": "arn:aws:iam::123456789012:role/BedrockLoggingRole"
    },
    "s3Config": {
      "bucketName": "my-bedrock-logs",
      "keyPrefix": "invocation-logs/"
    },
    "textDataDeliveryEnabled": true,
    "imageDataDeliveryEnabled": false,
    "embeddingDataDeliveryEnabled": false
  }' \
  --profile {profile} \
  --region {region}

# Create a guardrail
aws bedrock create-guardrail \
  --name my-guardrail \
  --description "Content filtering guardrail" \
  --blocked-input-messaging "Request blocked by guardrail" \
  --blocked-outputs-messaging "Response blocked by guardrail" \
  --content-policy-config '{
    "filtersConfig": [
      {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"}
    ]
  }' \
  --tags key=Environment,value=development key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}

# Update a guardrail
aws bedrock update-guardrail \
  --guardrail-identifier my-guardrail-id \
  --name my-guardrail \
  --description "Updated content filtering guardrail" \
  --blocked-input-messaging "Request blocked by guardrail" \
  --blocked-outputs-messaging "Response blocked by guardrail" \
  --profile {profile} \
  --region {region}

# Create guardrail version (snapshot)
aws bedrock create-guardrail-version \
  --guardrail-identifier my-guardrail-id \
  --description "Production-ready version" \
  --profile {profile} \
  --region {region}

# Create provisioned throughput
aws bedrock create-provisioned-model-throughput \
  --model-id anthropic.claude-sonnet-4-20250514 \
  --provisioned-model-name my-provisioned-claude \
  --model-units 1 \
  --tags key=Environment,value=production key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}

# Update provisioned throughput
aws bedrock update-provisioned-model-throughput \
  --provisioned-model-id my-provisioned-model \
  --desired-model-units 2 \
  --profile {profile} \
  --region {region}

# Tag a Bedrock resource
aws bedrock tag-resource \
  --resource-arn arn:aws:bedrock:us-east-1:123456789012:guardrail/my-guardrail \
  --tags key=Environment,value=production key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete a guardrail
aws bedrock delete-guardrail \
  --guardrail-identifier my-guardrail-id \
  --profile {profile} \
  --region {region}

# ⚠️ Delete provisioned throughput
aws bedrock delete-provisioned-model-throughput \
  --provisioned-model-id my-provisioned-model \
  --profile {profile} \
  --region {region}

# ⚠️ Delete custom model
aws bedrock delete-custom-model \
  --model-identifier my-custom-model \
  --profile {profile} \
  --region {region}

# ⚠️ Remove model invocation logging
aws bedrock delete-model-invocation-logging-configuration \
  --profile {profile} \
  --region {region}

# ⚠️ Untag a Bedrock resource
aws bedrock untag-resource \
  --resource-arn arn:aws:bedrock:us-east-1:123456789012:guardrail/my-guardrail \
  --tag-keys Environment Owner \
  --profile {profile} \
  --region {region}
```

## Key Notes

### CLI Namespaces

Bedrock uses two separate CLI namespaces:

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `aws bedrock` | Management operations — model access, guardrails, logging, provisioned throughput | `aws bedrock list-foundation-models` |
| `aws bedrock-runtime` | Inference operations — invoking models, streaming, conversations | `aws bedrock-runtime invoke-model` |

### Model ID Patterns

Anthropic models on Bedrock follow this pattern:

| Model | Model ID |
|-------|----------|
| Claude Opus 4 | `anthropic.claude-opus-4-20250514` |
| Claude Sonnet 4 | `anthropic.claude-sonnet-4-20250514` |
| Claude Haiku 3.5 | `anthropic.claude-3-5-haiku-20241022-v1:0` |

### Cross-Region Inference

Cross-region inference profiles provide high availability by routing requests across regions:

| Profile Pattern | Example |
|----------------|---------|
| `{region-prefix}.{model-id}` | `us.anthropic.claude-sonnet-4-20250514-v1:0` |

Use inference profiles for production workloads to avoid single-region capacity constraints.

### Bedrock Guardrails vs Governance Guardrails

**These are different concepts:**

| Term | Meaning |
|------|---------|
| **Bedrock Guardrails** | An AWS product feature — content filters applied to model inference (managed via `aws bedrock create-guardrail`) |
| **Governance Guardrails** | AWS Coworker's organizational policies — never-do/always-do rules for infrastructure operations (defined in `skills/org/aws-governance-guardrails/`) |

Do not confuse the two. Bedrock Guardrails filter model inputs/outputs. Governance Guardrails govern how we manage infrastructure.

## Best Practices

- **Model Access**: Explicitly grant access per model family — do not request access to all models
- **Inference Profiles**: Use cross-region inference profiles for production to distribute load
- **Guardrails**: Version guardrails before production use; test in development first
- **Logging**: Enable model invocation logging for audit trails and cost tracking
- **Provisioned Throughput**: Evaluate cost vs on-demand for steady-state workloads; provision only what you need
- **Cost Awareness**: Model invocations incur per-token costs — monitor usage via CloudWatch and logging
- **IAM**: Scope `bedrock:InvokeModel` permissions to specific model ARNs, not `*`
- **Tags**: Apply governance tags to all Bedrock resources (guardrails, provisioned throughput, custom models)

## Related Skills

- Bedrock AgentCore — Deploy and manage AI agents on Bedrock AgentCore Runtime
- IAM — Create roles with scoped Bedrock permissions
- CloudWatch — Monitor model invocation metrics and logging
- S3 — Store model invocation logs
- VPC — Configure VPC endpoints for private Bedrock API access
