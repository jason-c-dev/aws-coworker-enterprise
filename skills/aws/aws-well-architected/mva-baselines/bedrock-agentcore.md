# Bedrock AgentCore — MVA Baseline

## Overview

Amazon Bedrock AgentCore is a managed runtime for deploying AI agents as isolated, stateful sessions in Firecracker microVMs. This baseline defines the Minimum Viable Architecture for AgentCore deployments across environment tiers.

**MNA (Minimum Needed Architecture):** What's technically required for an AgentCore agent to run — an agent runtime definition, a container image (ECR), an IAM execution role, and network configuration (VPC, subnets, security group).

**MVA (Minimum Viable Architecture):** What the Well-Architected Framework says you should have — scoped IAM roles, no hardcoded credentials, logging, governance tags, private subnet placement, session timeout configuration, and monitoring.

### Service Appropriateness

AgentCore is the right choice for deploying AI agents that interact with AWS services, run long-lived sessions (up to 8 hours), and need managed identity/credential handling.

**Common misuses:**
- Simple API proxies to Bedrock → use API Gateway + Bedrock directly
- Batch inference without an agent loop → use Bedrock Batch Inference
- Non-agent LLM workloads (chatbot, summarization) → use Bedrock API directly
- Short-lived stateless functions → use Lambda

---

## Common (All Environments)

Items required regardless of environment tier. These are the absolute minimum for any deployment.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | IAM execution role follows least privilege (no `*` actions/resources) | Critical | Wildcard permissions on the execution role expose the entire account |
| Security | No hardcoded credentials or API keys in container image or environment variables | Critical | Credentials in images are extractable and cannot be rotated without redeployment |
| Security | Container image sourced from private ECR (not public registries) | High | Public images are untrusted supply chain — no control over contents or updates |
| Security | Agent runtime role is separate from execution role | High | Role separation limits blast radius — execution role pulls images, agent role acts at runtime |
| Security | Bedrock model access configured via IAM (not API keys) | Critical | Agent must use IAM-based Bedrock access (e.g. `CLAUDE_CODE_USE_BEDROCK=1`), not hardcoded API keys. The agent runtime role must have `bedrock:InvokeModel` scoped to required foundation models. This is the positive counterpart to "no hardcoded credentials" — without it, the agent cannot invoke models at all. |
| Reliability | Required Bedrock foundation models enabled and accessible | High | The agent's required models (orchestrator model + sub-agent models) must be enabled in the account and region. For AWS Coworker: Opus (orchestrator), Sonnet (mutations), Haiku (discovery). Missing models cause silent failures or degraded capability. |
| Operational Excellence | Governance tags applied to agent runtime, IAM roles, and VPC resources (Environment, Owner, CostCenter) | High | Tags are required for cost allocation, ownership tracking, and governance compliance |
| Performance Efficiency | Agent runtime resource limits explicitly configured (memory, timeout) | Medium | Unconfigured resource limits lead to unpredictable costs and potential resource exhaustion |

---

## Sandbox

Additional items beyond Common for sandbox environments. Typically empty — sandbox is intentionally loose.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| — | No additional items | — | Sandbox prioritizes experimentation |

---

## Development

Additional items beyond Common for development environments.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Operational Excellence | CloudWatch logging enabled with log retention policy | Medium | Logs are essential for debugging agent behavior; retention prevents unbounded log storage costs |
| Reliability | Session timeout configured (prevent runaway sessions) | Medium | Uncapped sessions consume resources and cost indefinitely |
| Security | Agent runtime placed in VPC (private subnets) | Medium | Private subnets prevent direct internet exposure of agent sessions |

---

## Staging

Additional items beyond Development for staging environments. These items are enforcement-gated: critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Separate IAM roles for discovery vs mutation agents | High | Role separation ensures read-only agents cannot accidentally mutate resources |
| Security | VPC endpoints for Bedrock API access (no public internet for API calls) | High | VPC endpoints keep Bedrock API traffic on the AWS backbone — no internet traversal |
| Reliability | Agent runtime health monitoring configured | High | Without health monitoring, failed agents run silently until session timeout |
| Cost Optimization | Session concurrency limits configured | Medium | Unbounded concurrency can cause unexpected cost spikes from parallel microVMs |
| Operational Excellence | Model invocation logging enabled | Medium | Invocation logs provide audit trail for what the agent sent to and received from models |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory when enforcement is `enforce` — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Cedar policies enforced for tool call interception (when available) | High | Cedar policies provide fine-grained control over which tools agents can invoke and under what conditions |
| Security | Customer-managed KMS encryption for stored data (logs, memory) | High | Customer-managed keys provide key rotation control and the ability to revoke access |
| Reliability | Multi-AZ deployment (subnets span multiple AZs) | High | Single-AZ failure takes down all agent sessions if subnets are in one AZ |
| Reliability | Automatic recovery / restart on failure | Medium | Agents should recover from transient failures without manual intervention |
| Cost Optimization | Provisioned throughput evaluated vs on-demand for Bedrock model access | Medium | Steady-state agent workloads may be cheaper with provisioned throughput |
| Operational Excellence | CloudWatch alarms for agent health, session duration, latency, error rate | High | Alarms enable proactive response to degradation before users are impacted |
| Operational Excellence | Deployed via IaC (CDK/CloudFormation), not direct CLI | High | Production infrastructure must be reproducible, version-controlled, and auditable |

---

## Full MVA Summary (Production = Superset)

This table shows ALL MVA items for production, which is the complete superset. Lower tiers inherit from Common upward.

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | IAM execution role follows least privilege | R | R | R | R | Critical |
| Security | No hardcoded credentials in image/env vars | R | R | R | R | Critical |
| Security | Bedrock model access configured via IAM (not API keys) | R | R | R | R | Critical |
| Security | Container image from private ECR | R | R | R | R | High |
| Security | Separate execution role from agent role | R | R | R | R | High |
| Security | Agent runtime in VPC (private subnets) | - | R | R | R | Medium |
| Security | Separate IAM roles for discovery vs mutation | - | - | R | R | High |
| Security | VPC endpoints for Bedrock API access | - | - | R | R | High |
| Security | Cedar policies for tool call interception | - | - | - | R | High |
| Security | Customer-managed KMS encryption | - | - | - | R | High |
| Operational Excellence | Governance tags applied | R | R | R | R | High |
| Operational Excellence | CloudWatch logging with retention | - | R | R | R | Medium |
| Operational Excellence | Model invocation logging enabled | - | - | R | R | Medium |
| Operational Excellence | CloudWatch alarms configured | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |
| Reliability | Required Bedrock foundation models enabled | R | R | R | R | High |
| Reliability | Session timeout configured | - | R | R | R | Medium |
| Reliability | Agent runtime health monitoring | - | - | R | R | High |
| Reliability | Multi-AZ deployment | - | - | - | R | High |
| Reliability | Automatic recovery on failure | - | - | - | R | Medium |
| Performance Efficiency | Resource limits configured (memory, timeout) | R | R | R | R | Medium |
| Cost Optimization | Session concurrency limits | - | - | R | R | Medium |
| Cost Optimization | Provisioned throughput evaluated | - | - | - | R | Medium |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

For each MVA item, how to detect a gap programmatically:

### IAM Execution Role — Least Privilege

- **Check command:** `aws iam get-role --role-name {execution-role}` then `aws iam list-attached-role-policies --role-name {execution-role}` and `aws iam get-role-policy --role-name {execution-role} --policy-name {policy}`
- **Gap condition:** Any policy statement contains `"Action": "*"` or `"Resource": "*"` without conditions
- **Severity:** Critical
- **Remediation:** Replace wildcard permissions with scoped permissions for ECR pull, CloudWatch Logs write, and Secrets Manager read
- **Remediation description:** Scope IAM policy actions to specific services and resources the execution role needs

### No Hardcoded Credentials

- **Check command:** Inspect container image environment variables via `aws ecr batch-get-image` + manifest inspection; check `aws bedrock-agentcore get-agent-runtime` for environment variable configuration
- **Gap condition:** Environment variables contain values matching credential patterns (AWS_ACCESS_KEY_ID, API keys, tokens)
- **Severity:** Critical
- **Remediation:** Remove credentials from image/env vars; use AgentCore Identity (`aws bedrock-agentcore create-api-key-credential`) or IAM roles
- **Remediation description:** Migrate credentials to AgentCore Identity or Secrets Manager references

### Bedrock Model Access Configured via IAM

- **Check command:** Inspect container environment for `CLAUDE_CODE_USE_BEDROCK=1` (or equivalent IAM-based model access flag) via Dockerfile or runtime config; verify agent runtime role has `bedrock:InvokeModel` permission via `aws iam get-role-policy --role-name {agent-role} --policy-name {policy}` → check for `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` actions scoped to required foundation models
- **Gap condition:** Container does not set `CLAUDE_CODE_USE_BEDROCK=1` (or equivalent); OR agent runtime role lacks `bedrock:InvokeModel` permission; OR `bedrock:InvokeModel` is not scoped to specific model ARNs
- **Severity:** Critical
- **Remediation:** Set `CLAUDE_CODE_USE_BEDROCK=1` in container environment variables and ensure agent runtime role includes `bedrock:InvokeModel` scoped to `arn:aws:bedrock:{region}::foundation-model/anthropic.*` (or more specifically to required models)
- **Remediation description:** Configure IAM-based Bedrock model access — the agent must use IAM roles, not API keys, to invoke foundation models

### Required Bedrock Foundation Models Enabled

- **Check command:** `aws bedrock list-foundation-models --by-provider Anthropic --profile {profile} --region {region}` → verify required models appear and have `modelLifecycle.status` of `ACTIVE`; for AWS Coworker: check Opus (orchestrator), Sonnet (mutations), Haiku (discovery)
- **Gap condition:** Required models not enabled or not available in the target region. For AWS Coworker: Opus missing means no orchestrator; Sonnet missing means no mutation agents; Haiku missing means no discovery agents
- **Severity:** High
- **Remediation:** Enable required models via Bedrock console Model Access page; if models are not available in region, consider region change
- **Remediation description:** Enable all required Bedrock foundation models in the target account and region

### Container Image from Private ECR

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → inspect `agentRuntimeArtifact.containerConfiguration.containerUri`
- **Gap condition:** Container URI does not match pattern `{account-id}.dkr.ecr.{region}.amazonaws.com/{repo}:{tag}`
- **Severity:** High
- **Remediation:** Push image to private ECR and update agent runtime configuration
- **Remediation description:** Move container image to account-owned ECR repository

### Separate Execution and Agent Roles

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → compare execution role ARN with any runtime role configuration
- **Gap condition:** Same IAM role ARN used for both execution and agent runtime purposes
- **Severity:** High
- **Remediation:** Create separate roles: execution role for image pull/logging, agent role for runtime AWS actions
- **Remediation description:** Split into dedicated execution and agent runtime IAM roles

### Governance Tags

- **Check command:** `aws bedrock-agentcore list-tags-for-resource --resource-arn {arn}`
- **Gap condition:** Missing any of: Environment, Owner, CostCenter tags
- **Severity:** High
- **Remediation:** `aws bedrock-agentcore tag-resource --resource-arn {arn} --tags key=Environment,value={env} key=Owner,value={owner} key=CostCenter,value={cc}`
- **Remediation description:** Apply required governance tags to the AgentCore resource

### CloudWatch Logging

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → inspect logging configuration
- **Gap condition:** Logging configuration is absent or log group does not exist
- **Severity:** Medium
- **Remediation:** Update agent runtime with logging configuration pointing to a CloudWatch log group with retention policy
- **Remediation description:** Enable CloudWatch logging and set log retention period

### Session Timeout

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → inspect session configuration
- **Gap condition:** Session timeout not configured or set to maximum (8 hours) without justification
- **Severity:** Medium
- **Remediation:** Configure appropriate session timeout based on expected task duration
- **Remediation description:** Set session timeout to match expected workload duration plus buffer

### VPC Placement (Private Subnets)

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → inspect `networkConfiguration.vpcConfiguration.subnetIds`; then `aws ec2 describe-subnets --subnet-ids {ids}` → check route tables for internet gateway routes
- **Gap condition:** Subnets have route to internet gateway (public subnets) or network mode is not VPC
- **Severity:** Medium
- **Remediation:** Move agent runtime to private subnets with NAT gateway for outbound access
- **Remediation description:** Reconfigure agent runtime to use private subnets without direct internet access

### VPC Endpoints for Bedrock API

- **Check command:** `aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values={vpc-id}" "Name=service-name,Values=com.amazonaws.{region}.bedrock-runtime"`
- **Gap condition:** No VPC endpoint found for bedrock-runtime service in the agent's VPC
- **Severity:** High
- **Remediation:** `aws ec2 create-vpc-endpoint --vpc-id {vpc-id} --service-name com.amazonaws.{region}.bedrock-runtime --vpc-endpoint-type Interface --subnet-ids {subnet-ids} --security-group-ids {sg-ids}`
- **Remediation description:** Create interface VPC endpoint for Bedrock Runtime to keep API traffic off the public internet

### Multi-AZ Deployment

- **Check command:** `aws bedrock-agentcore get-agent-runtime --agent-runtime-id {id}` → get subnet IDs; `aws ec2 describe-subnets --subnet-ids {ids}` → check AvailabilityZone values
- **Gap condition:** All subnets are in the same availability zone
- **Severity:** High
- **Remediation:** Add subnets from at least one additional AZ to the agent runtime network configuration
- **Remediation description:** Spread subnets across multiple availability zones for fault tolerance

### CloudWatch Alarms

- **Check command:** `aws cloudwatch describe-alarms --alarm-name-prefix agentcore-{runtime-name}`
- **Gap condition:** No alarms exist for agent runtime health, error rate, or session duration
- **Severity:** High
- **Remediation:** Create CloudWatch alarms for key metrics: agent errors, session duration exceeding threshold, health check failures
- **Remediation description:** Configure alarms for proactive monitoring of agent runtime health

### Deployed via IaC

- **Check command:** `aws bedrock-agentcore list-tags-for-resource --resource-arn {arn}` → check for CreatedBy tag; `aws cloudformation list-stack-resources` → search for resource
- **Gap condition:** Resource not managed by CloudFormation/CDK stack (no CreatedBy tag, not in any stack)
- **Severity:** High
- **Remediation:** Import resource into CDK/CloudFormation stack or redeploy via IaC
- **Remediation description:** Bring resource under IaC management for reproducibility and audit trail

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- Cedar policy enforcement (Production tier) is documented conceptually — implementation detail is Part 5 of the blog series
- AgentCore is a 2025 service — CLI commands and resource patterns may evolve; this baseline covers the stable, documented subset
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
