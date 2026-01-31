# EC2 CLI Reference

## Overview
Amazon Elastic Compute Cloud (EC2) provides scalable computing capacity in the cloud. Use these commands to launch and manage virtual machine instances, create and manage AMIs, configure security groups, manage key pairs, and handle volumes and snapshots.

## Discovery Commands (Read-Only)

```bash
# List all EC2 instances
aws ec2 describe-instances

# List running instances only
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"

# List instances with specific tag
aws ec2 describe-instances --filters "Name=tag:Environment,Values=production"

# Get detailed info about a specific instance
aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# List all AMIs (custom images only)
aws ec2 describe-images --owners self

# List all available security groups
aws ec2 describe-security-groups

# Get security group details
aws ec2 describe-security-groups --group-ids sg-12345678

# List inbound rules for a security group
aws ec2 describe-security-groups --group-ids sg-12345678 --query 'SecurityGroups[0].IpPermissions'

# List key pairs
aws ec2 describe-key-pairs

# Get details about a specific key pair
aws ec2 describe-key-pairs --key-names my-key-pair

# List volumes
aws ec2 describe-volumes

# Get volume details
aws ec2 describe-volumes --volume-ids vol-12345678

# List volume snapshots
aws ec2 describe-snapshots --owner-ids self

# Get snapshot details
aws ec2 describe-snapshots --snapshot-ids snap-12345678

# List network interfaces
aws ec2 describe-network-interfaces

# List availability zones
aws ec2 describe-availability-zones

# Get EC2 instance status (system and instance checks)
aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0

# List elastic IPs
aws ec2 describe-addresses

# Get instance console output (for troubleshooting)
aws ec2 get-console-output --instance-id i-1234567890abcdef0
```

## Common Operations

```bash
# Launch an EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --security-group-ids sg-12345678 \
  --subnet-id subnet-12345678 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=my-instance}]' \
  --iam-instance-profile Name=my-instance-profile

# Launch instance with user data script
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name my-key-pair \
  --user-data file://bootstrap.sh

# Create a new security group
aws ec2 create-security-group \
  --group-name web-sg \
  --description "Security group for web servers" \
  --vpc-id vpc-12345678

# Add inbound rule (HTTP)
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Add inbound rule (HTTPS)
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Add inbound rule (SSH from specific IP)
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.0/24

# Create key pair and save to file
aws ec2 create-key-pair --key-name my-key-pair --query 'KeyMaterial' --output text > my-key-pair.pem
chmod 600 my-key-pair.pem

# Create EBS volume
aws ec2 create-volume \
  --availability-zone us-east-1a \
  --size 100 \
  --volume-type gp3 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=data-volume}]'

# Attach volume to instance
aws ec2 attach-volume \
  --volume-id vol-12345678 \
  --instance-id i-1234567890abcdef0 \
  --device /dev/sdf

# Create snapshot from volume
aws ec2 create-snapshot \
  --volume-id vol-12345678 \
  --description "Backup of data volume"

# Create image from instance (AMI)
aws ec2 create-image \
  --instance-id i-1234567890abcdef0 \
  --name "my-custom-ami" \
  --description "Custom AMI from instance"

# Create elastic IP
aws ec2 allocate-address --domain vpc

# Associate elastic IP with instance
aws ec2 associate-address \
  --allocation-id eipalloc-12345678 \
  --instance-id i-1234567890abcdef0

# Tag an instance
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=Environment,Value=production Key=Owner,Value=admin
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Start a stopped instance
aws ec2 start-instances --instance-ids i-1234567890abcdef0

# ⚠️ Stop a running instance (charges still apply for volume storage)
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# ⚠️ Reboot an instance (forceful, may cause data loss if filesystem not synced)
aws ec2 reboot-instances --instance-ids i-1234567890abcdef0

# ⚠️ Terminate an instance (delete permanently - cannot be undone)
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# ⚠️ Force terminate instance
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0 --force

# ⚠️ Modify instance type (requires stop - downtime required)
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --instance-type "{\"Value\": \"t3.large\"}"

# ⚠️ Remove inbound rule from security group
aws ec2 revoke-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# ⚠️ Delete security group (must remove from all instances first)
aws ec2 delete-security-group --group-id sg-12345678

# ⚠️ Delete key pair
aws ec2 delete-key-pair --key-name my-key-pair

# ⚠️ Delete volume (must detach first, cannot recover)
aws ec2 delete-volume --volume-id vol-12345678

# ⚠️ Delete snapshot
aws ec2 delete-snapshot --snapshot-id snap-12345678

# ⚠️ Deregister AMI (removes the image)
aws ec2 deregister-image --image-id ami-12345678

# ⚠️ Delete tags from instance
aws ec2 delete-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=Environment Key=Owner

# ⚠️ Release elastic IP
aws ec2 release-address --allocation-id eipalloc-12345678

# ⚠️ Disassociate elastic IP
aws ec2 disassociate-address --association-id eipassoc-12345678

# ⚠️ Detach volume from instance (requires stop)
aws ec2 detach-volume --volume-id vol-12345678

# ⚠️ Enable termination protection (prevent accidental deletion)
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --disable-api-termination
```

## Best Practices

- **Instance Types**: Choose right-sized instances; use burstable types (t3) for variable workloads
- **Termination Protection**: Enable for production instances to prevent accidental deletion
- **Security Groups**: Use least privilege; restrict SSH/RDP to known IPs, not 0.0.0.0/0
- **Key Pair Management**: Store key pairs securely; rotate regularly; never commit to git
- **IAM Instance Profiles**: Use roles instead of storing AWS credentials on instances
- **EBS Volume Types**: Use gp3 for general workloads, io2 for databases, st1 for big data
- **Snapshots**: Take regular snapshots before major changes; schedule automated snapshots
- **Public vs Private**: Use private subnets for databases; expose only necessary services
- **Monitoring**: Set up CloudWatch alarms for CPU, memory, disk, and network usage
- **Patch Management**: Regularly apply OS and application patches; use Systems Manager Patch Manager
- **VPC Configuration**: Place instances in VPCs with proper subnet isolation and NACLs

## Related Skills

- VPC Networking - Configure VPCs, subnets, and routing
- IAM Roles - Attach roles to instances for permissions
- ELB/ALB - Load balance traffic across instances
- Auto Scaling - Automatically scale instance count
- CloudWatch - Monitor instance performance
- Systems Manager - Patch and configure instances
