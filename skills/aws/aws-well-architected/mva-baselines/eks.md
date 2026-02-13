# EKS — MVA Baseline

## Overview

Amazon Elastic Kubernetes Service (EKS) provides managed Kubernetes clusters on AWS. EKS manages the control plane; you manage worker nodes (managed node groups, Fargate profiles, or self-managed).

**MNA (Minimum Needed Architecture):** A cluster with a Kubernetes version, a VPC with subnets, and a cluster IAM role.
**MVA (Minimum Viable Architecture):** Control plane logging, managed node groups, restricted endpoint access, IRSA for pod-level permissions, secrets encryption, governance tagging, and appropriate node sizing.

**Service Appropriateness Warning:** EKS adds significant operational complexity and is only justified when Kubernetes-specific features are required. Before evaluating EKS MVA, the orchestrator MUST check whether EKS is the right service for the use case (see Service Appropriateness Check in SKILL.md). Common misuses include: simple containerised web applications (use ECS Fargate or App Runner), event-driven short-running tasks (use Lambda), applications that don't need Kubernetes features like CRDs, operators, or service mesh (use ECS), single-container services with basic scaling (use App Runner).

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Cluster endpoint access restricted (not fully public without restrictions) | Critical | Unrestricted public API server access exposes the control plane |
| Security | Control plane logging enabled (at minimum: api, audit, authenticator) | High | Without logging, cluster activity is invisible |
| Security | Managed node groups used (not self-managed instances) | High | Managed node groups handle patching, draining, and lifecycle |
| Operational Excellence | Governance tags applied to cluster, node groups, and associated resources | High | Untagged resources violate governance compliance |

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
| Security | OIDC provider configured for IAM Roles for Service Accounts (IRSA) | Medium | Enables pod-level IAM permissions instead of node-level |
| Security | Private endpoint access enabled (in addition to public) | Medium | Allows cluster access from within the VPC without traversing internet |
| Operational Excellence | CoreDNS, kube-proxy, and vpc-cni add-ons managed by EKS (not self-managed) | Medium | Managed add-ons receive automatic security patches |
| Cost Optimization | Node group instance types appropriate for workload (not over-provisioned) | Low | Dev workloads rarely need large instance types |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Cluster endpoint set to private-only (or public with CIDR restrictions) | High | Staging should mirror production network restrictions |
| Security | Secrets encryption enabled with KMS key | High | Kubernetes secrets are base64-encoded, not encrypted, by default |
| Security | Pod security standards enforced (baseline or restricted) | High | Prevents privileged containers and host namespace access |
| Reliability | Node groups span multiple Availability Zones | High | Single-AZ node groups are a single point of failure |
| Reliability | Network policies enforced (Calico or VPC CNI network policy) | Medium | Restricts pod-to-pod communication based on policy |
| Operational Excellence | Kubernetes version within supported window (not deprecated) | High | Deprecated versions stop receiving security patches |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | GuardDuty EKS protection enabled | High | Detects suspicious Kubernetes API calls and container runtime threats |
| Security | Private endpoint only (no public access) | High | Production control plane must not be internet-accessible |
| Reliability | Cluster Autoscaler or Karpenter configured | High | Automatic node scaling for workload demands |
| Reliability | Pod Disruption Budgets (PDBs) defined for critical workloads | Medium | Prevents voluntary disruptions from taking down all replicas |
| Reliability | Upgrade strategy documented (sequential minor version upgrades) | Medium | EKS only supports upgrading one minor version at a time |
| Cost Optimization | Spot instances evaluated for fault-tolerant node groups | Low | Significant savings for interruptible workloads |
| Operational Excellence | Kubernetes audit logs to CloudWatch (via control plane logging) | High | Production cluster activity must be auditable |
| Operational Excellence | CloudWatch Container Insights or Prometheus/Grafana for monitoring | High | Production must have monitoring and alerting |
| Operational Excellence | Deployed via IaC (CDK/Terraform/eksctl), not direct CLI | High | Production infrastructure must be reproducible |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | Cluster endpoint access restricted | R | R | R | R | Critical |
| Security | Control plane logging (api, audit, authenticator) | R | R | R | R | High |
| Security | Managed node groups | R | R | R | R | High |
| Security | OIDC provider / IRSA | - | R | R | R | Medium |
| Security | Private endpoint access enabled | - | R | R | R | Medium |
| Security | Private-only or CIDR-restricted endpoint | - | - | R | R | High |
| Security | Secrets encryption with KMS | - | - | R | R | High |
| Security | Pod security standards | - | - | R | R | High |
| Security | GuardDuty EKS protection | - | - | - | R | High |
| Security | Private endpoint only | - | - | - | R | High |
| Reliability | Multi-AZ node groups | - | - | R | R | High |
| Reliability | Network policies | - | - | R | R | Medium |
| Reliability | Cluster Autoscaler / Karpenter | - | - | - | R | High |
| Reliability | Pod Disruption Budgets | - | - | - | R | Medium |
| Reliability | Upgrade strategy documented | - | - | - | R | Medium |
| Cost Optimization | Instance types appropriate | - | R | R | R | Low |
| Cost Optimization | Spot instances evaluated | - | - | - | R | Low |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | Managed add-ons | - | R | R | R | Medium |
| Operational Excellence | Kubernetes version supported | - | - | R | R | High |
| Operational Excellence | Audit logs to CloudWatch | - | - | - | R | High |
| Operational Excellence | Container Insights / Prometheus | - | - | - | R | High |
| Operational Excellence | Deployed via IaC | - | - | - | R | High |

Legend: R = Required, - = Not required at this tier

---

## Gap Detection Guide

### Cluster Endpoint Access

- **Check command:** `aws eks describe-cluster --name {cluster_name} --query 'cluster.resourcesVpcConfig.{endpointPublicAccess:endpointPublicAccess,endpointPrivateAccess:endpointPrivateAccess,publicAccessCidrs:publicAccessCidrs}'`
- **Gap condition:** `endpointPublicAccess: true` with `publicAccessCidrs: ["0.0.0.0/0"]` and `endpointPrivateAccess: false`
- **Severity:** Critical
- **Remediation:** `aws eks update-cluster-config --name {cluster_name} --resources-vpc-config endpointPublicAccess=false,endpointPrivateAccess=true`
- **Remediation description:** Restricts API server access to VPC-internal traffic only

### Control Plane Logging

- **Check command:** `aws eks describe-cluster --name {cluster_name} --query 'cluster.logging.clusterLogging[0].{types:types,enabled:enabled}'`
- **Gap condition:** `enabled: false` or missing log types (api, audit, authenticator)
- **Severity:** High
- **Remediation:** `aws eks update-cluster-config --name {cluster_name} --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'`
- **Remediation description:** Enables control plane logging for visibility into cluster operations

### Secrets Encryption

- **Check command:** `aws eks describe-cluster --name {cluster_name} --query 'cluster.encryptionConfig'`
- **Gap condition:** `encryptionConfig` is null or empty
- **Severity:** High (staging/prod)
- **Remediation:** `aws eks associate-encryption-config --cluster-name {cluster_name} --encryption-config '[{"resources":["secrets"],"provider":{"keyArn":"{kms_key_arn}"}}]'`
- **Remediation description:** Encrypts Kubernetes secrets at rest using a KMS key

### Managed Node Groups

- **Check command:** `aws eks list-nodegroups --cluster-name {cluster_name}`
- **Gap condition:** No managed node groups (using self-managed instances or no node groups at all)
- **Severity:** High
- **Remediation:** `aws eks create-nodegroup --cluster-name {cluster_name} --nodegroup-name {name} --node-role {role_arn} --subnets {subnet_ids} --instance-types {types}`
- **Remediation description:** Creates a managed node group that handles patching and lifecycle automatically

### OIDC Provider for IRSA

- **Check command:** `aws eks describe-cluster --name {cluster_name} --query 'cluster.identity.oidc.issuer'` then check if provider exists: `aws iam list-open-id-connect-providers`
- **Gap condition:** Cluster has OIDC issuer but no corresponding IAM OIDC provider
- **Severity:** Medium
- **Remediation:** `eksctl utils associate-iam-oidc-provider --cluster {cluster_name} --approve` or create via AWS CLI
- **Remediation description:** Enables IAM Roles for Service Accounts (IRSA) for pod-level permissions

### Kubernetes Version

- **Check command:** `aws eks describe-cluster --name {cluster_name} --query 'cluster.version'`
- **Gap condition:** Version is deprecated or approaching end-of-support
- **Severity:** High (staging/prod)
- **Remediation:** `aws eks update-cluster-version --name {cluster_name} --kubernetes-version {next_version}`
- **Remediation description:** Upgrades to a supported Kubernetes version (one minor version at a time)

### Governance Tags

- **Check command:** `aws eks list-tags-for-resource --resource-arn {cluster_arn}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws eks tag-resource --resource-arn {cluster_arn} --tags Key1=Value1,Key2=Value2`
- **Remediation description:** Applies required governance tags for compliance

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- EKS cluster creation takes 10-15 minutes — plan accordingly for tests
- EKS only supports upgrading one minor Kubernetes version at a time (e.g., 1.28 → 1.29, not 1.28 → 1.30)
- IRSA (IAM Roles for Service Accounts) is the recommended way to grant AWS permissions to pods — avoid node-level IAM roles
- EKS Fargate profiles are an alternative to managed node groups for specific namespaces but have limitations (no DaemonSets, no GPU, no persistent volumes with EBS)
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/eks.md` for CLI command reference
