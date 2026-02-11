# CloudFront — MVA Baseline

## Overview

Amazon CloudFront is a content delivery network (CDN) that accelerates delivery of websites, APIs, and other web assets.

**MNA (Minimum Needed Architecture):** An origin (S3 bucket or custom origin) and a distribution with default cache behavior.
**MVA (Minimum Viable Architecture):** Access logging, TLS 1.2+, HTTPS enforcement, OAC for S3 origins, custom error pages, appropriate cache policy, and governance tagging.

---

## Common (All Environments)

Items required regardless of environment tier.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | HTTPS enforcement (`redirect-to-https` or `https-only`) | High | Prevents data interception; no valid reason to allow HTTP |
| Security | TLS minimum version 1.2 (`TLSv1.2_2021` or newer) | High | TLS 1.0/1.1 have known vulnerabilities |
| Security | OAC for S3 origins (not OAI, not public bucket) | High | OAI is deprecated; public S3 buckets are a security risk |
| Cost Optimization | Appropriate price class for audience | Medium | `PriceClass_All` wastes money if users are only in US/Europe |
| Operational Excellence | Governance tags applied (7 core tags) | High | Untagged resources violate governance compliance |

---

## Sandbox

No additional items beyond Common. Sandbox prioritizes experimentation.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| — | No additional items | — | Sandbox prioritizes experimentation |

---

## Development

Additional items beyond Common for development environments.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Access logging enabled (to S3 bucket) | Medium | Useful for debugging; not strictly required in dev |
| Performance Efficiency | Compression enabled (`Compress: true`) | Low | Reduces transfer costs and improves load times |
| Operational Excellence | Default root object set (e.g., `index.html`) | Low | Prevents 403 errors on root path |

---

## Staging

Additional items beyond Development for staging environments. Critical/high gaps BLOCK execution when enforcement is `strict`.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | Access logging enabled (to S3 bucket) | High | Staging mirrors production; logging is essential for validation |
| Security | Response headers policy (security headers: HSTS, CSP, X-Frame-Options) | Medium | Should be validated before production |
| Reliability | Custom error pages configured (403, 404, 500) | Medium | User experience should be validated in staging |
| Performance Efficiency | Managed cache policy (not legacy settings) | Medium | Modern cache policies provide better control |

---

## Production

Additional items beyond Staging for production environments. ALL items are mandatory — no override path.

| Pillar | MVA Item | Severity | Why |
|--------|----------|----------|-----|
| Security | WAF integration (WebACL attached) | High | Production distributions need protection against common web exploits |
| Security | Geo-restriction configured (if applicable) | Medium | Compliance and licensing may require geographic restrictions |
| Reliability | Multiple origins or failover origin configured | Medium | Single origin is a single point of failure for production |
| Cost Optimization | Cache policy optimized for content type | Medium | Poor caching wastes origin bandwidth and increases latency |
| Operational Excellence | CloudWatch alarms for error rate and latency | High | Production must have monitoring and alerting |

---

## Full MVA Summary (Production = Superset)

| Pillar | MVA Item | Sandbox | Dev | Staging | Prod | Severity |
|--------|----------|---------|-----|---------|------|----------|
| Security | HTTPS enforcement | R | R | R | R | High |
| Security | TLS 1.2 minimum | R | R | R | R | High |
| Security | OAC for S3 origins | R | R | R | R | High |
| Security | Access logging | - | M | R | R | High |
| Security | Response headers policy | - | - | R | R | Medium |
| Security | WAF integration | - | - | - | R | High |
| Security | Geo-restriction (if applicable) | - | - | - | R | Medium |
| Reliability | Custom error pages | - | - | R | R | Medium |
| Reliability | Failover origin | - | - | - | R | Medium |
| Performance Efficiency | Compression enabled | - | R | R | R | Low |
| Performance Efficiency | Managed cache policy | - | - | R | R | Medium |
| Cost Optimization | Appropriate price class | R | R | R | R | Medium |
| Cost Optimization | Cache policy optimized | - | - | - | R | Medium |
| Operational Excellence | Governance tags | R | R | R | R | High |
| Operational Excellence | Default root object | - | R | R | R | Low |
| Operational Excellence | CloudWatch alarms | - | - | - | R | High |

Legend: R = Required, M = Medium severity (recommended), - = Not required at this tier

---

## Gap Detection Guide

### HTTPS Enforcement

- **Check command:** `aws cloudfront get-distribution-config --id {dist_id}`
- **Gap condition:** `DefaultCacheBehavior.ViewerProtocolPolicy` is `allow-all`
- **Severity:** High
- **Remediation:** Update distribution config to set `ViewerProtocolPolicy` to `redirect-to-https`
- **Remediation description:** Forces all HTTP requests to redirect to HTTPS

### TLS 1.2 Minimum

- **Check command:** `aws cloudfront get-distribution-config --id {dist_id}`
- **Gap condition:** `ViewerCertificate.MinimumProtocolVersion` is not `TLSv1.2_2021` or newer
- **Severity:** High
- **Remediation:** Update `ViewerCertificate.MinimumProtocolVersion` to `TLSv1.2_2021`
- **Remediation description:** Prevents connections using vulnerable TLS versions

### OAC for S3 Origins

- **Check command:** `aws cloudfront get-distribution-config --id {dist_id}`
- **Gap condition:** S3 origin has empty `OriginAccessControlId` AND uses legacy `S3OriginConfig.OriginAccessIdentity` or no access control
- **Severity:** High
- **Remediation:** Create OAC via `aws cloudfront create-origin-access-control`, update distribution origin, update S3 bucket policy
- **Remediation description:** Replaces legacy OAI with modern OAC for secure S3 access

### Access Logging

- **Check command:** `aws cloudfront get-distribution-config --id {dist_id}`
- **Gap condition:** `Logging.Enabled` is `false`
- **Severity:** High (staging/prod), Medium (dev)
- **Remediation:** Update distribution config to set `Logging.Enabled: true`, `Logging.Bucket: {log-bucket}.s3.amazonaws.com`
- **Remediation description:** Enables access logging to S3 for audit trails

### WAF Integration

- **Check command:** `aws cloudfront get-distribution --id {dist_id}`
- **Gap condition:** `Distribution.DistributionConfig.WebACLId` is empty
- **Severity:** High (production only)
- **Remediation:** Create WAF WebACL and associate via `aws cloudfront update-distribution` with `WebACLId`
- **Remediation description:** Attaches WAF rules to protect against common web exploits

### Governance Tags

- **Check command:** `aws cloudfront list-tags-for-resource --resource arn:aws:cloudfront::{account}:distribution/{dist_id}`
- **Gap condition:** Any of the 7 core tags missing (Name, Environment, Owner, CostCenter, Application, CreatedBy, CreatedDate)
- **Severity:** High
- **Remediation:** `aws cloudfront tag-resource --resource {arn} --tags 'Items=[...]'`
- **Remediation description:** Applies required governance tags for compliance

### Compression

- **Check command:** `aws cloudfront get-distribution-config --id {dist_id}`
- **Gap condition:** `DefaultCacheBehavior.Compress` is `false`
- **Severity:** Low
- **Remediation:** Update distribution config to set `Compress: true`
- **Remediation description:** Enables automatic gzip/brotli compression for supported content types

### CloudWatch Alarms

- **Check command:** `aws cloudwatch describe-alarms --alarm-name-prefix {distribution-name}`
- **Gap condition:** No alarms exist for 5xxErrorRate or Latency metrics
- **Severity:** High (production only)
- **Remediation:** Create CloudWatch alarms for `5xxErrorRate > 5%` and `OriginLatency > 2s`
- **Remediation description:** Alerts on elevated error rates and latency degradation

---

## Notes

- Production MVA is the superset — all lower tiers are subsets
- Higher layers (org/BU) can ADD items but cannot remove core items
- Only the user can accept gaps below core MVA (non-production only)
- See `skills/aws/aws-well-architected/SKILL.md` for evaluation instructions
- See `skills/aws/aws-cli-playbook/commands/cloudfront.md` for CLI command reference
