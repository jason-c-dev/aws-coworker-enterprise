# VPC CLI Reference

## Overview
Amazon Virtual Private Cloud (VPC) enables you to launch AWS resources in an isolated network environment. Use these commands to create and manage VPCs, subnets, route tables, internet gateways, NAT gateways, network ACLs, and VPC peering connections.

## Discovery Commands (Read-Only)

```bash
# List all VPCs
aws ec2 describe-vpcs

# Get details about a specific VPC
aws ec2 describe-vpcs --vpc-ids vpc-12345678

# List subnets
aws ec2 describe-subnets

# List subnets in a VPC
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-12345678"

# Get subnet details
aws ec2 describe-subnets --subnet-ids subnet-12345678

# List route tables
aws ec2 describe-route-tables

# Get route table details
aws ec2 describe-route-tables --route-table-ids rtb-12345678

# List internet gateways
aws ec2 describe-internet-gateways

# List NAT gateways
aws ec2 describe-nat-gateways

# Get NAT gateway details
aws ec2 describe-nat-gateways --nat-gateway-ids natgw-12345678

# List network ACLs
aws ec2 describe-network-acls

# Get NACL details
aws ec2 describe-network-acls --network-acl-ids acl-12345678

# List VPC peering connections
aws ec2 describe-vpc-peering-connections

# List VPC endpoints
aws ec2 describe-vpc-endpoints

# List VPC endpoint services
aws ec2 describe-vpc-endpoint-services

# Get VPC flow logs
aws ec2 describe-flow-logs

# List VPC attributes
aws ec2 describe-vpc-attribute --vpc-id vpc-12345678 --attribute enableDnsHostnames

# List available CIDR blocks for VPC
aws ec2 describe-vpc-cidr-block-associations --filters "Name=vpc-id,Values=vpc-12345678"

# List network interfaces in VPC
aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=vpc-12345678"

# List security groups in VPC
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-12345678"

# Get VPC association details
aws ec2 describe-vpc-peering-connections --filters "Name=requester-vpc-info.vpc-id,Values=vpc-12345678"
```

## Common Operations

```bash
# Create a VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=my-vpc}]'

# Create a subnet
aws ec2 create-subnet \
  --vpc-id vpc-12345678 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet}]'

# Create internet gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=my-igw}]'

# Attach internet gateway to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-12345678 \
  --vpc-id vpc-12345678

# Create route table
aws ec2 create-route-table \
  --vpc-id vpc-12345678 \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]'

# Associate subnet with route table
aws ec2 associate-route-table \
  --subnet-id subnet-12345678 \
  --route-table-id rtb-12345678

# Add route to internet gateway
aws ec2 create-route \
  --route-table-id rtb-12345678 \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-12345678

# Allocate elastic IP for NAT gateway
aws ec2 allocate-address --domain vpc

# Create NAT gateway in public subnet
aws ec2 create-nat-gateway \
  --subnet-id subnet-12345678 \
  --allocation-id eipalloc-12345678 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=my-nat}]'

# Add route to NAT gateway from private subnet
aws ec2 create-route \
  --route-table-id rtb-private \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id natgw-12345678

# Create VPC peering connection
aws ec2 create-vpc-peering-connection \
  --vpc-id vpc-12345678 \
  --peer-vpc-id vpc-87654321

# Accept VPC peering connection (from peer account)
aws ec2 accept-vpc-peering-connection \
  --vpc-peering-connection-id pcx-12345678

# Add route for peered VPC
aws ec2 create-route \
  --route-table-id rtb-12345678 \
  --destination-cidr-block 10.1.0.0/16 \
  --vpc-peering-connection-id pcx-12345678

# Enable DNS hostnames for VPC
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-12345678 \
  --enable-dns-hostnames

# Enable DNS support for VPC
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-12345678 \
  --enable-dns-support

# Create VPC endpoint for S3 (gateway type)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345678

# Create VPC endpoint for DynamoDB
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids rtb-12345678

# Enable VPC Flow Logs (to CloudWatch)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-12345678 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs

# Add CIDR block to VPC (for expansion)
aws ec2 associate-vpc-cidr-block \
  --vpc-id vpc-12345678 \
  --cidr-block 10.1.0.0/16
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete subnet
aws ec2 delete-subnet --subnet-id subnet-12345678

# ⚠️ Delete route table (must be unassociated from subnets first)
aws ec2 delete-route-table --route-table-id rtb-12345678

# ⚠️ Delete route from route table
aws ec2 delete-route \
  --route-table-id rtb-12345678 \
  --destination-cidr-block 10.1.0.0/16

# ⚠️ Detach internet gateway from VPC
aws ec2 detach-internet-gateway \
  --internet-gateway-id igw-12345678 \
  --vpc-id vpc-12345678

# ⚠️ Delete internet gateway
aws ec2 delete-internet-gateway --internet-gateway-id igw-12345678

# ⚠️ Delete NAT gateway
aws ec2 delete-nat-gateway --nat-gateway-id natgw-12345678

# ⚠️ Release elastic IP
aws ec2 release-address --allocation-id eipalloc-12345678

# ⚠️ Delete network ACL (must be unassociated from subnets first)
aws ec2 delete-network-acl --network-acl-id acl-12345678

# ⚠️ Delete network ACL rule
aws ec2 delete-network-acl-entry \
  --network-acl-id acl-12345678 \
  --rule-number 100 \
  --egress

# ⚠️ Disassociate route table from subnet
aws ec2 disassociate-route-table --association-id rtbassoc-12345678

# ⚠️ Reject VPC peering connection
aws ec2 reject-vpc-peering-connection \
  --vpc-peering-connection-id pcx-12345678

# ⚠️ Delete VPC peering connection
aws ec2 delete-vpc-peering-connection \
  --vpc-peering-connection-id pcx-12345678

# ⚠️ Delete VPC endpoint
aws ec2 delete-vpc-endpoints --vpc-endpoint-ids vpce-12345678

# ⚠️ Delete VPC (must delete all subnets, gateways, and endpoints first)
aws ec2 delete-vpc --vpc-id vpc-12345678

# ⚠️ Disassociate CIDR block from VPC
aws ec2 disassociate-vpc-cidr-block \
  --association-id vpc-cidr-assoc-12345678

# ⚠️ Delete VPC Flow Logs
aws ec2 delete-flow-logs --flow-log-ids fl-12345678

# ⚠️ Unassociate subnet from route table
aws ec2 disassociate-route-table \
  --association-id rtbassoc-87654321
```

## Best Practices

- **CIDR Planning**: Plan IP address space carefully; use RFC 1918 ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- **Subnet Strategy**: Use /24 subnets for easy management; reserve .0 for networking infrastructure
- **AZ Distribution**: Spread subnets across availability zones for high availability
- **Public vs Private**: Only expose necessary services publicly; keep databases and app servers private
- **NAT Gateway**: Use NAT gateways (not instances) for reliable outbound internet access from private subnets
- **Route Table Management**: Create separate route tables for public and private subnets
- **VPC Endpoints**: Use endpoints for AWS services (S3, DynamoDB) to avoid internet routing
- **Flow Logs**: Enable VPC Flow Logs for security analysis and troubleshooting
- **DNS Configuration**: Enable DNS hostnames and support for easier instance naming
- **VPC Peering**: Use peering for cross-VPC communication instead of internet routing
- **NACL Rules**: Keep NACLs simple; rely on security groups for most access control
- **VPC Size**: Design for growth; use /16 VPC CIDR to allow subnet expansion

## Related Skills

- EC2 Instance Management - Launch instances in VPC subnets
- Security Groups - Control inbound/outbound traffic at instance level
- IAM - Manage VPC API access and resource permissions
- CloudWatch - Monitor VPC flow logs and connectivity
- Route 53 - Manage DNS for VPC resources
- VPN/Direct Connect - Secure connections from on-premises to VPC
