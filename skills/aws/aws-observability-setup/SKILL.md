---
name: aws-observability-setup
description: Standard patterns for CloudWatch, CloudTrail, Config, logging, and alerting
version: 1.0.0
category: aws
agents: [aws-coworker-core, aws-coworker-planner, aws-coworker-observability-cost]
tools: [Read, Bash]
---

# AWS Observability Setup

## Purpose

This skill provides standardized patterns for setting up AWS observability including CloudWatch metrics, logs, and alarms; CloudTrail for audit; AWS Config for compliance; and Security Hub for security posture.

## When to Use

- Setting up monitoring for new resources
- Establishing baseline observability
- Creating alerting strategies
- Implementing compliance logging
- Reviewing observability gaps

## When NOT to Use

- Application-level monitoring (APM tools)
- Third-party monitoring integration
- Custom metrics development (specific to apps)

---

## Observability Stack

| Component | Purpose |
|-----------|---------|
| **CloudWatch Metrics** | Performance and operational data |
| **CloudWatch Logs** | Centralized log management |
| **CloudWatch Alarms** | Alerting and automated actions |
| **CloudTrail** | API activity audit trail |
| **AWS Config** | Configuration compliance |
| **VPC Flow Logs** | Network traffic analysis |
| **Security Hub** | Security posture aggregation |

---

## CloudWatch Metrics

### Standard Metrics to Monitor

#### EC2

| Metric | Alarm Threshold | Period |
|--------|-----------------|--------|
| CPUUtilization | > 80% | 5 min |
| StatusCheckFailed | > 0 | 1 min |
| NetworkIn/Out | Anomaly detection | 5 min |
| EBSReadOps/WriteOps | Baseline + 2 std dev | 5 min |

#### RDS

| Metric | Alarm Threshold | Period |
|--------|-----------------|--------|
| CPUUtilization | > 80% | 5 min |
| FreeStorageSpace | < 20% of total | 5 min |
| DatabaseConnections | > 80% of max | 5 min |
| ReadLatency/WriteLatency | > baseline | 5 min |
| FreeableMemory | < 10% | 5 min |

#### Lambda

| Metric | Alarm Threshold | Period |
|--------|-----------------|--------|
| Errors | > 5% of invocations | 5 min |
| Duration | > 80% of timeout | 5 min |
| Throttles | > 0 | 5 min |
| ConcurrentExecutions | > 80% of limit | 5 min |

#### ALB/NLB

| Metric | Alarm Threshold | Period |
|--------|-----------------|--------|
| HTTPCode_ELB_5XX_Count | > 10 | 5 min |
| HTTPCode_Target_5XX_Count | > 10 | 5 min |
| TargetResponseTime | > 1 second | 5 min |
| UnHealthyHostCount | > 0 | 1 min |

### Enabling Detailed Monitoring

```bash
# Enable detailed monitoring for EC2
aws ec2 monitor-instances \
  --instance-ids i-xxxxxxxxx \
  --profile {profile} \
  --region {region}

# Enable enhanced monitoring for RDS
aws rds modify-db-instance \
  --db-instance-identifier {db-id} \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::{account}:role/rds-monitoring-role \
  --profile {profile} \
  --region {region}
```

---

## CloudWatch Alarms

### Alarm Configuration Pattern

```yaml
# CloudFormation example
Resources:
  CPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "${AWS::StackName}-cpu-high"
      AlarmDescription: CPU utilization exceeds 80%
      MetricName: CPUUtilization
      Namespace: AWS/EC2
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: InstanceId
          Value: !Ref MyInstance
      AlarmActions:
        - !Ref AlertSNSTopic
      OKActions:
        - !Ref AlertSNSTopic
```

### CLI Alarm Creation

```bash
# Create CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "prod-web-cpu-high" \
  --alarm-description "CPU utilization exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value=i-xxxxxxxxx \
  --alarm-actions arn:aws:sns:{region}:{account}:alerts \
  --profile {profile} \
  --region {region}
```

### Alarm Naming Convention

```
{env}-{service}-{metric}-{condition}

Examples:
- prod-web-cpu-high
- dev-rds-storage-low
- staging-lambda-errors-high
```

---

## CloudWatch Logs

### Log Group Configuration

```bash
# Create log group with retention
aws logs create-log-group \
  --log-group-name /aws/lambda/{function-name} \
  --profile {profile} \
  --region {region}

aws logs put-retention-policy \
  --log-group-name /aws/lambda/{function-name} \
  --retention-in-days 30 \
  --profile {profile} \
  --region {region}
```

### Standard Log Groups

| Service | Log Group Pattern | Retention |
|---------|------------------|-----------|
| Lambda | /aws/lambda/{function} | 30 days |
| ECS | /ecs/{cluster}/{service} | 30 days |
| API Gateway | /aws/api-gateway/{api} | 30 days |
| VPC Flow Logs | /vpc/flow-logs/{vpc} | 90 days |
| Application | /app/{service}/{env} | 30-90 days |

### Log Insights Queries

```sql
-- Error analysis
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

-- Lambda cold starts
fields @timestamp, @message, @duration
| filter @type = "REPORT" and @initDuration > 0
| sort @timestamp desc

-- Request latency percentiles
stats avg(@duration), pct(@duration, 95), pct(@duration, 99) by bin(5m)
```

---

## CloudTrail

### Trail Configuration

```bash
# Create organization trail
aws cloudtrail create-trail \
  --name org-audit-trail \
  --s3-bucket-name {audit-bucket} \
  --is-organization-trail \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --include-global-service-events \
  --profile {profile} \
  --region {region}

# Start logging
aws cloudtrail start-logging \
  --name org-audit-trail \
  --profile {profile} \
  --region {region}
```

### CloudTrail Best Practices

```markdown
## CloudTrail Configuration Checklist

- [ ] Multi-region trail enabled
- [ ] Log file validation enabled
- [ ] S3 bucket with encryption
- [ ] S3 bucket with access logging
- [ ] CloudWatch Logs integration
- [ ] Global service events included
- [ ] Data events for critical S3/Lambda (optional)
```

### CloudTrail Event Analysis

```bash
# Query recent events via CLI
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --start-time 2024-01-01T00:00:00Z \
  --profile {profile} \
  --region {region}
```

---

## VPC Flow Logs

### Enable Flow Logs

```bash
# Create log group
aws logs create-log-group \
  --log-group-name /vpc/flow-logs/{vpc-id} \
  --profile {profile} \
  --region {region}

# Create flow log
aws ec2 create-flow-logs \
  --resource-ids vpc-xxxxxxxxx \
  --resource-type VPC \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs/{vpc-id} \
  --deliver-logs-permission-arn arn:aws:iam::{account}:role/flow-logs-role \
  --profile {profile} \
  --region {region}
```

### Flow Log Analysis

```sql
-- Rejected traffic
fields @timestamp, srcAddr, dstAddr, dstPort, action
| filter action = "REJECT"
| sort @timestamp desc
| limit 100

-- Top talkers by bytes
stats sum(bytes) as totalBytes by srcAddr
| sort totalBytes desc
| limit 20
```

---

## AWS Config

### Enable Config Recording

```bash
# Create config recorder
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::{account}:role/config-role \
  --recording-group allSupported=true,includeGlobalResourceTypes=true \
  --profile {profile} \
  --region {region}

# Create delivery channel
aws configservice put-delivery-channel \
  --delivery-channel name=default,s3BucketName={config-bucket} \
  --profile {profile} \
  --region {region}

# Start recording
aws configservice start-configuration-recorder \
  --configuration-recorder-name default \
  --profile {profile} \
  --region {region}
```

### Essential Config Rules

| Rule | Purpose |
|------|---------|
| s3-bucket-public-read-prohibited | No public S3 buckets |
| encrypted-volumes | EBS encryption required |
| rds-storage-encrypted | RDS encryption required |
| ec2-instance-managed-by-ssm | Systems Manager coverage |
| vpc-flow-logs-enabled | Flow logs required |

---

## Security Hub

### Enable Security Hub

```bash
# Enable Security Hub
aws securityhub enable-security-hub \
  --enable-default-standards \
  --profile {profile} \
  --region {region}

# Enable specific standards
aws securityhub batch-enable-standards \
  --standards-subscription-requests \
    StandardsArn=arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0 \
  --profile {profile} \
  --region {region}
```

### Security Hub Findings

```bash
# Get critical findings
aws securityhub get-findings \
  --filters '{"SeverityLabel":[{"Value":"CRITICAL","Comparison":"EQUALS"}]}' \
  --profile {profile} \
  --region {region}
```

---

## Dashboard Template

### Production Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "EC2 CPU Utilization",
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-xxx"]
        ],
        "period": 300
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "ALB Request Count",
        "metrics": [
          ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/xxx"]
        ],
        "period": 60
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "RDS Connections",
        "metrics": [
          ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "xxx"]
        ],
        "period": 60
      }
    }
  ]
}
```

---

## Observability Checklist

```markdown
## Full Observability Checklist

### CloudWatch
- [ ] Detailed monitoring enabled
- [ ] Custom metrics where needed
- [ ] Alarms for critical metrics
- [ ] Dashboard created
- [ ] Anomaly detection configured

### Logging
- [ ] CloudWatch Logs for all services
- [ ] Retention policies set
- [ ] Log Insights queries saved
- [ ] Subscription filters for alerts

### Audit
- [ ] CloudTrail enabled (multi-region)
- [ ] Log file validation on
- [ ] S3 bucket secure
- [ ] CloudWatch Logs integration

### Network
- [ ] VPC Flow Logs enabled
- [ ] Traffic analysis configured
- [ ] Rejected traffic monitored

### Security
- [ ] Security Hub enabled
- [ ] Findings reviewed regularly
- [ ] Standards enabled (CIS, etc.)

### Compliance
- [ ] AWS Config recording
- [ ] Config rules deployed
- [ ] Non-compliance alerts
```

---

## Related Skills

- `aws-cli-playbook` — CLI patterns for setup
- `aws-well-architected` — Operational excellence pillar
- `aws-governance-guardrails` — Compliance requirements
- `aws-cost-optimizer` — Cost of observability
