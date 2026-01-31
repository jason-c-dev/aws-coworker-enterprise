# RDS CLI Reference

## Overview
Amazon Relational Database Service (RDS) provides managed relational databases. Use these commands to create and manage DB instances, manage snapshots and backups, configure parameter groups, manage security groups, handle automatic failover, and manage read replicas.

## Discovery Commands (Read-Only)

```bash
# List all RDS instances
aws rds describe-db-instances

# Get details about a specific DB instance
aws rds describe-db-instances --db-instance-identifier mydb

# List DB clusters (Aurora)
aws rds describe-db-clusters

# Get cluster details
aws rds describe-db-clusters --db-cluster-identifier my-cluster

# List DB snapshots
aws rds describe-db-snapshots

# List automated backups
aws rds describe-db-snapshots --db-instance-identifier mydb --snapshot-type automated

# Get snapshot details
aws rds describe-db-snapshots --db-snapshot-identifier mydb-snapshot

# List DB parameter groups
aws rds describe-db-parameter-groups

# Get parameter group details
aws rds describe-db-parameters --db-parameter-group-name mydb-params

# List DB security groups
aws rds describe-db-security-groups

# List VPC security groups associated with DB
aws rds describe-db-instances --db-instance-identifier mydb --query 'DBInstances[0].VpcSecurityGroups'

# List DB subnet groups
aws rds describe-db-subnet-groups

# Get subnet group details
aws rds describe-db-subnet-groups --db-subnet-group-name mydb-subnet-group

# List read replicas
aws rds describe-db-instances --filters "Name=db-instance-id,Values=*replica*"

# List event subscriptions
aws rds describe-event-subscriptions

# List available DB engines and versions
aws rds describe-db-engine-versions

# Get DB instance events
aws rds describe-events --source-identifier mydb

# List reserved DB instances
aws rds describe-reserved-db-instances

# Check DB instance backup status
aws rds describe-db-instances --db-instance-identifier mydb --query 'DBInstances[0].LatestRestorableTime'

# List DB cluster endpoints (Aurora)
aws rds describe-db-cluster-endpoints --db-cluster-identifier my-cluster

# Get RDS export tasks
aws rds describe-export-tasks

# List DB proxy endpoints
aws rds describe-db-proxies
```

## Common Operations

```bash
# Create an RDS instance (MySQL)
aws rds create-db-instance \
  --db-instance-identifier mydb \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --master-username admin \
  --master-user-password MyPassword123! \
  --allocated-storage 20 \
  --storage-type gp3 \
  --backup-retention-period 7 \
  --multi-az

# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier mydb \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password MyPassword123! \
  --allocated-storage 20

# Create Aurora cluster
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora \
  --engine aurora-mysql \
  --master-username admin \
  --master-user-password MyPassword123!

# Create Aurora cluster instance (in cluster)
aws rds create-db-instance \
  --db-instance-identifier my-aurora-instance-1 \
  --db-instance-class db.t3.micro \
  --engine aurora-mysql \
  --db-cluster-identifier my-aurora

# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier mydb-replica \
  --source-db-instance-identifier mydb

# Create cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier mydb-replica \
  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:mydb \
  --region us-west-2

# Create parameter group
aws rds create-db-parameter-group \
  --db-parameter-group-name mydb-params \
  --db-parameter-group-family mysql8.0 \
  --description "Custom parameter group for MySQL"

# Modify parameter in group
aws rds modify-db-parameter-group \
  --db-parameter-group-name mydb-params \
  --parameters "ParameterName=max_connections,ParameterValue=200,ApplyMethod=immediate"

# Apply parameter group to DB instance
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --db-parameter-group-name mydb-params

# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name mydb-subnet-group \
  --db-subnet-group-description "Subnet group for RDS" \
  --subnet-ids subnet-12345678 subnet-87654321

# Modify DB instance (instance class)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --db-instance-class db.t3.small \
  --apply-immediately

# Modify allocated storage
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --allocated-storage 100 \
  --apply-immediately

# Enable encryption at rest
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/12345678

# Enable backup
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --backup-retention-period 30

# Create snapshot
aws rds create-db-snapshot \
  --db-snapshot-identifier mydb-snapshot \
  --db-instance-identifier mydb

# Copy snapshot to another region
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier arn:aws:rds:us-east-1:123456789012:snapshot:mydb-snapshot \
  --target-db-snapshot-identifier mydb-snapshot-copy \
  --region us-west-2

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier mydb-restored \
  --db-snapshot-identifier mydb-snapshot

# Create DB event subscription
aws rds create-event-subscription \
  --subscription-name mydb-events \
  --sns-topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --source-type db-instance

# Export DB snapshot to S3
aws rds start-export-task \
  --export-task-identifier mydb-export \
  --source-arn arn:aws:rds:us-east-1:123456789012:snapshot:mydb-snapshot \
  --s3-bucket-name my-bucket \
  --s3-prefix export/ \
  --iam-role-arn arn:aws:iam::123456789012:role/rds-export-role

# Add tags to RDS instance
aws rds add-tags-to-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:mydb \
  --tags Key=Environment,Value=production Key=Owner,Value=admin
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Start RDS instance
aws rds start-db-instance --db-instance-identifier mydb

# ⚠️ Stop RDS instance (stops charges, data persists)
aws rds stop-db-instance --db-instance-identifier mydb

# ⚠️ Reboot RDS instance
aws rds reboot-db-instance --db-instance-identifier mydb

# ⚠️ Delete RDS instance (cannot be recovered without snapshot)
aws rds delete-db-instance \
  --db-instance-identifier mydb \
  --skip-final-snapshot

# ⚠️ Delete with final snapshot (creates backup before deletion)
aws rds delete-db-instance \
  --db-instance-identifier mydb \
  --final-db-snapshot-identifier mydb-final-snapshot

# ⚠️ Delete snapshot
aws rds delete-db-snapshot --db-snapshot-identifier mydb-snapshot

# ⚠️ Delete DB cluster
aws rds delete-db-cluster \
  --db-cluster-identifier my-aurora \
  --skip-final-snapshot

# ⚠️ Delete parameter group (cannot be in use)
aws rds delete-db-parameter-group --db-parameter-group-name mydb-params

# ⚠️ Delete subnet group (no instances using it)
aws rds delete-db-subnet-group --db-subnet-group-name mydb-subnet-group

# ⚠️ Modify master user password
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --master-user-password NewPassword123! \
  --apply-immediately

# ⚠️ Enable automated backup (affects performance)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# ⚠️ Change backup window (causes reboot)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --preferred-backup-window "02:00-03:00" \
  --apply-immediately

# ⚠️ Enable Multi-AZ (requires downtime for initial sync)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --multi-az \
  --apply-immediately

# ⚠️ Delete event subscription
aws rds delete-event-subscription --subscription-name mydb-events

# ⚠️ Delete read replica
aws rds delete-db-instance \
  --db-instance-identifier mydb-replica \
  --skip-final-snapshot

# ⚠️ Modify publicly accessible setting
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --publicly-accessible \
  --apply-immediately

# ⚠️ Change database engine version (requires downtime)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --engine-version 8.0.28 \
  --allow-major-version-upgrade \
  --apply-immediately

# ⚠️ Remove tags from RDS instance
aws rds remove-tags-from-resource \
  --resource-name arn:aws:rds:us-east-1:123456789012:db:mydb \
  --tag-keys Environment Owner
```

## Best Practices

- **Backup Strategy**: Enable automated backups with 7+ day retention; test restore procedures
- **Multi-AZ**: Enable for production databases to ensure high availability and automatic failover
- **Parameter Groups**: Create custom parameter groups to tune for workload; use versioning
- **Instance Class**: Start conservative and scale up; use Compute Optimizer for recommendations
- **Encryption**: Enable encryption at rest and in transit for sensitive data
- **Read Replicas**: Use for read-heavy workloads; can promote to standalone instance if needed
- **Subnet Groups**: Place instances in private subnets; use security groups to restrict access
- **Monitoring**: Enable Enhanced Monitoring and Performance Insights for troubleshooting
- **Maintenance**: Schedule backups and maintenance windows during off-peak hours
- **Storage Scaling**: Use auto-scaling for gp3 volumes; monitor growth trends
- **Point-in-Time Recovery**: Backups allow recovery to any point within retention period
- **Snapshots**: Copy snapshots to another region for disaster recovery

## Related Skills

- VPC - Place RDS in private subnets with proper security group rules
- IAM - Grant database access permissions and RDS API access
- CloudWatch - Monitor database performance and set alarms
- Secrets Manager - Store database credentials securely
- Lambda - Trigger Lambda functions on RDS events
- DMS - Migrate databases to RDS from other sources
