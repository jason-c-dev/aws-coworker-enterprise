# Lambda — MVA Baseline

## Overview

AWS Lambda is a serverless compute service that runs code in response to events without provisioning or managing servers.

**MNA (Minimum Needed Architecture):** A function with a handler, runtime, and an IAM execution role.
**MVA (Minimum Viable Architecture):** Least-privilege execution role, no hardcoded secrets, appropriate timeout and memory, dead-letter queue, governance tagging, and monitoring.

**Service Appropriateness Warning:** Lambda is sometimes chosen when a different service would be more appropriate. Before evaluating Lambda MVA, the orchestrator MUST check whether Lambda is the right service for the use case (see Service Appropriateness Check in SKILL.md). Common misuses include: long-running processes exceeding 15 minutes (use ECS/Fargate or Step Functions), complex multi-step orchestration (use Step Functions), high-throughput stream processing with ordering guarantees (use Kinesis Data Analytics or ECS), applications requiring persistent connections (use ECS/Fargate or App Runner).

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | IAM execution role follows least privilege (no `*` actions or `*` resources) | Critical | Overly permissive roles are the most common Lambda security failure |
| Security | No hardcoded secrets in code or environment variables (use Secrets Manager or SSM Parameter Store) | Critical | Credentials in code or plaintext env vars are exposed in console and logs |
| Operational Excellence | Governance tags applied (7 core tags) | High | Untagged resources violate governance compliance |
| Performance Efficiency | Timeout configured appropriately (not default 3 seconds) | High | Default timeout causes unexpected failures for most real workloads |
| Performance Efficiency | Memory sized for workload (not default 128MB) | Medium | Under-provisioned memory increases duration and cost; over-provisioned wastes money |

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
| Reliability | Dead-letter queue (DLQ) or on-failure destination configured | Medium | Captures failed invocations for debugging and retry |
| Operational Excellence | CloudWatch log group with retention policy set (not indefinite) | Medium | Prevents unbounded log storage costs |
| Operational Excellence | X-Ray tracing enabled | Low | Distributed tracing for debugging invocation chains |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Environment variables encrypted with KMS key (not default Lambda encryption) | High | Sensitive configuration must use customer-managed encryption |
| Security | Function URL authentication type is not NONE (if function URL exists) | High | Unauthenticated function URLs expose the function to the internet |
| Reliability | Reserved concurrency configured | High | Prevents a single function from consuming all account concurrency |
| Performance Efficiency | Memory and timeout tuned based on testing (not defaults) | Medium | Staging should validate production-representative configuration |
| Operational Excellence | Code signing configured (if org requires it) | Medium | Ensures only trusted code is deployed |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | VPC configuration for functions accessing private resources | High | Functions accessing databases or internal services must be in the VPC |
| Reliability | Provisioned concurrency for latency-sensitive functions | Medium | Eliminates cold starts for user-facing workloads |
| Reliability | Version aliases configured for traffic shifting (canary/linear deployment) | High | Production deployments must support gradual rollout and instant rollback |
| Cost Optimization | Arm64 architecture evaluated for cost savings | Low | Graviton2 provides up to 34% better price-performance |
| Operational Excellence | CloudWatch alarms for Errors, Throttles, Duration, and IteratorAge | High | Production must have monitoring and alerting |
| Operational Excellence | CloudWatch Logs Insights queries or metric filters for error patterns | Medium | Proactive error detection and operational visibility |
| Operational Excellence | Deployed via IaC (SAM/CDK/Terraform/Serverless Framework), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | Least-privilege execution role | R | R | R | R | Critical |
| Security | No hardcoded secrets | R | R | R | R | Critical |
| Security | Env vars encrypted with KMS | - | - | R | R | High |
| Security | Function URL auth type not NONE | - | - | R | R | High |
| Security | VPC configuration for private access | - | - | - | R | High |
| Reliability | Dead-letter queue / on-failure destination | - | R | R | R | Medium |
| Reliability | Reserved concurrency | - | - | R | R | High |
| Reliability | Provisioned concurrency (latency-sensitive) | - | - | - | R | Medium |
| Reliability | Version aliases for traffic shifting | - | - | - | R | High |
| Performance Efficiency | Timeout configured (not 3s default) | R | R | R | R | High |
| Performance Efficiency | Memory sized for workload | R | R | R | R | Medium |
| Performance Efficiency | Memory and timeout tuned from testing | - | - | R | R | Medium |
| Cost Optimization | Arm64 architecture evaluated | - | - | - | R | Low |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | CloudWatch log retention policy | - | R | R | R | Medium |
| Operational Excellence | X-Ray tracing | - | R | R | R | Low |
| Operational Excellence | Code signing | - | - | R | R | Medium |
| Operational Excellence | CloudWatch alarms | - | - | - | R | High |
| Operational Excellence | Logs Insights / metric filters | - | - | - | R | Medium |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Least-Privilege Execution Role

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'Role'` then `aws iam get-role-policy --role-name {role_name} --policy-name {policy_name}` or `aws iam list-attached-role-policies --role-name {role_name}`
- **Gap condition:** Any policy statement uses `Action: "*"` or `Resource: "*"`
- **Severity:** Critical
- **Remediation:** Create a scoped policy with only required actions and specific resource ARNs
- **Remediation description:** Restricts the execution role to only the permissions the function actually needs

### No Hardcoded Secrets

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'Environment.Variables'`
- **Gap condition:** Environment variables contain values that look like credentials (API keys, passwords, connection strings with embedded credentials)
- **Severity:** Critical
- **Remediation:** Store secrets in Secrets Manager or SSM Parameter Store and reference them at runtime
- **Remediation description:** Removes credentials from plaintext environment variables

### Dead-Letter Queue

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'DeadLetterConfig'`
- **Gap condition:** `DeadLetterConfig` is null or `TargetArn` is empty
- **Severity:** Medium
- **Remediation:** `aws lambda update-function-configuration --function-name {function_name} --dead-letter-config TargetArn={sqs_or_sns_arn}`
- **Remediation description:** Configures a dead-letter queue to capture failed asynchronous invocations

### Timeout Configuration

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'Timeout'`
- **Gap condition:** Returns `3` (default)
- **Severity:** High
- **Remediation:** `aws lambda update-function-configuration --function-name {function_name} --timeout {seconds}`
- **Remediation description:** Sets an appropriate timeout for the function's workload

### Memory Configuration

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'MemorySize'`
- **Gap condition:** Returns `128` (default) without justification
- **Severity:** Medium
- **Remediation:** `aws lambda update-function-configuration --function-name {function_name} --memory-size {mb}`
- **Remediation description:** Sets memory to an appropriate size (also affects CPU allocation)

### Environment Variable Encryption

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'KMSKeyArn'`
- **Gap condition:** Returns null (using default Lambda service key instead of customer-managed KMS key)
- **Severity:** High (staging/prod)
- **Remediation:** `aws lambda update-function-configuration --function-name {function_name} --kms-key-arn {kms_key_arn}`
- **Remediation description:** Encrypts environment variables with a customer-managed KMS key

### Reserved Concurrency

- **Check command:** `aws lambda get-function-concurrency --function-name {function_name}`
- **Gap condition:** Returns empty (no reserved concurrency set)
- **Severity:** High (staging/prod)
- **Remediation:** `aws lambda put-function-concurrency --function-name {function_name} --reserved-concurrent-executions {count}`
- **Remediation description:** Reserves concurrency to prevent account-wide throttling from a single function

### CloudWatch Log Retention

- **Check command:** `aws logs describe-log-groups --log-group-name-prefix /aws/lambda/{function_name} --query 'logGroups[0].retentionInDays'`
- **Gap condition:** Returns null (indefinite retention)
- **Severity:** Medium
- **Remediation:** `aws logs put-retention-policy --log-group-name /aws/lambda/{function_name} --retention-in-days {days}`
- **Remediation description:** Sets log retention to prevent unbounded storage costs

### X-Ray Tracing

- **Check command:** `aws lambda get-function-configuration --function-name {function_name} --query 'TracingConfig.Mode'`
- **Gap condition:** Returns `PassThrough` instead of `Active`
- **Severity:** Low (dev), Medium (staging/prod)
- **Remediation:** `aws lambda update-function-configuration --function-name {function_name} --tracing-config Mode=Active`
- **Remediation description:** Enables active X-Ray tracing for distributed tracing

### Governance Tags

- **Check command:** `aws lambda list-tags --resource {function_arn}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws lambda tag-resource --resource {function_arn} --tags Key1=Value1,Key2=Value2`
- **Remediation description:** Applies required governance tags for compliance

### CloudWatch Alarms

- **Check command:** `aws cloudwatch describe-alarms --alarm-name-prefix {function_name}`
- **Gap condition:** No alarms exist for Errors, Throttles, Duration, or IteratorAge (for stream-based triggers)
- **Severity:** High (production only)
- **Remediation:** Create CloudWatch alarms using Lambda metrics
- **Remediation description:** Alerts on error rates, throttling, slow execution, and stream processing lag

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- Lambda memory allocation also controls CPU — doubling memory doubles CPU (and halves duration for CPU-bound functions)
- Lambda cold starts are affected by VPC configuration, memory size, and runtime choice
- Provisioned concurrency has a cost even when idle — only appropriate for latency-sensitive production functions
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/lambda.md` for CLI command reference
