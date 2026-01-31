# Network Security Policies

## Overview
Network security policies enforce secure architecture patterns, prevent unauthorized traffic flows, and ensure compliance with network segmentation standards. These policies protect data in transit and prevent network-based attacks. **Enforcement Level: MANDATORY** - Network violations are immediately remediated by automated guardrails.

## Mandatory Rules (NEVER Violate)

### Rule: No Public RDS/Database Instances
- **Severity:** CRITICAL
- **Description:** RDS instances, Aurora clusters, and other databases must never have `PubliclyAccessible` set to true or be exposed to 0.0.0.0/0 in security groups.
- **Rationale:** Public databases are prime targets for automated attacks, credential brute-forcing, and data exfiltration. Database credentials are high-value targets.
- **Validation:**
  - `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier, PubliclyAccessible]'`
  - `aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId, IpPermissions[?FromPort==3306 || FromPort==5432]]'`
  - Check for rules allowing 0.0.0.0/0 to database ports
- **Remediation:**
  - Set `PubliclyAccessible` to false: `aws rds modify-db-instance --db-instance-identifier <id> --no-publicly-accessible`
  - Remove security group rules: `aws ec2 revoke-security-group-ingress --group-id <sg-id> --protocol tcp --port <port> --cidr 0.0.0.0/0`
  - Use private RDS endpoints within VPC only

### Rule: No Security Group Rules Allowing 0.0.0.0/0 for SSH/RDP
- **Severity:** CRITICAL
- **Description:** Security group ingress rules must never allow SSH (port 22), RDP (port 3389), or management ports from 0.0.0.0/0 (internet).
- **Rationale:** Public SSH/RDP access enables automated brute-force attacks, credential compromise, and lateral movement.
- **Validation:**
  - `aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId, IpPermissions[?(FromPort==22 || FromPort==3389) && (IpRanges[0].CidrIp==`0.0.0.0/0`)]]'`
  - Check for rules with CidrIp "0.0.0.0/0" and ports 22, 3389
  - Check for IPv6 rules with `::/0`
- **Remediation:**
  - Remove internet-facing SSH/RDP rules
  - Implement bastion host architecture for administrative access
  - Use Systems Manager Session Manager instead of direct SSH/RDP
  - Restrict to VPN CIDR or specific IP ranges

### Rule: Enable Network ACLs on All Subnets
- **Severity:** CRITICAL
- **Description:** All subnets must have explicit Network ACLs (NACLs) configured beyond default ACLs. Critical subnets must have explicit deny rules for suspicious traffic.
- **Rationale:** NACLs provide stateless filtering and can block attacks before reaching security groups.
- **Validation:**
  - `aws ec2 describe-network-acls --query 'NetworkAcls[*].[NetworkAclId, IsDefault]'`
  - Verify custom NACLs exist for production subnets
  - Check for explicit deny rules: `aws ec2 describe-network-acls --query 'NetworkAcls[*].Entries[?RuleAction==`Deny`]'`
- **Remediation:**
  - Create custom NACL: `aws ec2 create-network-acl --vpc-id <vpc-id>`
  - Associate with subnet: `aws ec2 associate-network-acl --network-acl-id <nacl-id> --subnet-id <subnet-id>`
  - Add deny rules for known attack patterns

### Rule: VPC Flow Logs Must Be Enabled on All VPCs
- **Severity:** CRITICAL
- **Description:** VPC Flow Logs must be enabled for all production VPCs and sent to CloudWatch Logs or S3 with retention ≥90 days.
- **Rationale:** Flow logs enable detection of suspicious traffic patterns, unauthorized access attempts, and compliance auditing.
- **Validation:**
  - `aws ec2 describe-flow-logs --filter 'Name=resource-type,Values=VPC' --query 'FlowLogs[*].[ResourceId, FlowLogStatus]'`
  - Verify S3 or CloudWatch destination exists
  - Check retention: `aws logs describe-log-groups --query 'logGroups[*].[logGroupName, retentionInDays]'`
- **Remediation:**
  - Create CloudWatch Logs group: `aws logs create-log-group --log-group-name /aws/vpc/flowlogs`
  - Enable Flow Logs: `aws ec2 create-flow-logs --resource-type VPC --resource-ids <vpc-id> --traffic-type ALL --log-destination-type cloud-watch-logs --log-group-name <log-group>`
  - Set retention: `aws logs put-retention-policy --log-group-name <group> --retention-in-days 90`

### Rule: NLB/ALB Must Not Allow Unencrypted HTTP to Internet
- **Severity:** CRITICAL
- **Description:** Network Load Balancers and Application Load Balancers must not accept unencrypted HTTP traffic from the internet on production listeners.
- **Rationale:** Unencrypted HTTP exposes user credentials, session tokens, and sensitive data to interception attacks (MITM).
- **Validation:**
  - `aws elbv2 describe-listeners --load-balancer-arn <arn> --query 'Listeners[?Protocol==`HTTP`].Port'`
  - Check for port 80 listeners with internet-facing flag
  - Verify HTTPS/SSL listeners exist on port 443
- **Remediation:**
  - Redirect HTTP to HTTPS: `aws elbv2 modify-listener --listener-arn <arn> --default-actions Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}`
  - Enable HTTPS listener: `aws elbv2 create-listener --load-balancer-arn <arn> --protocol HTTPS --port 443 --certificates CertificateArn=<cert-arn>`
  - Remove HTTP listener for production

### Rule: All Network Resources Must Be in Private Subnets (Except ALB/NLB)
- **Severity:** CRITICAL
- **Description:** EC2 instances, databases, and application servers must be deployed in private subnets without direct internet routes. Only load balancers and NAT gateways should be in public subnets.
- **Rationale:** Private subnets prevent direct internet access and limit attack surface. Applications communicate through load balancers.
- **Validation:**
  - `aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId, SubnetId]'`
  - Check subnet route tables: `aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc-id> | grep -i "0.0.0.0/0"`
  - Verify instances are not in public subnets with direct IGW routes
- **Remediation:**
  - Launch instances in private subnets
  - Remove internet routes from application subnets
  - Use NAT gateway for outbound internet access if needed
  - Use Systems Manager Session Manager or bastion for SSH access

### Rule: Enable VPC Endpoint Gateway for AWS Services
- **Severity:** CRITICAL
- **Description:** S3 and DynamoDB access from private subnets must use VPC Gateway Endpoints to avoid internet routing.
- **Rationale:** VPC endpoints prevent data from transiting through NAT gateways/internet, reducing costs and improving security.
- **Validation:**
  - `aws ec2 describe-vpc-endpoints --filters Name=service-name,Values=com.amazonaws.region.s3`
  - Verify endpoint policies restrict access appropriately
  - Check route tables for S3 endpoint routes: `aws ec2 describe-route-tables --query 'RouteTables[*].Routes[?DestinationPrefixListId!=null]'`
- **Remediation:**
  - Create S3 Gateway Endpoint: `aws ec2 create-vpc-endpoint --vpc-id <vpc-id> --service-name com.amazonaws.region.s3`
  - Associate with route tables: `aws ec2 create-vpc-endpoint-route-table-association --vpc-endpoint-id <endpoint-id> --route-table-id <rtb-id>`
  - Update S3 bucket policies to restrict VPC endpoint access

## Recommended Practices (SHOULD Follow)

### Practice: Use AWS Secrets Manager for RDS Database Credentials
- **Severity:** HIGH
- **Description:** RDS database passwords must be stored in Secrets Manager with automatic rotation enabled, not hardcoded or stored in application configuration.
- **Rationale:** Automatic rotation limits window of exposure if credentials are compromised.
- **Exceptions:** Development and test databases with non-sensitive data may use temporary credentials.

### Practice: Implement Security Group Chaining
- **Severity:** HIGH
- **Description:** Create and use security group IDs instead of IP ranges in ingress rules where possible for applications within the VPC.
- **Rationale:** Security group references are more maintainable and enable dynamic IP updates without rule changes.

### Practice: Enable GuardDuty on All Accounts
- **Severity:** HIGH
- **Description:** AWS GuardDuty must be enabled on all AWS accounts to detect anomalous network behavior and API misuse.
- **Rationale:** GuardDuty uses machine learning to identify threats that manual inspection would miss.

### Practice: Use AWS WAF for Public Applications
- **Severity:** HIGH
- **Description:** All internet-facing ALBs/CloudFront distributions must have AWS WAF rules enabled to protect against OWASP Top 10 vulnerabilities.
- **Rationale:** WAF rules prevent common web attacks (SQL injection, XSS, etc.) at the perimeter.

## Environment-Specific Rules

### Production
- VPC Flow Logs must be enabled and retained for 90+ days
- All databases must be in private subnets with encryption in transit
- NLB/ALB must use HTTPS with minimum TLS 1.2
- GuardDuty must be enabled and monitoring enabled
- Security group rules must be reviewed monthly
- VPC Peering must require explicit approval

### Non-Production (Dev/Test)
- VPC Flow Logs recommended but may have shorter retention (30 days minimum)
- HTTP allowed for internal testing only (must use HTTPS for any external access)
- Developers may create temporary security groups with documented justification
- GuardDuty enabled but findings may be reviewed less frequently

## Validation Commands

```bash
# Find public RDS instances
aws rds describe-db-instances --query 'DBInstances[?PubliclyAccessible==true].[DBInstanceIdentifier, Engine]'

# Find security groups with public SSH access
aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId, GroupName, IpPermissions[?(FromPort==22 && IpRanges[0].CidrIp==`0.0.0.0/0`)]]'

# Check VPC Flow Logs status
aws ec2 describe-flow-logs --filter 'Name=resource-type,Values=VPC' --query 'FlowLogs[*].[ResourceId, FlowLogStatus, LogGroupName]' --output table

# Find instances in public subnets
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId, SubnetId, PublicIpAddress]' --output table

# Check load balancer listeners for HTTP
aws elbv2 describe-listeners --load-balancer-arn <arn> --query 'Listeners[?Protocol==`HTTP`].[ListenerArn, Port, Protocol]'

# Verify VPC Gateway Endpoints
aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[*].[VpcEndpointId, ServiceName, State]' --output table

# List all security group rules allowing 0.0.0.0/0
aws ec2 describe-security-group-rules --filters Name=cidr,Values=0.0.0.0/0 Name=group-owner-id,Values=<account-id> --query 'SecurityGroupRules[*].[GroupId, FromPort, ToPort, IpProtocol]'
```

## Common Violations

| Violation | Severity | Remediation |
|-----------|----------|-------------|
| RDS instance publicly accessible | CRITICAL | Modify to non-public, restrict SG to private CIDR |
| Security group allows 0.0.0.0/0 SSH | CRITICAL | Remove rule, use bastion host or Session Manager |
| VPC Flow Logs disabled | CRITICAL | Enable Flow Logs to CloudWatch/S3, set retention |
| Instance in public subnet with public IP | CRITICAL | Move to private subnet, use NAT gateway for egress |
| HTTP listener on production ALB | CRITICAL | Redirect to HTTPS, remove port 80 listener |
| RDS password in code/config | CRITICAL | Store in Secrets Manager, rotate immediately |
| No custom NACL on production subnets | HIGH | Create and associate custom NACL with rules |
| Missing S3 VPC Gateway Endpoint | HIGH | Create endpoint, update route tables |
| GuardDuty disabled | HIGH | Enable GuardDuty on all production accounts |
| Database security group too permissive | HIGH | Restrict to application servers only, use SG reference |

## Exception Process

Network security exceptions are rarely granted due to high risk. Requirements:

1. **Justification Document**
   - Business requirement that cannot be met otherwise
   - Specific security risk assessment
   - Compensating technical controls (WAF rules, IDS, etc.)
   - Duration (maximum 7 days for CRITICAL violations)

2. **Multi-Level Approval**
   - Security architect review
   - Network team approval
   - VP of Security sign-off (required for any exception)

3. **Mandatory Monitoring**
   - CloudWatch alarms on affected resources
   - Real-time alerting to security team
   - Daily review and status reporting
   - Automatic remediation if conditions change

4. **Documentation**
   - Exception logged with timestamp and approver
   - Daily email confirmation exception is still valid
   - Automatic expiration and alert before deadline

Network exceptions expire automatically and are NOT renewed - remediation is required.
