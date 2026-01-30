# Installation Guide

This guide covers detailed installation and configuration of AWS Coworker.

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| Claude Environment | Claude Code or compatible |
| AWS CLI | Version 2.x |
| Git | Version 2.x |
| Operating System | macOS, Linux, or Windows with WSL |

### Recommended

| Component | Recommendation |
|-----------|----------------|
| GitHub CLI | `gh` for easier workflows |
| AWS profiles | Separate profiles per environment |
| Terminal | Modern terminal with good Unicode support |

---

## Installation Steps

### 1. Clone the Repository

```bash
# HTTPS
git clone https://github.com/your-org/aws-coworker-enterprise.git

# SSH (if configured)
git clone git@github.com:your-org/aws-coworker-enterprise.git

# Navigate to directory
cd aws-coworker-enterprise
```

### 2. Verify Dependencies

```bash
# Check AWS CLI
aws --version
# Expected: aws-cli/2.x.x Python/3.x.x ...

# Check Git
git --version
# Expected: git version 2.x.x

# Check GitHub CLI (optional)
gh --version
# Expected: gh version 2.x.x
```

### 3. Configure AWS CLI

If not already configured:

```bash
# Interactive configuration
aws configure

# Or configure a specific profile
aws configure --profile dev-admin
```

#### Profile Configuration Examples

**~/.aws/credentials**
```ini
[default]
aws_access_key_id = AKIAEXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[dev-admin]
aws_access_key_id = AKIADEVEXAMPLE
aws_secret_access_key = devSecretKeyExample
```

**~/.aws/config**
```ini
[default]
region = us-east-1
output = json

[profile dev-admin]
region = us-west-2
output = json

[profile prod-readonly]
region = us-east-1
role_arn = arn:aws:iam::123456789012:role/ReadOnlyRole
source_profile = default
```

### 4. Verify AWS Access

```bash
# Test default profile
aws sts get-caller-identity

# Test specific profile
aws sts get-caller-identity --profile dev-admin
```

### 5. Open in Claude Environment

Open the `aws-coworker-enterprise` directory in your Claude Code or compatible environment.

---

## Configuration Options

### AWS Profile Classification

Create `config/profiles/profiles.yaml` to classify your profiles:

```yaml
# config/profiles/profiles.yaml
profiles:
  default:
    classification: development
    permissions: read-write
    description: Default development profile

  dev-admin:
    classification: development
    permissions: read-write
    description: Development admin access

  staging-readonly:
    classification: staging
    permissions: read-only
    description: Staging read-only access

  prod-readonly:
    classification: production
    permissions: read-only
    description: Production read-only access

  prod-admin:
    classification: production
    permissions: read-write
    require_approval: always
    description: Production admin - emergency use only
```

### Environment Configuration

Create `config/environments/environments.yaml`:

```yaml
# config/environments/environments.yaml
environments:
  sandbox:
    purpose: Experimentation and learning
    accounts: ["111111111111"]
    default_profile: sandbox-admin
    cli_permissions: read-write
    approval_required: none

  development:
    purpose: Active development
    accounts: ["222222222222"]
    default_profile: dev-admin
    cli_permissions: read-write
    approval_required: destructive-only

  staging:
    purpose: Pre-production testing
    accounts: ["333333333333"]
    default_profile: staging-readonly
    cli_permissions: read-only
    approval_required: all-mutations
    change_method: iac-pipeline

  production:
    purpose: Live workloads
    accounts: ["444444444444"]
    default_profile: prod-readonly
    cli_permissions: read-only
    approval_required: via-cicd-only
    change_method: iac-pipeline
```

### Organization Configuration

Create `config/org-config/org-config.yaml`:

```yaml
# config/org-config/org-config.yaml
organization:
  name: Your Organization Name
  management_account: "000000000000"

  # AWS Organizations structure
  organizational_units:
    - name: Security
      id: ou-xxxx-security
      accounts: ["111111111111"]

    - name: Workloads
      id: ou-xxxx-workloads
      children:
        - name: Development
          id: ou-xxxx-dev
          accounts: ["222222222222"]
        - name: Production
          id: ou-xxxx-prod
          accounts: ["333333333333", "444444444444"]

  # Tagging standards
  tagging:
    required:
      - Environment
      - Owner
      - CostCenter
    recommended:
      - Project
      - DataClassification

    allowed_values:
      Environment: [sandbox, development, staging, production]
      DataClassification: [public, internal, confidential, restricted]

  # Naming conventions
  naming:
    pattern: "{org}-{env}-{service}-{component}"
    org_prefix: acme
```

---

## Verification

### Run Audit

After installation, verify AWS Coworker health:

```
/aws-coworker-audit-library
```

This checks:
- All components have valid structure
- No missing required files
- Configuration is valid

### Test Discovery

Try a simple discovery operation:

```
"What S3 buckets exist in this account?"
```

Verify that:
1. Profile and region are announced
2. Read-only commands are used
3. Results are presented clearly

---

## Upgrading

### From a Previous Version

```bash
# Fetch updates
git fetch origin

# Check current version
git describe --tags

# Review changes
git log HEAD..origin/main --oneline

# Update
git pull origin main
```

### Preserving Customizations

If you have organization customizations:

1. Ensure customizations are in `skills/org/` or `config/org-config/`
2. These directories are designed to survive upgrades
3. Review CHANGELOG for any breaking changes

---

## Uninstallation

To remove AWS Coworker:

```bash
# Simply delete the directory
rm -rf aws-coworker-enterprise

# AWS CLI configuration is not modified
# Remove profiles manually if desired
```

---

## Troubleshooting

### AWS CLI Issues

**"Unable to locate credentials"**
```bash
# Check credentials file exists
cat ~/.aws/credentials

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**"Region not specified"**
```bash
# Set default region
aws configure set region us-east-1

# Or use environment variable
export AWS_DEFAULT_REGION=us-east-1
```

### Git Issues

**"Permission denied (publickey)"**
```bash
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/your-org/aws-coworker-enterprise.git

# Or configure SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### Claude Environment Issues

**Commands not recognized**
- Ensure you're in the AWS Coworker directory
- Verify the `.claude/` directory exists
- Check your Claude environment version

---

## Next Steps

- [First Interaction](../getting-started/README.md#your-first-interaction)
- [Common Workflows](common-workflows.md)
- [Customization Guide](../customization/README.md)
