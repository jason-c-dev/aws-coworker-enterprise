# EKS CLI Reference

## Overview
Amazon Elastic Kubernetes Service (EKS) is a managed Kubernetes service that simplifies running Kubernetes on AWS. Use these commands to create and manage EKS clusters, manage node groups, install and manage add-ons, configure networking, and integrate with AWS services.

## Discovery Commands (Read-Only)

```bash
# List all EKS clusters
aws eks list-clusters

# Get cluster details
aws eks describe-cluster --name my-cluster

# Get cluster endpoint (for kubectl)
aws eks describe-cluster --name my-cluster --query 'cluster.endpoint'

# Get cluster certificate authority data
aws eks describe-cluster --name my-cluster --query 'cluster.certificateAuthority.data'

# List node groups in cluster
aws eks list-nodegroups --cluster-name my-cluster

# Get node group details
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup

# Get cluster status
aws eks describe-cluster --name my-cluster --query 'cluster.status'

# List EKS add-ons
aws eks describe-addon-versions

# List installed add-ons in cluster
aws eks list-addons --cluster-name my-cluster

# Get add-on details
aws eks describe-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni

# Get cluster resources (CPU, memory allocation)
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --query 'nodegroup.resources'

# List cluster security groups
aws eks describe-cluster --name my-cluster --query 'cluster.resourcesVpcConfig.securityGroupIds'

# Get cluster subnets
aws eks describe-cluster --name my-cluster --query 'cluster.resourcesVpcConfig.subnetIds'

# Check OIDC provider for cluster
aws eks describe-cluster --name my-cluster --query 'cluster.identity.oidc.issuer'

# List cluster access entries (IAM authentication)
aws eks list-access-entries --cluster-name my-cluster

# Get access entry details
aws eks describe-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/eks-admin

# List cluster tags
aws eks describe-cluster --name my-cluster --query 'cluster.tags'

# Check cluster logging configuration
aws eks describe-cluster --name my-cluster --query 'cluster.logging.clusterLogging'

# Get node group scaling configuration
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --query 'nodegroup.scalingConfig'

# Check node group capacity
aws eks describe-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --query 'nodegroup.resources'
```

## Common Operations

```bash
# Create EKS cluster (minimal configuration)
aws eks create-cluster \
  --name my-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-12345678,subnet-87654321

# Create cluster with advanced configuration
aws eks create-cluster \
  --name my-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-12345678,subnet-87654321,securityGroupIds=sg-12345678 \
  --logging clusterLogging=[{enabled=true,types=[api,audit,authenticator,controllerManager,scheduler]}] \
  --tags Environment=production,Owner=admin

# Create cluster with access entries (IAM authentication)
aws eks create-cluster \
  --name my-cluster \
  --version 1.28 \
  --role-arn arn:aws:iam::123456789012:role/eks-service-role \
  --resources-vpc-config subnetIds=subnet-12345678,subnet-87654321 \
  --access-config authenticationMode=API_AND_CONFIG_MAP

# Create node group (managed)
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --subnets subnet-12345678 subnet-87654321 \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --scaling-config minSize=1,maxSize=10,desiredSize=3

# Create node group with specific instance types
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --subnets subnet-12345678 subnet-87654321 \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --instance-types t3.medium t3.large \
  --scaling-config minSize=1,maxSize=10,desiredSize=3 \
  --disk-size 50

# Create Spot instance node group (cost optimization)
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-spot-nodegroup \
  --subnets subnet-12345678 subnet-87654321 \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --capacity-type SPOT \
  --instance-types t3.medium t3.large t2.medium \
  --scaling-config minSize=1,maxSize=10,desiredSize=3

# Install/update add-on (VPC CNI)
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni \
  --addon-version v1.14.1-eksbuild.1 \
  --service-account-role-arn arn:aws:iam::123456789012:role/vpc-cni-role

# Install CoreDNS add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name coredns \
  --addon-version v1.9.3-eksbuild.2

# Install kube-proxy add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name kube-proxy \
  --addon-version v1.28.0-eksbuild.1

# Update cluster version
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-network-config serviceIpv4Cidr=10.100.0.0/16

# Update node group scaling
aws eks update-nodegroup-config \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --scaling-config minSize=2,maxSize=20,desiredSize=5

# Enable cluster logging (API, audit, authenticator, controllerManager, scheduler)
aws eks update-cluster-config \
  --name my-cluster \
  --logging clusterLogging=[{enabled=true,types=[api,audit,authenticator,controllerManager,scheduler]}]

# Create OIDC identity provider (for IRSA - IAM Roles for Service Accounts)
aws iam create-open-id-connect-provider \
  --url https://oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E \
  --client-id-list sts.amazonaws.com

# Create IAM role for service account (IRSA)
# First create trust policy, then create role
aws iam create-role \
  --role-name eks-service-account-role \
  --assume-role-policy-document file://trust-policy.json

# Add access entry for IAM principal
aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/my-role \
  --access-scope type=cluster \
  --access-policy arn=arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy

# Tag cluster
aws eks tag-resource \
  --resource-arn arn:aws:eks:us-east-1:123456789012:cluster/my-cluster \
  --tags Environment=production,CostCenter=engineering

# Update node group tags
aws eks update-nodegroup-config \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --tags Environment=production,Owner=admin
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Delete EKS cluster (must delete node groups first)
aws eks delete-cluster --name my-cluster

# ⚠️ Delete node group
aws eks delete-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup

# ⚠️ Update cluster networking (causes disruption)
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config subnetIds=subnet-12345678,subnet-87654321,subnet-aaaaaaaa

# ⚠️ Update node group launch template (rolling update of nodes)
aws eks update-nodegroup-config \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --launch-template id=lt-12345678,version=2

# ⚠️ Update add-on (may cause temporary service disruption)
aws eks update-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni \
  --addon-version v1.15.0-eksbuild.1

# ⚠️ Delete add-on
aws eks delete-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni

# ⚠️ Disassociate access policy (removes IAM access)
aws eks disassociate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/my-role \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy

# ⚠️ Remove access entry (denies IAM principal cluster access)
aws eks delete-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/my-role

# ⚠️ Untag cluster
aws eks untag-resource \
  --resource-arn arn:aws:eks:us-east-1:123456789012:cluster/my-cluster \
  --tag-keys Environment CostCenter

# ⚠️ Update cluster encryption configuration (requires downtime)
aws eks update-cluster-config \
  --name my-cluster \
  --encryption-config resources=[secrets],provider={keyArn=arn:aws:kms:region:account-id:key/key-id}

# ⚠️ Downgrade cluster version (risky, not recommended)
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-version 1.27

# ⚠️ Disable endpoint private access (makes cluster internet-facing only)
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPrivateAccess=false,endpointPublicAccess=true

# ⚠️ Delete OIDC provider (breaks IRSA)
aws iam delete-open-id-connect-provider --open-id-connect-provider-arn arn:aws:iam::123456789012:oidc-provider/oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E
```

## Best Practices

- **Cluster Networking**: Create clusters with private subnets for nodes; restrict public endpoint access if possible
- **Node Groups**: Use managed node groups; distribute across multiple AZs for high availability
- **Add-ons**: Keep add-ons updated (VPC CNI, CoreDNS, kube-proxy) for security patches
- **IRSA**: Use IAM Roles for Service Accounts instead of node IAM role for fine-grained permissions
- **Logging**: Enable control plane logging for audit, API, and authenticator logs to CloudWatch
- **Monitoring**: Use CloudWatch Container Insights for cluster and workload monitoring
- **Security**: Enable private endpoint access; use security groups to restrict pod traffic
- **Auto Scaling**: Use Cluster Autoscaler or Karpenter for automatic node scaling based on pod requirements
- **Cost Optimization**: Mix On-Demand and Spot instances; use Fargate for burstable workloads
- **RBAC**: Define Kubernetes RBAC roles for access control within the cluster
- **Version Updates**: Keep cluster and add-ons up to date; test in dev before production updates
- **Backup Strategy**: Back up etcd and critical workloads regularly; plan disaster recovery

## Related Skills

- IAM - Create roles for cluster and nodes, configure IRSA
- VPC - Configure VPCs and subnets for cluster networking
- CloudWatch - Monitor cluster and application metrics
- Secrets Manager - Store sensitive data securely in Kubernetes
- ECR - Push container images for EKS workloads
- Auto Scaling - Automatically scale nodes based on demand
- Load Balancing - Distribute traffic to Kubernetes services
