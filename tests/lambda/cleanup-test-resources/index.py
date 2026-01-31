"""
AWS Coworker Test Resource Cleanup Lambda

Runs on a schedule to clean up any test resources that have exceeded their TTL.
This is the "safety net" that catches resources missed by manual cleanup.

Environment Variables:
    DRY_RUN: Set to "true" to log without deleting (default: false)
    DEFAULT_TTL_HOURS: Default TTL if not tagged (default: 4)
    SNS_TOPIC_ARN: Optional SNS topic for notifications
"""

import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# Configuration
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'
DEFAULT_TTL_HOURS = int(os.environ.get('DEFAULT_TTL_HOURS', '4'))
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
TAG_PURPOSE = 'aws-coworker-test'

# Clients
ec2 = boto3.client('ec2')
s3 = boto3.client('s3')
eks = boto3.client('eks')
rds = boto3.client('rds')
lambda_client = boto3.client('lambda')
ecs = boto3.client('ecs')
sts = boto3.client('sts')
sns = boto3.client('sns') if SNS_TOPIC_ARN else None

# Get account ID for ARN construction
ACCOUNT_ID = sts.get_caller_identity()['Account']
REGION = boto3.session.Session().region_name


def lambda_handler(event, context):
    """Main Lambda handler."""
    print(f"Starting cleanup run. DRY_RUN={DRY_RUN}")

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dry_run': DRY_RUN,
        'cleaned': {
            'ec2_instances': [],
            'security_groups': [],
            'key_pairs': [],
            's3_buckets': [],
            'elastic_ips': [],
            'ebs_volumes': [],
            'eks_clusters': [],
            'rds_instances': [],
            'lambda_functions': [],
            'ecs_clusters': [],
            'nat_gateways': []
        },
        'errors': [],
        'skipped': []
    }

    try:
        # Clean up in order of dependencies (highest-level first)

        # 1. Container orchestration (slow, start early)
        results['cleaned']['eks_clusters'] = cleanup_eks_clusters()
        results['cleaned']['ecs_clusters'] = cleanup_ecs_clusters()

        # 2. Databases
        results['cleaned']['rds_instances'] = cleanup_rds_instances()

        # 3. Compute
        results['cleaned']['ec2_instances'] = cleanup_ec2_instances()
        results['cleaned']['lambda_functions'] = cleanup_lambda_functions()
        results['cleaned']['ebs_volumes'] = cleanup_ebs_volumes()

        # 4. Networking
        results['cleaned']['nat_gateways'] = cleanup_nat_gateways()
        results['cleaned']['elastic_ips'] = cleanup_elastic_ips()
        results['cleaned']['security_groups'] = cleanup_security_groups()

        # 5. Storage & keys
        results['cleaned']['key_pairs'] = cleanup_key_pairs()
        results['cleaned']['s3_buckets'] = cleanup_s3_buckets()

    except Exception as e:
        results['errors'].append(str(e))
        print(f"Error during cleanup: {e}")

    # Send notification if configured
    if SNS_TOPIC_ARN and any(results['cleaned'].values()):
        send_notification(results)

    print(f"Cleanup complete: {json.dumps(results, indent=2)}")
    return results


def get_resource_age_hours(tags: List[Dict]) -> float:
    """Calculate resource age from TestRun tag."""
    for tag in tags:
        if tag.get('Key') == 'TestRun':
            try:
                # Parse timestamp like 20260130-143022
                created = datetime.strptime(tag['Value'], '%Y%m%d-%H%M%S')
                created = created.replace(tzinfo=timezone.utc)
                age = datetime.now(timezone.utc) - created
                return age.total_seconds() / 3600
            except ValueError:
                pass
    return float('inf')  # Unknown age, treat as expired


def get_ttl_hours(tags: List[Dict]) -> int:
    """Get TTL from tags or use default."""
    for tag in tags:
        if tag.get('Key') == 'TTL':
            try:
                return int(tag['Value'])
            except ValueError:
                pass
    return DEFAULT_TTL_HOURS


def is_test_resource(tags: List[Dict]) -> bool:
    """Check if resource is tagged as a test resource."""
    for tag in tags:
        if tag.get('Key') == 'Purpose' and tag.get('Value') == TAG_PURPOSE:
            return True
    return False


def should_cleanup(tags: List[Dict]) -> bool:
    """Determine if resource should be cleaned up based on age and TTL."""
    if not is_test_resource(tags):
        return False

    age_hours = get_resource_age_hours(tags)
    ttl_hours = get_ttl_hours(tags)

    return age_hours > ttl_hours


def cleanup_ec2_instances() -> List[str]:
    """Terminate expired EC2 instances."""
    cleaned = []

    paginator = ec2.get_paginator('describe_instances')
    for page in paginator.paginate(
        Filters=[
            {'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}
        ]
    ):
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                tags = instance.get('Tags', [])

                if should_cleanup(tags):
                    age = get_resource_age_hours(tags)
                    ttl = get_ttl_hours(tags)
                    print(f"Instance {instance_id}: age={age:.1f}h, ttl={ttl}h - EXPIRED")

                    if not DRY_RUN:
                        ec2.terminate_instances(InstanceIds=[instance_id])
                        print(f"Terminated instance: {instance_id}")
                    else:
                        print(f"[DRY RUN] Would terminate: {instance_id}")

                    cleaned.append(instance_id)

    return cleaned


def cleanup_ebs_volumes() -> List[str]:
    """Delete expired unattached EBS volumes."""
    cleaned = []

    paginator = ec2.get_paginator('describe_volumes')
    for page in paginator.paginate(
        Filters=[
            {'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]},
            {'Name': 'status', 'Values': ['available']}  # Only unattached
        ]
    ):
        for volume in page['Volumes']:
            volume_id = volume['VolumeId']
            tags = volume.get('Tags', [])

            if should_cleanup(tags):
                if not DRY_RUN:
                    ec2.delete_volume(VolumeId=volume_id)
                    print(f"Deleted volume: {volume_id}")
                else:
                    print(f"[DRY RUN] Would delete volume: {volume_id}")

                cleaned.append(volume_id)

    return cleaned


def cleanup_security_groups() -> List[str]:
    """Delete expired security groups."""
    cleaned = []

    # Wait a bit for instances to terminate
    if not DRY_RUN:
        import time
        time.sleep(10)

    paginator = ec2.get_paginator('describe_security_groups')
    for page in paginator.paginate(
        Filters=[{'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]}]
    ):
        for sg in page['SecurityGroups']:
            sg_id = sg['GroupId']
            tags = sg.get('Tags', [])

            if should_cleanup(tags):
                try:
                    if not DRY_RUN:
                        ec2.delete_security_group(GroupId=sg_id)
                        print(f"Deleted security group: {sg_id}")
                    else:
                        print(f"[DRY RUN] Would delete security group: {sg_id}")

                    cleaned.append(sg_id)
                except Exception as e:
                    print(f"Could not delete {sg_id}: {e}")

    return cleaned


def cleanup_key_pairs() -> List[str]:
    """Delete expired key pairs."""
    cleaned = []

    response = ec2.describe_key_pairs(
        Filters=[{'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]}]
    )

    for kp in response.get('KeyPairs', []):
        kp_name = kp['KeyName']
        kp_id = kp.get('KeyPairId', '')
        tags = kp.get('Tags', [])

        if should_cleanup(tags):
            if not DRY_RUN:
                ec2.delete_key_pair(KeyPairId=kp_id)
                print(f"Deleted key pair: {kp_name}")
            else:
                print(f"[DRY RUN] Would delete key pair: {kp_name}")

            cleaned.append(kp_name)

    return cleaned


def cleanup_elastic_ips() -> List[str]:
    """Release expired Elastic IPs."""
    cleaned = []

    response = ec2.describe_addresses(
        Filters=[{'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]}]
    )

    for address in response.get('Addresses', []):
        allocation_id = address['AllocationId']
        tags = address.get('Tags', [])

        if should_cleanup(tags):
            if not DRY_RUN:
                ec2.release_address(AllocationId=allocation_id)
                print(f"Released Elastic IP: {allocation_id}")
            else:
                print(f"[DRY RUN] Would release Elastic IP: {allocation_id}")

            cleaned.append(allocation_id)

    return cleaned


def cleanup_s3_buckets() -> List[str]:
    """Delete expired S3 buckets."""
    cleaned = []

    response = s3.list_buckets()

    for bucket in response.get('Buckets', []):
        bucket_name = bucket['Name']

        try:
            tagging = s3.get_bucket_tagging(Bucket=bucket_name)
            tags = [{'Key': t['Key'], 'Value': t['Value']} for t in tagging.get('TagSet', [])]

            if should_cleanup(tags):
                if not DRY_RUN:
                    # Empty bucket first
                    s3_resource = boto3.resource('s3')
                    bucket_obj = s3_resource.Bucket(bucket_name)
                    bucket_obj.objects.all().delete()
                    bucket_obj.object_versions.all().delete()
                    s3.delete_bucket(Bucket=bucket_name)
                    print(f"Deleted bucket: {bucket_name}")
                else:
                    print(f"[DRY RUN] Would delete bucket: {bucket_name}")

                cleaned.append(bucket_name)

        except s3.exceptions.ClientError as e:
            if 'NoSuchTagSet' not in str(e):
                print(f"Error checking bucket {bucket_name}: {e}")

    return cleaned


def cleanup_eks_clusters() -> List[str]:
    """Delete expired EKS clusters."""
    cleaned = []

    try:
        response = eks.list_clusters()
        for cluster_name in response.get('clusters', []):
            try:
                cluster = eks.describe_cluster(name=cluster_name)
                tags = cluster['cluster'].get('tags', {})

                # Convert dict tags to list format for should_cleanup
                tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]

                if should_cleanup(tag_list):
                    if not DRY_RUN:
                        # Delete nodegroups first
                        nodegroups = eks.list_nodegroups(clusterName=cluster_name)
                        for ng in nodegroups.get('nodegroups', []):
                            eks.delete_nodegroup(clusterName=cluster_name, nodegroupName=ng)
                            print(f"Deleting nodegroup: {ng}")

                        # Delete cluster (async)
                        eks.delete_cluster(name=cluster_name)
                        print(f"Initiated EKS cluster deletion: {cluster_name}")
                    else:
                        print(f"[DRY RUN] Would delete EKS cluster: {cluster_name}")

                    cleaned.append(cluster_name)
            except Exception as e:
                print(f"Error processing EKS cluster {cluster_name}: {e}")
    except Exception as e:
        print(f"Error listing EKS clusters: {e}")

    return cleaned


def cleanup_rds_instances() -> List[str]:
    """Delete expired RDS instances."""
    cleaned = []

    try:
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for instance in page['DBInstances']:
                db_id = instance['DBInstanceIdentifier']
                db_arn = instance['DBInstanceArn']

                try:
                    tags_response = rds.list_tags_for_resource(ResourceName=db_arn)
                    tags = [{'Key': t['Key'], 'Value': t['Value']} for t in tags_response.get('TagList', [])]

                    if should_cleanup(tags):
                        if not DRY_RUN:
                            rds.delete_db_instance(
                                DBInstanceIdentifier=db_id,
                                SkipFinalSnapshot=True,
                                DeleteAutomatedBackups=True
                            )
                            print(f"Initiated RDS deletion: {db_id}")
                        else:
                            print(f"[DRY RUN] Would delete RDS instance: {db_id}")

                        cleaned.append(db_id)
                except Exception as e:
                    print(f"Error processing RDS instance {db_id}: {e}")
    except Exception as e:
        print(f"Error listing RDS instances: {e}")

    return cleaned


def cleanup_lambda_functions() -> List[str]:
    """Delete expired Lambda functions."""
    cleaned = []

    try:
        paginator = lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            for func in page['Functions']:
                func_name = func['FunctionName']
                func_arn = func['FunctionArn']

                try:
                    tags_response = lambda_client.list_tags(Resource=func_arn)
                    tags = [{'Key': k, 'Value': v} for k, v in tags_response.get('Tags', {}).items()]

                    if should_cleanup(tags):
                        if not DRY_RUN:
                            lambda_client.delete_function(FunctionName=func_name)
                            print(f"Deleted Lambda function: {func_name}")
                        else:
                            print(f"[DRY RUN] Would delete Lambda: {func_name}")

                        cleaned.append(func_name)
                except Exception as e:
                    print(f"Error processing Lambda {func_name}: {e}")
    except Exception as e:
        print(f"Error listing Lambda functions: {e}")

    return cleaned


def cleanup_ecs_clusters() -> List[str]:
    """Delete expired ECS clusters."""
    cleaned = []

    try:
        response = ecs.list_clusters()
        for cluster_arn in response.get('clusterArns', []):
            try:
                tags_response = ecs.list_tags_for_resource(resourceArn=cluster_arn)
                tags = [{'Key': t['key'], 'Value': t['value']} for t in tags_response.get('tags', [])]

                if should_cleanup(tags):
                    cluster_name = cluster_arn.split('/')[-1]

                    if not DRY_RUN:
                        # Stop and delete services first
                        services = ecs.list_services(cluster=cluster_name)
                        for svc_arn in services.get('serviceArns', []):
                            ecs.delete_service(cluster=cluster_name, service=svc_arn, force=True)

                        ecs.delete_cluster(cluster=cluster_name)
                        print(f"Deleted ECS cluster: {cluster_name}")
                    else:
                        print(f"[DRY RUN] Would delete ECS cluster: {cluster_name}")

                    cleaned.append(cluster_name)
            except Exception as e:
                print(f"Error processing ECS cluster {cluster_arn}: {e}")
    except Exception as e:
        print(f"Error listing ECS clusters: {e}")

    return cleaned


def cleanup_nat_gateways() -> List[str]:
    """Delete expired NAT Gateways."""
    cleaned = []

    try:
        paginator = ec2.get_paginator('describe_nat_gateways')
        for page in paginator.paginate(
            Filters=[
                {'Name': 'tag:Purpose', 'Values': [TAG_PURPOSE]},
                {'Name': 'state', 'Values': ['available', 'pending']}
            ]
        ):
            for nat in page['NatGateways']:
                nat_id = nat['NatGatewayId']
                tags = nat.get('Tags', [])

                if should_cleanup(tags):
                    if not DRY_RUN:
                        ec2.delete_nat_gateway(NatGatewayId=nat_id)
                        print(f"Initiated NAT Gateway deletion: {nat_id}")
                    else:
                        print(f"[DRY RUN] Would delete NAT Gateway: {nat_id}")

                    cleaned.append(nat_id)
    except Exception as e:
        print(f"Error cleaning NAT Gateways: {e}")

    return cleaned


def send_notification(results: Dict[str, Any]):
    """Send SNS notification about cleanup."""
    if not sns:
        return

    total_cleaned = sum(len(v) for v in results['cleaned'].values())

    message = f"""
AWS Coworker Test Resource Cleanup Report
==========================================
Time: {results['timestamp']}
Dry Run: {results['dry_run']}

Resources Cleaned: {total_cleaned}

Details:
- EKS Clusters: {len(results['cleaned']['eks_clusters'])}
- ECS Clusters: {len(results['cleaned']['ecs_clusters'])}
- RDS Instances: {len(results['cleaned']['rds_instances'])}
- EC2 Instances: {len(results['cleaned']['ec2_instances'])}
- Lambda Functions: {len(results['cleaned']['lambda_functions'])}
- NAT Gateways: {len(results['cleaned']['nat_gateways'])}
- Security Groups: {len(results['cleaned']['security_groups'])}
- Key Pairs: {len(results['cleaned']['key_pairs'])}
- S3 Buckets: {len(results['cleaned']['s3_buckets'])}
- Elastic IPs: {len(results['cleaned']['elastic_ips'])}
- EBS Volumes: {len(results['cleaned']['ebs_volumes'])}

Errors: {len(results['errors'])}
"""

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='AWS Coworker Test Cleanup Report',
            Message=message
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")


# For local testing
if __name__ == '__main__':
    os.environ['DRY_RUN'] = 'true'
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))
