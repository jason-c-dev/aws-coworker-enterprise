#!/bin/bash
#
# AgentCore Deployment Test Prerequisites Check
# Run this before D-D1 through D-D5 tests
#

set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-aws-coworker-test}"
AWS_REGION="${AWS_REGION:-us-east-1}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "${GREEN}  ✓ $1${NC}"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}  ✗ $1${NC}"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
    ((WARN++))
}

echo "═══════════════════════════════════════════════════"
echo "  AgentCore Deployment Test Prerequisites"
echo "  Profile: $AWS_PROFILE | Region: $AWS_REGION"
echo "═══════════════════════════════════════════════════"
echo ""

# 1. Bedrock Model Access
echo "1. Bedrock Model Access"
if aws bedrock list-foundation-models \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --by-provider anthropic \
    --query 'modelSummaries[0].modelId' \
    --output text 2>/dev/null | grep -q "anthropic"; then
    check_pass "Anthropic models available in $AWS_REGION"
else
    check_fail "No Anthropic models found — enable Bedrock model access in the console"
fi

# 2. ECR Repository
echo ""
echo "2. ECR Repository"
if aws ecr describe-repositories \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --repository-names aws-coworker 2>/dev/null | grep -q "aws-coworker"; then
    check_pass "ECR repository 'aws-coworker' exists"
else
    check_fail "ECR repository 'aws-coworker' not found"
    echo "       Create it: aws ecr create-repository --repository-name aws-coworker --profile $AWS_PROFILE --region $AWS_REGION"
fi

# 3. VPC Infrastructure
echo ""
echo "3. VPC Infrastructure"
PRIVATE_SUBNETS=$(aws ec2 describe-subnets \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --filters "Name=map-public-ip-on-launch,Values=false" \
    --query 'Subnets[*].[SubnetId,AvailabilityZone]' \
    --output text 2>/dev/null || echo "")

if [[ -z "$PRIVATE_SUBNETS" ]]; then
    check_fail "No private subnets found"
    echo "       Create a VPC with private subnets in at least 2 AZs"
else
    SUBNET_COUNT=$(echo "$PRIVATE_SUBNETS" | wc -l | tr -d ' ')
    AZ_COUNT=$(echo "$PRIVATE_SUBNETS" | awk '{print $2}' | sort -u | wc -l | tr -d ' ')
    if [[ "$AZ_COUNT" -ge 2 ]]; then
        check_pass "Private subnets found: $SUBNET_COUNT subnets across $AZ_COUNT AZs"
    else
        check_warn "Private subnets found but only in $AZ_COUNT AZ (recommend 2+)"
    fi
fi

SG_COUNT=$(aws ec2 describe-security-groups \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --query 'SecurityGroups | length(@)' \
    --output text 2>/dev/null || echo "0")
if [[ "$SG_COUNT" -gt 0 ]]; then
    check_pass "Security groups available: $SG_COUNT"
else
    check_fail "No security groups found"
fi

# 4. IAM Permissions
echo ""
echo "4. IAM Permissions"
CALLER=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --output json 2>/dev/null || echo "")
if [[ -n "$CALLER" ]]; then
    ACCOUNT=$(echo "$CALLER" | jq -r '.Account')
    ARN=$(echo "$CALLER" | jq -r '.Arn')
    check_pass "Authenticated as: $ARN (Account: $ACCOUNT)"
else
    check_fail "Cannot authenticate with profile $AWS_PROFILE"
fi

# Test key permissions
if aws bedrock-agentcore-control help 2>&1 | grep -q "AVAILABLE COMMANDS\|Available Commands\|list-agent-runtimes"; then
    check_pass "bedrock-agentcore-control CLI commands available"
elif aws bedrock-agentcore-control list-agent-runtimes --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null; then
    check_pass "bedrock-agentcore-control API access confirmed"
else
    check_warn "Cannot verify bedrock-agentcore-control access — may need to update AWS CLI or check permissions"
fi

# 5. CLAUDE_CODE_USE_BEDROCK
echo ""
echo "5. CLAUDE_CODE_USE_BEDROCK Environment Variable"
if [[ "${CLAUDE_CODE_USE_BEDROCK:-}" == "1" ]]; then
    check_pass "CLAUDE_CODE_USE_BEDROCK=1 is set"
else
    check_fail "CLAUDE_CODE_USE_BEDROCK is not set to 1"
    echo "       Set it: export CLAUDE_CODE_USE_BEDROCK=1"
    echo "       Persist: echo 'export CLAUDE_CODE_USE_BEDROCK=1' >> ~/.zshrc"
fi

# 6. AgentCore CLI Available
echo ""
echo "6. AgentCore CLI"
AWS_VERSION=$(aws --version 2>&1 || echo "unknown")
echo "   AWS CLI version: $AWS_VERSION"
if echo "$AWS_VERSION" | grep -qE "aws-cli/2\.(1[5-9]|[2-9][0-9])"; then
    check_pass "AWS CLI version supports bedrock-agentcore"
else
    check_warn "AWS CLI may need updating for bedrock-agentcore support — verify with: aws bedrock-agentcore-control help"
fi

# 7. Clean State
echo ""
echo "7. Clean State"
EXISTING_RUNTIMES=$(aws bedrock-agentcore-control list-agent-runtimes \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --query 'agentRuntimeSummaries | length(@)' \
    --output text 2>/dev/null || echo "0")

if [[ "$EXISTING_RUNTIMES" == "0" ]]; then
    check_pass "No existing agent runtimes (clean state)"
else
    check_warn "$EXISTING_RUNTIMES existing agent runtime(s) found — clean up before testing"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Results: ${GREEN}$PASS passed${NC} | ${RED}$FAIL failed${NC} | ${YELLOW}$WARN warnings${NC}"
echo "═══════════════════════════════════════════════════"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo -e "${RED}Fix $FAIL prerequisite(s) before running D-D tests.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}All prerequisites met. Ready to run D-D tests.${NC}"
    exit 0
fi
