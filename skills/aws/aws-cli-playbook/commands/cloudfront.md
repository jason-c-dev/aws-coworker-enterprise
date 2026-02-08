# CloudFront CLI Reference

## Overview
Amazon CloudFront is a content delivery network (CDN) that accelerates delivery of websites, APIs, and other web assets. Use these commands to create and manage distributions, configure origins (including private S3 buckets), manage cache behaviors, create invalidations, and set up Origin Access Control (OAC) for secure S3 integration.

## Discovery Commands (Read-Only)

```bash
# List all CloudFront distributions
aws cloudfront list-distributions

# List distributions with key details (ID, domain, status)
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status,Origins:Origins.Items[0].DomainName}'

# Get detailed info about a specific distribution
aws cloudfront get-distribution --id E1234567890ABC

# Get distribution configuration (for modification)
aws cloudfront get-distribution-config --id E1234567890ABC

# List origin access controls (OAC)
aws cloudfront list-origin-access-controls

# Get specific origin access control details
aws cloudfront get-origin-access-control --id E1234567890ABC

# List cache policies
aws cloudfront list-cache-policies

# Get cache policy details
aws cloudfront get-cache-policy --id 658327ea-f89d-4fab-a63d-7e88639e58f6

# List origin request policies
aws cloudfront list-origin-request-policies

# List response headers policies
aws cloudfront list-response-headers-policies

# List invalidations for a distribution
aws cloudfront list-invalidations --distribution-id E1234567890ABC

# Get invalidation status
aws cloudfront get-invalidation --distribution-id E1234567890ABC --id I1234567890ABC

# List CloudFront functions
aws cloudfront list-functions

# Get function details
aws cloudfront describe-function --name my-function

# List key groups (for signed URLs/cookies)
aws cloudfront list-key-groups

# List public keys
aws cloudfront list-public-keys

# Get distribution tags
aws cloudfront list-tags-for-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E1234567890ABC

# Check CloudFront pricing class options
# (us-europe = PriceClass_100, us-europe-asia = PriceClass_200, all = PriceClass_All)
```

## Common Operations

```bash
# Create Origin Access Control (OAC) for S3
aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "my-oac",
    "Description": "OAC for private S3 bucket",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }'

# Create a basic distribution with S3 origin (using OAC)
aws cloudfront create-distribution \
  --distribution-config file://distribution-config.json

# Example distribution-config.json for S3 static site:
# {
#   "CallerReference": "unique-ref-$(date +%s)",
#   "Origins": {
#     "Quantity": 1,
#     "Items": [{
#       "Id": "S3-my-bucket",
#       "DomainName": "my-bucket.s3.us-east-1.amazonaws.com",
#       "S3OriginConfig": { "OriginAccessIdentity": "" },
#       "OriginAccessControlId": "E1234567890ABC"
#     }]
#   },
#   "DefaultCacheBehavior": {
#     "TargetOriginId": "S3-my-bucket",
#     "ViewerProtocolPolicy": "redirect-to-https",
#     "AllowedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] },
#     "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
#     "Compress": true
#   },
#   "DefaultRootObject": "index.html",
#   "Enabled": true,
#   "Comment": "Static site distribution",
#   "PriceClass": "PriceClass_100"
# }

# Update distribution configuration
# First get current config and ETag
aws cloudfront get-distribution-config --id E1234567890ABC > dist-config.json
# Edit the config (remove ETag from file, keep for --if-match)
aws cloudfront update-distribution \
  --id E1234567890ABC \
  --distribution-config file://dist-config-updated.json \
  --if-match ETAG123

# Create cache invalidation (clear CDN cache)
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"

# Create invalidation for specific paths
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/index.html" "/css/*" "/js/*"

# Add custom error response (e.g., SPA routing)
# Update distribution with custom error responses for 403/404 -> index.html
# (Requires full distribution update via get-distribution-config + update-distribution)

# Create CloudFront function (for simple transformations)
aws cloudfront create-function \
  --name my-function \
  --function-config '{
    "Comment": "Add security headers",
    "Runtime": "cloudfront-js-2.0"
  }' \
  --function-code fileb://function.js

# Publish CloudFront function
aws cloudfront publish-function \
  --name my-function \
  --if-match ETAG123

# Associate function with distribution
# (Requires updating distribution cache behavior)

# Add tags to distribution
aws cloudfront tag-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E1234567890ABC \
  --tags 'Items=[{Key=Environment,Value=production},{Key=Project,Value=website}]'

# Create public key (for signed URLs)
aws cloudfront create-public-key \
  --public-key-config '{
    "CallerReference": "unique-ref",
    "Name": "my-public-key",
    "EncodedKey": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
    "Comment": "For signed URLs"
  }'
```

## Mutation Commands (Require Approval)

```bash
# ⚠️ Disable distribution (must disable before delete)
aws cloudfront update-distribution \
  --id E1234567890ABC \
  --distribution-config file://disabled-config.json \
  --if-match ETAG123
# Note: Set "Enabled": false in config

# ⚠️ Delete distribution (must be disabled first, cannot be undone)
aws cloudfront delete-distribution --id E1234567890ABC --if-match ETAG123

# ⚠️ Delete origin access control
aws cloudfront delete-origin-access-control --id E1234567890ABC --if-match ETAG123

# ⚠️ Delete CloudFront function
aws cloudfront delete-function --name my-function --if-match ETAG123

# ⚠️ Delete public key
aws cloudfront delete-public-key --id K1234567890ABC --if-match ETAG123

# ⚠️ Delete key group
aws cloudfront delete-key-group --id KG1234567890ABC --if-match ETAG123

# ⚠️ Remove tags from distribution
aws cloudfront untag-resource \
  --resource arn:aws:cloudfront::123456789012:distribution/E1234567890ABC \
  --tag-keys 'Items=["Environment","Project"]'

# ⚠️ Invalidate all cached content (may cause origin load spike)
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

## Best Practices

- **S3 Static Hosting Pattern**: Use private S3 bucket + CloudFront with Origin Access Control (OAC). Never make S3 buckets public; OAC allows CloudFront to access private bucket securely. Add bucket policy granting CloudFront access.
- **HTTPS Everywhere**: Set `ViewerProtocolPolicy` to `redirect-to-https` for all behaviors
- **Default Root Object**: Set `DefaultRootObject` to `index.html` for static sites
- **Compression**: Enable `Compress: true` in cache behaviors for automatic gzip/brotli
- **Cache Policies**: Use managed cache policies (CachingOptimized: 658327ea-f89d-4fab-a63d-7e88639e58f6) for static content
- **SPA Routing**: Configure custom error response: 403/404 → /index.html with 200 status for single-page apps
- **Price Class**: Use `PriceClass_100` (US/Europe) for cost savings if global reach not needed
- **Invalidations**: Invalidations cost money after 1000/month; use versioned file names instead when possible
- **OAC vs OAI**: Origin Access Control (OAC) is the modern replacement for Origin Access Identity (OAI); prefer OAC for new distributions
- **Logging**: Enable access logging to S3 for audit trails and analytics
- **Security Headers**: Use response headers policy or CloudFront Functions to add security headers (CSP, HSTS, X-Frame-Options)
- **Geo Restrictions**: Use geographic restrictions for compliance or licensing requirements

## S3 Bucket Policy for CloudFront OAC

When using OAC, add this policy to your S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipal",
    "Effect": "Allow",
    "Principal": {
      "Service": "cloudfront.amazonaws.com"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/E1234567890ABC"
      }
    }
  }]
}
```

## Related Skills

- S3 - Store objects that CloudFront distributes; configure bucket policies for OAC
- Route 53 - Create custom domain aliases for CloudFront distributions
- ACM - Provision SSL/TLS certificates for HTTPS (must be in us-east-1 for CloudFront)
- WAF - Attach Web Application Firewall rules to distributions
- Lambda@Edge - Run serverless code at edge locations for complex transformations
