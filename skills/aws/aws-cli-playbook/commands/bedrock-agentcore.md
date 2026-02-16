# Bedrock AgentCore CLI Reference

## Overview

Amazon Bedrock AgentCore is a managed runtime for deploying AI agents as long-running, stateful sessions. AgentCore handles session isolation (Firecracker microVMs), identity management, tool gateway configuration, and observability. Use these commands to deploy agent runtimes, manage credentials, configure gateway targets, and monitor agent sessions.

**Service launched:** 2025. CLI may evolve — this documents the stable subset.

**CLI namespace:** `aws bedrock-agentcore`

## Discovery Commands (Read-Only)

```bash
# List all agent runtimes
aws bedrock-agentcore list-agent-runtimes \
  --profile {profile} \
  --region {region}

# Get agent runtime details
aws bedrock-agentcore get-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List agent runtime endpoints
aws bedrock-agentcore list-agent-runtime-endpoints \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# Get agent runtime endpoint details
aws bedrock-agentcore get-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --endpoint-id ep-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List API key credentials (AgentCore Identity)
aws bedrock-agentcore list-api-key-credentials \
  --profile {profile} \
  --region {region}

# Get API key credential details
aws bedrock-agentcore get-api-key-credential \
  --api-key-credential-id akc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List OAuth2 credentials
aws bedrock-agentcore list-oauth2-credentials \
  --profile {profile} \
  --region {region}

# Get OAuth2 credential details
aws bedrock-agentcore get-oauth2-credential \
  --oauth2-credential-id oc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List gateway targets (AgentCore Gateway)
aws bedrock-agentcore list-gateway-targets \
  --profile {profile} \
  --region {region}

# Get gateway target details
aws bedrock-agentcore get-gateway-target \
  --gateway-target-id gt-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List workload identities
aws bedrock-agentcore list-workload-identities \
  --profile {profile} \
  --region {region}

# Get workload identity details
aws bedrock-agentcore get-workload-identity \
  --workload-identity-id wi-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List memory stores (agent memory)
aws bedrock-agentcore list-memories \
  --profile {profile} \
  --region {region}

# Get memory details
aws bedrock-agentcore get-memory \
  --memory-id mem-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List tags for an AgentCore resource
aws bedrock-agentcore list-tags-for-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

## Common Operations

```bash
# Create an agent runtime
aws bedrock-agentcore create-agent-runtime \
  --agent-runtime-name aws-coworker-agent \
  --description "AWS Coworker deployment" \
  --role-arn arn:aws:iam::123456789012:role/AgentCoreExecutionRole \
  --network-configuration '{
    "networkMode": "VPC",
    "vpcConfiguration": {
      "subnetIds": ["subnet-xxxxxxxxxx", "subnet-yyyyyyyyyy"],
      "securityGroupIds": ["sg-xxxxxxxxxx"]
    }
  }' \
  --agent-runtime-artifact '{
    "containerConfiguration": {
      "containerUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/aws-coworker:latest"
    }
  }' \
  --tags key=Environment,value=development key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}

# Create agent runtime endpoint
aws bedrock-agentcore create-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --name aws-coworker-endpoint \
  --description "Primary endpoint for AWS Coworker" \
  --profile {profile} \
  --region {region}

# Update an agent runtime
aws bedrock-agentcore update-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --description "Updated AWS Coworker deployment" \
  --agent-runtime-artifact '{
    "containerConfiguration": {
      "containerUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/aws-coworker:v2"
    }
  }' \
  --profile {profile} \
  --region {region}

# Create API key credential (AgentCore Identity)
aws bedrock-agentcore create-api-key-credential \
  --name aws-coworker-api-key \
  --description "API key for external service access" \
  --api-key "STORED_IN_SECRETS_MANAGER" \
  --profile {profile} \
  --region {region}

# Create OAuth2 credential
aws bedrock-agentcore create-oauth2-credential \
  --name aws-coworker-oauth \
  --description "OAuth2 credential for service integration" \
  --oauth2-provider-config-type CUSTOM \
  --credential-provider-type OAUTH2_CLIENT_CREDENTIALS \
  --profile {profile} \
  --region {region}

# Create a gateway target
aws bedrock-agentcore create-gateway-target \
  --name aws-api-gateway \
  --description "API Gateway target for tool calls" \
  --gateway-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/gw-xxxxxxxxxx \
  --endpoint-config '{
    "url": "https://api.example.com"
  }' \
  --profile {profile} \
  --region {region}

# Update a gateway target
aws bedrock-agentcore update-gateway-target \
  --gateway-target-id gt-xxxxxxxxxx \
  --description "Updated API Gateway target" \
  --endpoint-config '{
    "url": "https://api-v2.example.com"
  }' \
  --profile {profile} \
  --region {region}

# Create workload identity
aws bedrock-agentcore create-workload-identity \
  --name aws-coworker-identity \
  --allowed-resource-oauth2-return-urls '["https://callback.example.com/oauth2"]' \
  --profile {profile} \
  --region {region}

# Create memory (agent memory store)
aws bedrock-agentcore create-memory \
  --name aws-coworker-memory \
  --description "Memory store for AWS Coworker sessions" \
  --profile {profile} \
  --region {region}

# Tag an AgentCore resource
aws bedrock-agentcore tag-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --tags key=Environment,value=production key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete an agent runtime
aws bedrock-agentcore delete-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete an agent runtime endpoint
aws bedrock-agentcore delete-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --endpoint-id ep-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete API key credential
aws bedrock-agentcore delete-api-key-credential \
  --api-key-credential-id akc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete OAuth2 credential
aws bedrock-agentcore delete-oauth2-credential \
  --oauth2-credential-id oc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete a gateway target
aws bedrock-agentcore delete-gateway-target \
  --gateway-target-id gt-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete workload identity
aws bedrock-agentcore delete-workload-identity \
  --workload-identity-id wi-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete memory
aws bedrock-agentcore delete-memory \
  --memory-id mem-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Untag an AgentCore resource
aws bedrock-agentcore untag-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --tag-keys Environment Owner \
  --profile {profile} \
  --region {region}
```

## Key Notes

### AgentCore Architecture

AgentCore provides three core capabilities:

| Capability | Description |
|-----------|-------------|
| **AgentCore Runtime** | Deploy and run agent containers in isolated Firecracker microVMs |
| **AgentCore Identity** | Per-agent IAM identity, credential management (API keys, OAuth2), workload identity |
| **AgentCore Gateway** | Managed API gateway for agent tool calls with credential injection |

### Session Isolation

Each agent session runs in a dedicated Firecracker microVM:

- Sessions are fully isolated from each other
- Sessions can run for up to 8 hours (long-running agentic tasks)
- Each session gets its own network namespace and filesystem
- Session state is ephemeral — destroyed when session ends

### Resource ID Patterns

| Resource | ID Pattern | Example |
|----------|-----------|---------|
| Agent Runtime | `art-{alphanumeric}` | `art-abc123def456` |
| Endpoint | `ep-{alphanumeric}` | `ep-abc123def456` |
| API Key Credential | `akc-{alphanumeric}` | `akc-abc123def456` |
| OAuth2 Credential | `oc-{alphanumeric}` | `oc-abc123def456` |
| Gateway Target | `gt-{alphanumeric}` | `gt-abc123def456` |
| Workload Identity | `wi-{alphanumeric}` | `wi-abc123def456` |
| Memory | `mem-{alphanumeric}` | `mem-abc123def456` |

### IAM Roles for AgentCore

AgentCore requires at least two IAM roles:

| Role | Purpose |
|------|---------|
| **Execution Role** | Assumed by AgentCore to pull container images, write logs, access secrets |
| **Agent Role** | Assumed by the agent at runtime to interact with AWS services (scoped to what the agent should be able to do) |

**Critical:** These must be separate roles. The execution role should not have permissions the agent needs at runtime, and vice versa.

### AgentCore Policy (Cedar) — Reference Only

AgentCore supports Cedar policies for fine-grained tool call interception. Cedar policies can:

- Allow or deny specific tool calls based on context
- Enforce data classification rules on tool inputs/outputs
- Require human approval for certain operations

Cedar policy implementation is covered separately (Part 5 of the blog series / future skill addition). This CLI reference documents the runtime, not Cedar policies.

### Service Appropriateness

AgentCore is the right choice for:

| Use Case | Why AgentCore |
|----------|--------------|
| Deploying AI agents that interact with AWS | Purpose-built: session isolation, identity, tool gateway |
| Long-running agentic tasks (minutes to hours) | Up to 8-hour sessions, unlike Lambda's 15-minute limit |
| Agents that need tool access with credential management | AgentCore Gateway handles credential injection |
| Multi-turn agent conversations with state | Session state preserved within microVM |

AgentCore is NOT the right choice for:

| Use Case | Better Alternative |
|----------|--------------------|
| Simple API proxy to Bedrock | API Gateway + Bedrock direct |
| Batch inference (no agent loop) | Bedrock Batch Inference |
| Non-agent LLM workloads (chatbot, summarization) | Bedrock API directly |
| Short-lived stateless functions | Lambda |

## Best Practices

- **Container Images**: Source from private ECR only — never use public registries for agent containers
- **IAM**: Separate execution role from agent runtime role; scope both to least privilege
- **VPC Placement**: Deploy agent runtimes in private subnets; use VPC endpoints for AWS API access
- **Credentials**: Never hardcode API keys in container images or environment variables — use AgentCore Identity
- **Session Timeouts**: Configure appropriate session timeouts to prevent runaway sessions and cost overruns
- **Logging**: Enable CloudWatch logging for all agent runtimes; set retention policies
- **Tags**: Apply governance tags (Environment, Owner, CostCenter) to all AgentCore resources
- **Gateway Targets**: Use AgentCore Gateway for external API calls instead of direct HTTP from agents
- **Monitoring**: Set up CloudWatch alarms for agent health, session duration, and error rates
- **Cost**: Monitor session concurrency — each session runs a microVM; unused sessions still incur cost

## Related Skills

- Bedrock — Foundation model access and guardrails
- IAM — Create execution and agent runtime roles
- ECR — Host agent container images
- VPC — Configure private subnets and security groups for agent runtimes
- CloudWatch — Monitor agent runtime metrics and logs
- Secrets Manager — Store API keys and credentials referenced by AgentCore Identity
