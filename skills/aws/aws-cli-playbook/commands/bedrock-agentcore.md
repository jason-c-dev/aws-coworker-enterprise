# Bedrock AgentCore CLI Reference

## Overview

Amazon Bedrock AgentCore is a managed runtime for deploying AI agents as long-running, stateful sessions. AgentCore handles session isolation (Firecracker microVMs), identity management, tool gateway configuration, and observability. Use these commands to deploy agent runtimes, manage credentials, configure gateway targets, and monitor agent sessions.

**Service launched:** 2025 (GA). CLI stable as of AWS CLI v2.33.0+.

**IMPORTANT — Two CLI Namespaces:**

AgentCore uses a **control plane / data plane split**. Using the wrong namespace is the most common error.

| Namespace | Purpose | Use For |
|-----------|---------|---------|
| `aws bedrock-agentcore-control` | **Control plane** — manage infrastructure | Create, list, update, delete runtimes, gateways, policies, agents |
| `aws bedrock-agentcore` | **Data plane** — invoke agents | Send requests to running agent runtimes |

**Common mistake:** Running `aws bedrock-agentcore list-agent-runtimes` (wrong — data plane namespace) instead of `aws bedrock-agentcore-control list-agent-runtimes` (correct — control plane namespace). All management commands use `bedrock-agentcore-control`.

---

## Control Plane: Agent Runtime Operations

### Discovery Commands (Read-Only)

```bash
# List all agent runtimes
aws bedrock-agentcore-control list-agent-runtimes \
  --profile {profile} \
  --region {region}

# Get agent runtime details
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List agent runtime endpoints
aws bedrock-agentcore-control list-agent-runtime-endpoints \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# Get agent runtime endpoint details
aws bedrock-agentcore-control get-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --endpoint-id ep-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create an agent runtime
aws bedrock-agentcore-control create-agent-runtime \
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
aws bedrock-agentcore-control create-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --name aws-coworker-endpoint \
  --description "Primary endpoint for AWS Coworker" \
  --profile {profile} \
  --region {region}

# Update an agent runtime
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --description "Updated AWS Coworker deployment" \
  --agent-runtime-artifact '{
    "containerConfiguration": {
      "containerUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/aws-coworker:v2"
    }
  }' \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete an agent runtime
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete an agent runtime endpoint
aws bedrock-agentcore-control delete-agent-runtime-endpoint \
  --agent-runtime-id art-xxxxxxxxxx \
  --endpoint-id ep-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: Agent Definition Operations

### Discovery Commands (Read-Only)

```bash
# List all agents
aws bedrock-agentcore-control list-agents \
  --profile {profile} \
  --region {region}

# Get agent details
aws bedrock-agentcore-control get-agent \
  --agent-id ag-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create an agent definition
aws bedrock-agentcore-control create-agent \
  --agent-name aws-coworker \
  --description "AWS Coworker agent definition" \
  --profile {profile} \
  --region {region}

# Update an agent
aws bedrock-agentcore-control update-agent \
  --agent-id ag-xxxxxxxxxx \
  --description "Updated agent definition" \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete an agent
aws bedrock-agentcore-control delete-agent \
  --agent-id ag-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: MCP Gateway Operations

MCP Gateways provide managed tool access for agents, with credential injection and target routing.

### Discovery Commands (Read-Only)

```bash
# List all MCP gateways
aws bedrock-agentcore-control list-mcp-gateways \
  --profile {profile} \
  --region {region}

# Get MCP gateway details
aws bedrock-agentcore-control get-mcp-gateway \
  --gateway-id gw-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List MCP gateway targets
aws bedrock-agentcore-control list-mcp-gateway-targets \
  --gateway-id gw-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# Get MCP gateway target details
aws bedrock-agentcore-control get-mcp-gateway-target \
  --gateway-id gw-xxxxxxxxxx \
  --target-id gt-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create an MCP gateway
aws bedrock-agentcore-control create-mcp-gateway \
  --name aws-coworker-gateway \
  --description "Tool gateway for AWS Coworker agents" \
  --profile {profile} \
  --region {region}

# Create an MCP gateway target (Lambda)
aws bedrock-agentcore-control create-mcp-gateway-target \
  --gateway-id gw-xxxxxxxxxx \
  --name api-tool-target \
  --description "Lambda-backed tool target" \
  --endpoint-config '{
    "url": "https://api.example.com"
  }' \
  --profile {profile} \
  --region {region}

# Update an MCP gateway
aws bedrock-agentcore-control update-mcp-gateway \
  --gateway-id gw-xxxxxxxxxx \
  --description "Updated gateway configuration" \
  --profile {profile} \
  --region {region}

# Update an MCP gateway target
aws bedrock-agentcore-control update-mcp-gateway-target \
  --gateway-id gw-xxxxxxxxxx \
  --target-id gt-xxxxxxxxxx \
  --endpoint-config '{
    "url": "https://api-v2.example.com"
  }' \
  --profile {profile} \
  --region {region}

# Synchronize gateway targets with their sources
aws bedrock-agentcore-control synchronize-mcp-gateway-targets \
  --gateway-id gw-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete an MCP gateway
aws bedrock-agentcore-control delete-mcp-gateway \
  --gateway-id gw-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete an MCP gateway target
aws bedrock-agentcore-control delete-mcp-gateway-target \
  --gateway-id gw-xxxxxxxxxx \
  --target-id gt-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: Identity and Credential Operations

### Discovery Commands (Read-Only)

```bash
# List API key credentials (AgentCore Identity)
aws bedrock-agentcore-control list-api-key-credentials \
  --profile {profile} \
  --region {region}

# Get API key credential details
aws bedrock-agentcore-control get-api-key-credential \
  --api-key-credential-id akc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List OAuth2 credentials
aws bedrock-agentcore-control list-oauth2-credentials \
  --profile {profile} \
  --region {region}

# Get OAuth2 credential details
aws bedrock-agentcore-control get-oauth2-credential \
  --oauth2-credential-id oc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List workload identities
aws bedrock-agentcore-control list-workload-identities \
  --profile {profile} \
  --region {region}

# Get workload identity details
aws bedrock-agentcore-control get-workload-identity \
  --workload-identity-id wi-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create API key credential (AgentCore Identity)
aws bedrock-agentcore-control create-api-key-credential \
  --name aws-coworker-api-key \
  --description "API key for external service access" \
  --api-key "STORED_IN_SECRETS_MANAGER" \
  --profile {profile} \
  --region {region}

# Create OAuth2 credential
aws bedrock-agentcore-control create-oauth2-credential \
  --name aws-coworker-oauth \
  --description "OAuth2 credential for service integration" \
  --oauth2-provider-config-type CUSTOM \
  --credential-provider-type OAUTH2_CLIENT_CREDENTIALS \
  --profile {profile} \
  --region {region}

# Create workload identity
aws bedrock-agentcore-control create-workload-identity \
  --name aws-coworker-identity \
  --allowed-resource-oauth2-return-urls '["https://callback.example.com/oauth2"]' \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete API key credential
aws bedrock-agentcore-control delete-api-key-credential \
  --api-key-credential-id akc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete OAuth2 credential
aws bedrock-agentcore-control delete-oauth2-credential \
  --oauth2-credential-id oc-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete workload identity
aws bedrock-agentcore-control delete-workload-identity \
  --workload-identity-id wi-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: Policy Engine (Cedar) Operations

AgentCore supports Cedar policies for fine-grained authorization of tool calls, data classification, and human-in-the-loop approval flows.

### Discovery Commands (Read-Only)

```bash
# List policy engines
aws bedrock-agentcore-control list-policy-engines \
  --profile {profile} \
  --region {region}

# Get policy engine details
aws bedrock-agentcore-control get-policy-engine \
  --policy-engine-id pe-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# List policies in a policy engine
aws bedrock-agentcore-control list-policies \
  --policy-engine-id pe-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# Get policy details
aws bedrock-agentcore-control get-policy \
  --policy-engine-id pe-xxxxxxxxxx \
  --policy-id pol-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create a policy engine
aws bedrock-agentcore-control create-policy-engine \
  --name aws-coworker-policies \
  --description "Cedar policy engine for AWS Coworker tool authorization" \
  --profile {profile} \
  --region {region}

# Create a Cedar policy
aws bedrock-agentcore-control create-policy \
  --policy-engine-id pe-xxxxxxxxxx \
  --name deny-production-mutations \
  --description "Block mutation tool calls in production without approval" \
  --policy-type CEDAR \
  --policy-document '{
    "statement": "forbid(principal, action == Action::\"InvokeTool\", resource) when { resource.environment == \"production\" && resource.mutating == true };"
  }' \
  --profile {profile} \
  --region {region}

# Update a policy
aws bedrock-agentcore-control update-policy \
  --policy-engine-id pe-xxxxxxxxxx \
  --policy-id pol-xxxxxxxxxx \
  --description "Updated policy" \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete a policy (only if no active references)
aws bedrock-agentcore-control delete-policy \
  --policy-engine-id pe-xxxxxxxxxx \
  --policy-id pol-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# ⚠️ Delete a policy engine (only if no policies exist)
aws bedrock-agentcore-control delete-policy-engine \
  --policy-engine-id pe-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: Memory Operations

### Discovery Commands (Read-Only)

```bash
# List memory stores (agent memory)
aws bedrock-agentcore-control list-memories \
  --profile {profile} \
  --region {region}

# Get memory details
aws bedrock-agentcore-control get-memory \
  --memory-id mem-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

### Common Operations

```bash
# Create memory (agent memory store)
aws bedrock-agentcore-control create-memory \
  --name aws-coworker-memory \
  --description "Memory store for AWS Coworker sessions" \
  --profile {profile} \
  --region {region}
```

### Mutation Commands (Require Approval)

```bash
# ⚠️ Delete memory
aws bedrock-agentcore-control delete-memory \
  --memory-id mem-xxxxxxxxxx \
  --profile {profile} \
  --region {region}
```

---

## Control Plane: Tagging

```bash
# List tags for an AgentCore resource
aws bedrock-agentcore-control list-tags-for-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --profile {profile} \
  --region {region}

# Tag an AgentCore resource
aws bedrock-agentcore-control tag-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --tags key=Environment,value=production key=Owner,value=platform-team \
  --profile {profile} \
  --region {region}

# ⚠️ Untag an AgentCore resource
aws bedrock-agentcore-control untag-resource \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/art-xxxxxxxxxx \
  --tag-keys Environment Owner \
  --profile {profile} \
  --region {region}
```

---

## Data Plane: Agent Invocation

The data plane namespace (`aws bedrock-agentcore`) is used to invoke running agent runtimes.

```bash
# Invoke an agent runtime (send a request)
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-id art-xxxxxxxxxx \
  --endpoint-id ep-xxxxxxxxxx \
  --payload '{"message": "List my S3 buckets"}' \
  --profile {profile} \
  --region {region}
```

**Note:** `invoke-agent-runtime` supports streaming responses and payloads up to 100 MB. Requires `bedrock-agentcore:InvokeAgentRuntime` permission.

---

## Key Notes

### AgentCore Architecture

AgentCore provides four core capabilities:

| Capability | Description |
|-----------|-------------|
| **AgentCore Runtime** | Deploy and run agent containers in isolated Firecracker microVMs |
| **AgentCore Identity** | Per-agent IAM identity, credential management (API keys, OAuth2), workload identity |
| **AgentCore Gateway (MCP)** | Managed MCP gateway for agent tool calls with credential injection |
| **AgentCore Policy (Cedar)** | Fine-grained authorization policies for tool call interception |

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
| Agent | `ag-{alphanumeric}` | `ag-abc123def456` |
| API Key Credential | `akc-{alphanumeric}` | `akc-abc123def456` |
| OAuth2 Credential | `oc-{alphanumeric}` | `oc-abc123def456` |
| MCP Gateway | `gw-{alphanumeric}` | `gw-abc123def456` |
| Gateway Target | `gt-{alphanumeric}` | `gt-abc123def456` |
| Policy Engine | `pe-{alphanumeric}` | `pe-abc123def456` |
| Policy | `pol-{alphanumeric}` | `pol-abc123def456` |
| Workload Identity | `wi-{alphanumeric}` | `wi-abc123def456` |
| Memory | `mem-{alphanumeric}` | `mem-abc123def456` |

### IAM Roles for AgentCore

AgentCore requires at least two IAM roles:

| Role | Purpose |
|------|---------|
| **Execution Role** | Assumed by AgentCore to pull container images, write logs, access secrets |
| **Agent Role** | Assumed by the agent at runtime to interact with AWS services (scoped to what the agent should be able to do) |

**Critical:** These must be separate roles. The execution role should not have permissions the agent needs at runtime, and vice versa.

### CLI Namespace Quick Reference

| I want to... | Use this namespace |
|---|---|
| Create/update/delete an agent runtime | `aws bedrock-agentcore-control` |
| List or describe agent runtimes | `aws bedrock-agentcore-control` |
| Create/manage MCP gateways | `aws bedrock-agentcore-control` |
| Create/manage Cedar policies | `aws bedrock-agentcore-control` |
| Manage credentials and identities | `aws bedrock-agentcore-control` |
| Tag/untag resources | `aws bedrock-agentcore-control` |
| **Invoke a running agent** | `aws bedrock-agentcore` |

### Service Appropriateness

AgentCore is the right choice for:

| Use Case | Why AgentCore |
|----------|--------------|
| Deploying AI agents that interact with AWS | Purpose-built: session isolation, identity, tool gateway |
| Long-running agentic tasks (minutes to hours) | Up to 8-hour sessions, unlike Lambda's 15-minute limit |
| Agents that need tool access with credential management | MCP Gateway handles credential injection |
| Multi-turn agent conversations with state | Session state preserved within microVM |

AgentCore is NOT the right choice for:

| Use Case | Better Alternative |
|----------|--------------------|
| Simple API proxy to Bedrock | API Gateway + Bedrock direct |
| Batch inference (no agent loop) | Bedrock Batch Inference |
| Non-agent LLM workloads (chatbot, summarization) | Bedrock API directly |
| Short-lived stateless functions | Lambda |

### Regional Availability

Amazon Bedrock AgentCore is available in 9 AWS regions:

- US East (N. Virginia), US East (Ohio), US West (Oregon)
- Asia Pacific (Mumbai, Singapore, Sydney, Tokyo)
- Europe (Frankfurt, Ireland)

## Best Practices

- **Container Images**: Source from private ECR only — never use public registries for agent containers
- **IAM**: Separate execution role from agent runtime role; scope both to least privilege
- **VPC Placement**: Deploy agent runtimes in private subnets; use VPC endpoints for AWS API access
- **Credentials**: Never hardcode API keys in container images or environment variables — use AgentCore Identity
- **Session Timeouts**: Configure appropriate session timeouts to prevent runaway sessions and cost overruns
- **Logging**: Enable CloudWatch logging for all agent runtimes; set retention policies
- **Tags**: Apply governance tags (Environment, Owner, CostCenter) to all AgentCore resources
- **Gateway**: Use MCP Gateway for external API calls instead of direct HTTP from agents
- **Policies**: Use Cedar policies for tool call authorization in staging and production
- **Monitoring**: Set up CloudWatch alarms for agent health, session duration, and error rates
- **Cost**: Monitor session concurrency — each session runs a microVM; unused sessions still incur cost

## Related Skills

- Bedrock — Foundation model access and guardrails
- IAM — Create execution and agent runtime roles
- ECR — Host agent container images
- VPC — Configure private subnets and security groups for agent runtimes
- CloudWatch — Monitor agent runtime metrics and logs
- Secrets Manager — Store API keys and credentials referenced by AgentCore Identity
