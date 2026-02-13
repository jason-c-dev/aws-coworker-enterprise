# VPC — MVA Baseline

## Overview

Amazon Virtual Private Cloud (VPC) provides isolated network environments for AWS resources. VPCs are foundational infrastructure — most AWS services (EC2, RDS, ECS, EKS, Lambda) deploy into VPCs.

**MNA (Minimum Needed Architecture):** A VPC with a CIDR block and at least one subnet.
**MVA (Minimum Viable Architecture):** Public and private subnet separation, flow logs, restricted NACLs, NAT gateway for private subnet outbound, governance tagging, and appropriate routing.

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | No 0.0.0.0/0 ingress in security groups except for explicitly required public-facing ports (80, 443) | Critical | Wide-open ingress is the most common VPC security failure |
| Security | Default security group blocks all inbound traffic (no rules added to default SG) | High | The default SG is often accidentally permissive |
| Operational Excellence | Governance tags applied to all VPC resources (VPC, subnets, route tables, IGW, NAT GW, NACLs, security groups) | High | Untagged network resources violate governance compliance |
| Operational Excellence | DNS resolution and DNS hostnames enabled | Medium | Required for most AWS service integrations |

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
| Security | Separate public and private subnets (databases and internal services in private subnets) | Medium | Prevents unnecessary exposure of backend resources |
| Security | NAT gateway for private subnet outbound access | Medium | Private subnets need outbound access without being directly reachable |
| Reliability | Subnets in at least 2 Availability Zones | Medium | Basic redundancy for development workloads |
| Operational Excellence | Non-default VPC for application workloads (avoid relying on default VPC) | Low | Default VPCs have permissive defaults not suitable for structured work |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | VPC flow logs enabled (to CloudWatch Logs or S3) | High | Staging should validate logging before production |
| Security | VPC endpoints for S3 and DynamoDB (gateway endpoints — no cost) | High | Data should not traverse the public internet when accessing AWS services |
| Security | Network ACLs restrict inter-subnet traffic where appropriate | Medium | Defence in depth beyond security groups |
| Reliability | Subnets in at least 3 Availability Zones | High | Staging should mirror production AZ distribution |
| Operational Excellence | Route tables explicitly associated with subnets (not relying on main route table) | Medium | Explicit routing prevents accidental exposure |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | VPC endpoints for all frequently accessed AWS services (interface endpoints for SSM, ECR, CloudWatch, etc.) | High | Production traffic should stay on the AWS backbone |
| Security | No internet gateway routes in private subnet route tables | High | Private subnets must not have direct internet paths |
| Reliability | Redundant NAT gateways (one per AZ) | High | Single NAT gateway is a single point of failure |
| Reliability | Transit Gateway or VPC peering for multi-VPC connectivity | Medium | Production environments often span multiple VPCs |
| Cost Optimization | NAT gateway usage monitored (consider alternatives for high-volume traffic) | Medium | NAT gateways charge per GB processed — can be significant |
| Operational Excellence | VPC flow logs with retention policy configured | High | Production logs must have defined lifecycle |
| Operational Excellence | CloudWatch alarms for NAT gateway metrics (ErrorPortAllocation, PacketsDropCount) | High | Production must have monitoring and alerting |
| Operational Excellence | Deployed via IaC (CDK/Terraform/CloudFormation), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | No 0.0.0.0/0 ingress (except 80/443 where required) | R | R | R | R | Critical |
| Security | Default SG blocks all inbound | R | R | R | R | High |
| Security | Public/private subnet separation | - | R | R | R | Medium |
| Security | NAT gateway for private subnets | - | R | R | R | Medium |
| Security | VPC flow logs | - | - | R | R | High |
| Security | VPC endpoints (S3/DynamoDB gateway) | - | - | R | R | High |
| Security | VPC endpoints (interface — SSM, ECR, CW) | - | - | - | R | High |
| Security | No IGW routes in private subnets | - | - | - | R | High |
| Security | NACLs restrict inter-subnet traffic | - | - | R | R | Medium |
| Reliability | Subnets in 2+ AZs | - | R | R | R | Medium |
| Reliability | Subnets in 3+ AZs | - | - | R | R | High |
| Reliability | Redundant NAT gateways (per AZ) | - | - | - | R | High |
| Reliability | Transit Gateway / VPC peering | - | - | - | R | Medium |
| Cost Optimization | NAT gateway usage monitored | - | - | - | R | Medium |
| Operational Excellence | Governance tags (all VPC resources) | R | R | R | R | High |
| Operational Excellence | DNS resolution and hostnames | R | R | R | R | Medium |
| Operational Excellence | Non-default VPC | - | R | R | R | Low |
| Operational Excellence | Explicit route table associations | - | - | R | R | Medium |
| Operational Excellence | Flow logs with retention policy | - | - | - | R | High |
| Operational Excellence | CloudWatch alarms (NAT GW metrics) | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Security Group Ingress (0.0.0.0/0)

- **Check command:** `aws ec2 describe-security-groups --filters "Name=vpc-id,Values={vpc_id}" --query 'SecurityGroups[*].{GroupId:GroupId,GroupName:GroupName,IpPermissions:IpPermissions}'`
- **Gap condition:** Any ingress rule allows `0.0.0.0/0` or `::/0` on ports other than 80 or 443
- **Severity:** Critical
- **Remediation:** `aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port {port} --cidr 0.0.0.0/0`
- **Remediation description:** Removes wide-open ingress rules and restricts to known CIDRs

### Default Security Group

- **Check command:** `aws ec2 describe-security-groups --filters "Name=vpc-id,Values={vpc_id}" "Name=group-name,Values=default" --query 'SecurityGroups[0].IpPermissions'`
- **Gap condition:** Default security group has any inbound rules
- **Severity:** High
- **Remediation:** `aws ec2 revoke-security-group-ingress --group-id {default_sg_id} --protocol all --port all --source-group {default_sg_id}`
- **Remediation description:** Removes all rules from the default security group so it blocks all inbound traffic

### VPC Flow Logs

- **Check command:** `aws ec2 describe-flow-logs --filter "Name=resource-id,Values={vpc_id}"`
- **Gap condition:** No flow logs found for the VPC
- **Severity:** High (staging/prod)
- **Remediation:** `aws ec2 create-flow-logs --resource-type VPC --resource-ids {vpc_id} --traffic-type ALL --log-destination-type cloud-watch-logs --log-group-name /aws/vpc/flowlogs/{vpc_id} --deliver-logs-permission-arn {flow_log_role_arn}`
- **Remediation description:** Enables VPC flow logs for network traffic visibility and security analysis

### VPC Endpoints (Gateway — S3/DynamoDB)

- **Check command:** `aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values={vpc_id}" --query 'VpcEndpoints[*].{ServiceName:ServiceName,VpcEndpointType:VpcEndpointType}'`
- **Gap condition:** No gateway endpoints for `com.amazonaws.{region}.s3` or `com.amazonaws.{region}.dynamodb`
- **Severity:** High (staging/prod)
- **Remediation:** `aws ec2 create-vpc-endpoint --vpc-id {vpc_id} --service-name com.amazonaws.{region}.s3 --route-table-ids {rtb_ids}`
- **Remediation description:** Creates a gateway VPC endpoint so S3 traffic stays on the AWS backbone

### Subnet AZ Distribution

- **Check command:** `aws ec2 describe-subnets --filters "Name=vpc-id,Values={vpc_id}" --query 'Subnets[*].AvailabilityZone' | sort -u | wc -l`
- **Gap condition:** Fewer than required AZs for the environment tier (2 for dev, 3 for staging/prod)
- **Severity:** Medium (dev), High (staging/prod)
- **Remediation:** Create additional subnets in missing AZs
- **Remediation description:** Distributes subnets across Availability Zones for redundancy

### NAT Gateway Redundancy

- **Check command:** `aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values={vpc_id}" "Name=state,Values=available" --query 'NatGateways[*].{SubnetId:SubnetId,NatGatewayId:NatGatewayId}'`
- **Gap condition:** Fewer NAT gateways than AZs with private subnets (production requires one per AZ)
- **Severity:** High (production only)
- **Remediation:** `aws ec2 create-nat-gateway --subnet-id {public_subnet_in_az} --allocation-id {eip_alloc_id}`
- **Remediation description:** Creates redundant NAT gateways to eliminate single point of failure

### Governance Tags

- **Check command:** `aws ec2 describe-vpcs --vpc-ids {vpc_id} --query 'Vpcs[0].Tags'`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws ec2 create-tags --resources {vpc_id} --tags Key=...,Value=...`
- **Remediation description:** Applies required governance tags for compliance

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- Gateway VPC endpoints (S3, DynamoDB) are free — there is no reason to skip them
- Interface VPC endpoints have an hourly cost — evaluate which services justify the cost
- Default VPCs should not be used for structured workloads; they exist for experimentation only
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/vpc.md` for CLI command reference
