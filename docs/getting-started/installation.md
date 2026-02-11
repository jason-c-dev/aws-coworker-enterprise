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

AWS Coworker ships with **batteries-included defaults** — core config files are committed to the repository and work out of the box after `git clone`. You only need to customize what's specific to your organization.

### What Ships by Default (Core)

| File | Purpose | Action Needed |
|------|---------|---------------|
| `config/environments/environments.yaml` | Environment tier definitions (sandbox through production) with safety rules | **None** — review and use as-is, or override with `environments.local.yaml` |
| `config/profiles/profiles.yaml` | Profile schema and auto-classify patterns (maps profile names to environments) | **None** — works with standard naming conventions |

### What You Customize (Organization)

| File | Purpose | Action Needed |
|------|---------|---------------|
| `config/profiles/profiles.local.yaml` | Your specific AWS CLI profile-to-environment mappings | **Create** — see `example-profiles.yaml` for reference |
| `config/org-config/org-config.yaml` | Your OU structure, tagging standards, naming conventions | **Create if needed** — see `example-org-config.yaml` for reference |

All `*.local.yaml` files are gitignored, so your organization-specific configuration stays out of the shared repository.

### Adding Your Profile Mappings

Create `config/profiles/profiles.local.yaml` with your specific profiles:

```yaml
# config/profiles/profiles.local.yaml (gitignored — your org's profiles)
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

> **Note:** If your profiles follow standard naming conventions (e.g., `myorg-dev-admin`, `myorg-prod-readonly`), the auto-classify patterns in the core `profiles.yaml` will detect them automatically. You only need `profiles.local.yaml` for profiles that don't match the patterns or need custom settings.

### Adding Organization Configuration (Optional)

If you have an AWS Organizations structure, create `config/org-config/org-config.yaml`:

```yaml
# config/org-config/org-config.yaml (or org-config.local.yaml if gitignoring)
organization:
  name: Your Organization Name
  management_account: "000000000000"

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

  tagging:
    required: [Environment, Owner, CostCenter]
    recommended: [Project, DataClassification]

  naming:
    pattern: "{org}-{env}-{service}-{component}"
    org_prefix: acme
```

See `config/org-config/example-org-config.yaml` for the full reference template.

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

Try a simple discovery operation using the AWS Coworker command:

```
/aws-coworker-plan-interaction

# When prompted, describe your goal:
"Discover what S3 buckets exist in this account"
```

Verify that:
1. Profile and region are announced before any AWS CLI execution
2. The plan uses read-only commands
3. Results are presented clearly

**Note:** While you can invoke AWS Coworker commands directly (starting with `/aws-coworker-`), free-form prompts like "list my S3 buckets" will also work safely. The [CLAUDE.md](../../CLAUDE.md) configuration ensures all AWS-related requests are automatically routed through the appropriate AWS Coworker command, enforcing the safety model regardless of how you phrase your request.

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

1. Ensure customizations use `*.local.yaml` files or are in `skills/org/`
2. Core config files (`environments.yaml`, `profiles.yaml`) may be updated — review diffs
3. Your `*.local.yaml` overrides and `skills/org/` content survive upgrades
4. Review CHANGELOG for any breaking changes to core defaults

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
