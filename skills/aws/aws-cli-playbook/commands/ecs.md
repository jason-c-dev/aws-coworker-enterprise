# ECS CLI Reference

## Overview
Amazon Elastic Container Service (ECS) is a container orchestration service for running Docker containers. Use these commands to create and manage clusters, define task definitions, run tasks, manage services, and configure load balancing.

## Discovery Commands (Read-Only)

```bash
# List all ECS clusters
aws ecs list-clusters

# Get cluster details
aws ecs describe-clusters --clusters my-cluster

# List container instances in cluster
aws ecs list-container-instances --cluster my-cluster

# Get container instance details
aws ecs describe-container-instances \
  --cluster my-cluster \
  --container-instances container-instance-arn

# List services in cluster
aws ecs list-services --cluster my-cluster

# Get service details
aws ecs describe-services --cluster my-cluster --services my-service

# List task definitions
aws ecs list-task-definitions

# Get task definition details
aws ecs describe-task-definition --task-definition my-task

# List tasks in a service
aws ecs list-tasks --cluster my-cluster --service-name my-service

# List all running tasks
aws ecs list-tasks --cluster my-cluster

# Get task details
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abcd1234

# List task definition families
aws ecs list-task-definition-families

# Get task definition revisions
aws ecs list-task-definitions --family-prefix my-task

# List container instances
aws ecs list-container-instances --cluster my-cluster

# Get cluster capacity provider information
aws ecs describe-capacity-providers --capacity-providers my-capacity-provider

# List cluster capacity provider associations
aws ecs list-clusters --query 'clusterArns[]'

# Get service events (load balancer, scaling events)
aws ecs describe-services \
  --cluster my-cluster \
  --services my-service \
  --query 'services[0].events'

# List task attributes
aws ecs list-attributes \
  --cluster my-cluster \
  --target-type container-instance

# Get container instance attributes
aws ecs list-attributes \
  --cluster my-cluster \
  --target-type container-instance \
  --attribute-name ecs.ami-id

# Check container instance resource availability
aws ecs describe-container-instances \
  --cluster my-cluster \
  --container-instances container-instance-arn \
  --query 'containerInstances[0].remainingResources'
```

## Common Operations

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name my-cluster

# Create cluster with Container Insights
aws ecs create-cluster \
  --cluster-name my-cluster \
  --cluster-settings name=containerInsights,value=enabled

# Register task definition (from JSON file)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Register task definition inline
aws ecs register-task-definition \
  --family my-task \
  --network-mode awsvpc \
  --requires-compatibilities EC2 FARGATE \
  --cpu 256 \
  --memory 512 \
  --container-definitions file://container-definitions.json

# Run a one-time task
aws ecs run-task \
  --cluster my-cluster \
  --task-definition my-task:1 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678]} \
  --count 1

# Run task with overrides
aws ecs run-task \
  --cluster my-cluster \
  --task-definition my-task:1 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678]} \
  --overrides containerOverrides=[{name=my-container,environment=[{name=ENV,value=production}]}]

# Create service with load balancer
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service \
  --task-definition my-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678]} \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/abcd1234,containerName=my-container,containerPort=8080

# Create service with EC2 launch type
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service \
  --task-definition my-task:1 \
  --desired-count 3 \
  --launch-type EC2

# Update service desired count
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --desired-count 5

# Update service task definition (deploy new version)
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --task-definition my-task:2 \
  --force-new-deployment

# Create service with auto scaling
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service \
  --task-definition my-task:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --deployment-configuration maximumPercent=200,minimumHealthyPercent=100

# Create Auto Scaling target
aws autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10

# Create Auto Scaling policy (target tracking)
aws autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration TargetValue=70,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}

# Update task definition with new container image
aws ecs update-task-definition \
  --task-definition my-task \
  --container-definitions '[{"name":"my-container","image":"my-repo/my-image:v2.0","memory":512}]'

# Tag ECS resource
aws ecs tag-resource \
  --resource-arn arn:aws:ecs:us-east-1:123456789012:service/my-cluster/my-service \
  --tags key=Environment,value=production key=Owner,value=admin

# Execute command in running container
aws ecs execute-command \
  --cluster my-cluster \
  --task arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abcd1234 \
  --container my-container \
  --command "/bin/bash" \
  --interactive

# Put cluster capacity providers
aws ecs put-cluster-capacity-providers \
  --cluster my-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1,base=2
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete ECS cluster
aws ecs delete-cluster --cluster my-cluster

# ⚠️ Stop service (removes all tasks)
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --desired-count 0

# ⚠️ Delete service
aws ecs delete-service \
  --cluster my-cluster \
  --service my-service \
  --force

# ⚠️ Deregister task definition
aws ecs deregister-task-definition --task-definition my-task:1

# ⚠️ Stop running task
aws ecs stop-task \
  --cluster my-cluster \
  --task arn:aws:ecs:us-east-1:123456789012:task/my-cluster/abcd1234 \
  --reason "Manual stop"

# ⚠️ Stop all tasks in service
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --desired-count 0

# ⚠️ Drain container instance (graceful drain of tasks)
aws ecs update-container-instance-state \
  --cluster my-cluster \
  --container-instance arn:aws:ecs:us-east-1:123456789012:container-instance/my-cluster/abcd1234 \
  --status DRAINING

# ⚠️ Deregister container instance
aws ecs deregister-container-instance \
  --cluster my-cluster \
  --container-instance arn:aws:ecs:us-east-1:123456789012:container-instance/my-cluster/abcd1234 \
  --force

# ⚠️ Deregister task definition (removes all revisions)
aws ecs deregister-task-definition --task-definition my-task:1

# ⚠️ Update service and force new deployment
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --force-new-deployment

# ⚠️ Update service with zero desired count
aws ecs update-service \
  --cluster my-cluster \
  --service my-service \
  --desired-count 0

# ⚠️ Deregister entire container instance
aws ecs deregister-container-instance \
  --cluster my-cluster \
  --container-instance container-instance-arn \
  --force

# ⚠️ Put attributes on container instance (marks for drain)
aws ecs put-attributes \
  --cluster my-cluster \
  --attributes name=ecs.instance-state,value=draining,targetId=container-instance-arn

# ⚠️ Update service scaling policy (decrease)
aws autoscaling put-scaling-policy \
  --policy-name scale-down \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type StepScaling \
  --adjustment-type PercentChangeInCapacity \
  --metric-aggregation-type Average

# ⚠️ Untag ECS resource
aws ecs untag-resource \
  --resource-arn arn:aws:ecs:us-east-1:123456789012:service/my-cluster/my-service \
  --tag-keys Environment Owner

# ⚠️ Delete Auto Scaling target
aws autoscaling deregister-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount
```

## Best Practices

- **Launch Type Choice**: Use Fargate for simpler deployment; use EC2 for more control and cost savings at scale
- **Task Definition Versioning**: Always version task definitions; use immutable image tags (not latest)
- **Resource Allocation**: Right-size CPU and memory; monitor CloudWatch metrics to optimize
- **Health Checks**: Define health checks in task definitions for load balancer integration
- **Logging**: Configure CloudWatch Logs or other logging for container stdout/stderr
- **Secrets Management**: Use Secrets Manager or Parameter Store for sensitive data, not environment variables
- **Service Updates**: Use blue-green deployments with minimum healthy percentage settings
- **Capacity Planning**: Monitor cluster capacity; use auto scaling for dynamic workloads
- **Networking**: Place Fargate tasks in private subnets; use security groups to control access
- **IAM Roles**: Assign task execution role and task role for proper permissions
- **Monitoring**: Enable Container Insights for cluster-level visibility and alarms
- **Cost Optimization**: Use Spot capacity providers for non-critical workloads; use Fargate Spot for savings

## Related Skills

- ECR - Push container images to Amazon Elastic Container Registry
- IAM - Create roles for ECS task execution and application permissions
- CloudWatch - Monitor container logs and metrics
- Load Balancing - Distribute traffic across ECS services
- Auto Scaling - Scale ECS services based on metrics
- Secrets Manager - Store database credentials and API keys
