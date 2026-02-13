# ECS — MVA Baseline

## Overview

Amazon Elastic Container Service (ECS) is a container orchestration service for running Docker containers on AWS using Fargate (serverless) or EC2 launch types.

**MNA (Minimum Needed Architecture):** A cluster, a task definition with at least one container, and an IAM task execution role.
**MVA (Minimum Viable Architecture):** Least-privilege task roles, no hardcoded secrets, Fargate launch type, CloudWatch logging, health checks, governance tagging, and appropriate resource limits.

**Service Appropriateness Warning:** ECS is sometimes chosen when a simpler or more appropriate service would suffice. Before evaluating ECS MVA, the orchestrator MUST check whether ECS is the right service for the use case (see Service Appropriateness Check in SKILL.md). Common misuses include: simple event-driven functions (use Lambda), simple web applications with minimal configuration (use App Runner), workloads requiring Kubernetes-specific features like CRDs or operators (use EKS), batch processing with simple scheduling (use Lambda + EventBridge or AWS Batch).

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Task execution role follows least privilege (no `*` actions or `*` resources) | Critical | Overly permissive task roles are the most common ECS security failure |
| Security | No hardcoded secrets in task definitions (use Secrets Manager or SSM Parameter Store references) | Critical | Secrets in task definitions are visible in the console and API |
| Security | Container images from trusted registries only (ECR or verified public registries) | High | Untrusted images can contain malware or vulnerabilities |
| Operational Excellence | Governance tags applied to cluster, service, and task definitions | High | Untagged resources violate governance compliance |
| Performance Efficiency | Task definition CPU and memory explicitly set (not relying on defaults) | Medium | Undefined resource limits cause unpredictable behaviour |

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
| Operational Excellence | CloudWatch log driver configured (awslogs) with log group and retention | Medium | Container logs must be captured for debugging |
| Reliability | Container health checks defined in task definition | Medium | Enables ECS to detect and replace unhealthy containers |
| Security | Fargate launch type preferred over EC2 (unless EC2-specific features required) | Low | Fargate reduces operational overhead and attack surface |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Tasks run in private subnets (with NAT gateway for outbound) | High | Containers should not be directly accessible from the internet |
| Reliability | Service deployment circuit breaker enabled | High | Prevents failed deployments from draining healthy tasks |
| Reliability | Service auto-scaling configured (target tracking or step scaling) | High | Staging should validate scaling behaviour before production |
| Performance Efficiency | Container Insights enabled for cluster | Medium | Provides container-level metrics for performance analysis |
| Operational Excellence | Service discovery configured (Cloud Map or ALB) | Medium | Services should be discoverable without hardcoded endpoints |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | ECS Exec disabled (unless explicitly required for debugging) | High | Exec access to production containers is a security risk |
| Reliability | Multi-AZ task placement (spread across AZs) | High | Single-AZ placement is a single point of failure |
| Reliability | Deployment circuit breaker with automatic rollback enabled | High | Failed deployments must automatically roll back in production |
| Reliability | Minimum healthy percent >= 100% during deployments | Medium | Ensures no capacity loss during rolling updates |
| Cost Optimization | Fargate Spot considered for fault-tolerant workloads | Low | Up to 70% savings for interruptible tasks |
| Operational Excellence | CloudWatch alarms for service health (running count, CPU, memory) | High | Production must have monitoring and alerting |
| Operational Excellence | Deployed via IaC (CDK/Terraform/CloudFormation), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | Task execution role least privilege | R | R | R | R | Critical |
| Security | No hardcoded secrets | R | R | R | R | Critical |
| Security | Trusted container images | R | R | R | R | High |
| Security | Fargate preferred | - | R | R | R | Low |
| Security | Tasks in private subnets | - | - | R | R | High |
| Security | ECS Exec disabled | - | - | - | R | High |
| Reliability | Container health checks | - | R | R | R | Medium |
| Reliability | Deployment circuit breaker | - | - | R | R | High |
| Reliability | Service auto-scaling | - | - | R | R | High |
| Reliability | Multi-AZ task placement | - | - | - | R | High |
| Reliability | Circuit breaker with rollback | - | - | - | R | High |
| Reliability | Min healthy percent >= 100% | - | - | - | R | Medium |
| Performance Efficiency | CPU/memory explicitly set | R | R | R | R | Medium |
| Performance Efficiency | Container Insights | - | - | R | R | Medium |
| Cost Optimization | Fargate Spot evaluated | - | - | - | R | Low |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | CloudWatch logging with retention | - | R | R | R | Medium |
| Operational Excellence | Service discovery | - | - | R | R | Medium |
| Operational Excellence | CloudWatch alarms | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Task Execution Role Permissions

- **Check command:** `aws ecs describe-task-definition --task-definition {task_def} --query 'taskDefinition.executionRoleArn'` then `aws iam list-attached-role-policies --role-name {role_name}`
- **Gap condition:** Role has AdministratorAccess or policies with `Action: "*"`
- **Severity:** Critical
- **Remediation:** Create a scoped policy with only `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `logs:CreateLogStream`, `logs:PutLogEvents`, and any secrets access needed
- **Remediation description:** Restricts the task execution role to only the permissions required for container runtime

### Hardcoded Secrets in Task Definition

- **Check command:** `aws ecs describe-task-definition --task-definition {task_def} --query 'taskDefinition.containerDefinitions[*].environment'`
- **Gap condition:** Environment variables contain values resembling credentials (passwords, API keys, connection strings)
- **Severity:** Critical
- **Remediation:** Move secrets to Secrets Manager or SSM Parameter Store and reference via `secrets` block in container definition
- **Remediation description:** Removes credentials from task definition and references them securely at runtime

### CloudWatch Logging

- **Check command:** `aws ecs describe-task-definition --task-definition {task_def} --query 'taskDefinition.containerDefinitions[*].logConfiguration'`
- **Gap condition:** `logConfiguration` is null or `logDriver` is not `awslogs`
- **Severity:** Medium
- **Remediation:** Update task definition with `logConfiguration: { logDriver: "awslogs", options: { "awslogs-group": "/ecs/{service}", "awslogs-region": "{region}", "awslogs-stream-prefix": "ecs" } }`
- **Remediation description:** Configures CloudWatch log driver for container output capture

### Container Health Check

- **Check command:** `aws ecs describe-task-definition --task-definition {task_def} --query 'taskDefinition.containerDefinitions[*].healthCheck'`
- **Gap condition:** `healthCheck` is null
- **Severity:** Medium
- **Remediation:** Add health check to container definition: `healthCheck: { command: ["CMD-SHELL", "curl -f http://localhost/ || exit 1"], interval: 30, timeout: 5, retries: 3 }`
- **Remediation description:** Enables ECS to detect and replace unhealthy containers

### Deployment Circuit Breaker

- **Check command:** `aws ecs describe-services --cluster {cluster} --services {service} --query 'services[0].deploymentConfiguration.deploymentCircuitBreaker'`
- **Gap condition:** `enable` is `false` or circuit breaker config is missing
- **Severity:** High (staging/prod)
- **Remediation:** `aws ecs update-service --cluster {cluster} --service {service} --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true}"`
- **Remediation description:** Enables circuit breaker to stop and roll back failed deployments

### Service Auto-Scaling

- **Check command:** `aws application-autoscaling describe-scalable-targets --service-namespace ecs --resource-ids service/{cluster}/{service}`
- **Gap condition:** No scalable target registered for the service
- **Severity:** High (staging/prod)
- **Remediation:** Register scalable target and create scaling policy
- **Remediation description:** Enables automatic scaling based on CPU, memory, or custom metrics

### Governance Tags

- **Check command:** `aws ecs list-tags-for-resource --resource-arn {cluster_or_service_arn}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws ecs tag-resource --resource-arn {arn} --tags key=...,value=...`
- **Remediation description:** Applies required governance tags for compliance

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- Fargate eliminates the need to manage EC2 instances but has higher per-task cost — evaluate for each workload
- ECS Exec is powerful for debugging but must be disabled in production unless there's an explicit need
- Task definition revisions are immutable — changes create new revisions, old ones remain for rollback
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/ecs.md` for CLI command reference
