#!/bin/bash
#
# AWS Coworker Test Hooks
# Pre-test and post-test hooks for resource tracking and validation
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(dirname "$SCRIPT_DIR")"
STATE_DIR="${TESTS_DIR}/state"

AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

#######################################
# Pre-Test Hook
# Call this before running a test
#######################################
pre_test() {
    local test_id="${1:-unknown}"
    local snapshot_file="${STATE_DIR}/pre-${test_id}-$(date +%Y%m%d-%H%M%S).json"

    mkdir -p "$STATE_DIR"

    echo -e "${GREEN}[PRE-TEST]${NC} Taking snapshot for test: $test_id"

    cat > "$snapshot_file" << EOF
{
  "test_id": "${test_id}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase": "pre",
  "resources": {
    "ec2_instances": $(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'Reservations[*].Instances[*].InstanceId' --output json 2>/dev/null | jq -c 'flatten // []'),
    "security_groups": $(aws ec2 describe-security-groups --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'SecurityGroups[*].GroupId' --output json 2>/dev/null | jq -c '. // []'),
    "key_pairs": $(aws ec2 describe-key-pairs --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'KeyPairs[*].KeyName' --output json 2>/dev/null | jq -c '. // []'),
    "ebs_volumes": $(aws ec2 describe-volumes --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'Volumes[*].VolumeId' --output json 2>/dev/null | jq -c '. // []')
  }
}
EOF

    echo -e "${GREEN}[PRE-TEST]${NC} Snapshot saved: $snapshot_file"
    echo "$snapshot_file"
}

#######################################
# Post-Test Hook
# Call this after running a test
#######################################
post_test() {
    local test_id="${1:-unknown}"
    local pre_snapshot="${2:-}"
    local post_file="${STATE_DIR}/post-${test_id}-$(date +%Y%m%d-%H%M%S).json"

    echo -e "${GREEN}[POST-TEST]${NC} Taking post-test snapshot for: $test_id"

    cat > "$post_file" << EOF
{
  "test_id": "${test_id}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase": "post",
  "resources": {
    "ec2_instances": $(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'Reservations[*].Instances[*].InstanceId' --output json 2>/dev/null | jq -c 'flatten // []'),
    "security_groups": $(aws ec2 describe-security-groups --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'SecurityGroups[*].GroupId' --output json 2>/dev/null | jq -c '. // []'),
    "key_pairs": $(aws ec2 describe-key-pairs --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'KeyPairs[*].KeyName' --output json 2>/dev/null | jq -c '. // []'),
    "ebs_volumes": $(aws ec2 describe-volumes --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'Volumes[*].VolumeId' --output json 2>/dev/null | jq -c '. // []')
  }
}
EOF

    # Compare if pre-snapshot provided
    if [[ -n "$pre_snapshot" && -f "$pre_snapshot" ]]; then
        echo -e "${GREEN}[POST-TEST]${NC} Comparing snapshots..."
        diff_resources "$pre_snapshot" "$post_file"
    fi

    echo "$post_file"
}

#######################################
# Diff Resources
# Compare pre and post snapshots
#######################################
diff_resources() {
    local pre_file="$1"
    local post_file="$2"

    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "  Resource Diff Report"
    echo "═══════════════════════════════════════════════════"

    # EC2 Instances
    local pre_instances=$(jq -r '.resources.ec2_instances[]' "$pre_file" 2>/dev/null | sort)
    local post_instances=$(jq -r '.resources.ec2_instances[]' "$post_file" 2>/dev/null | sort)

    local new_instances=$(comm -13 <(echo "$pre_instances") <(echo "$post_instances") | grep -v '^$' || true)
    local removed_instances=$(comm -23 <(echo "$pre_instances") <(echo "$post_instances") | grep -v '^$' || true)

    if [[ -n "$new_instances" ]]; then
        echo -e "${YELLOW}NEW EC2 Instances:${NC}"
        echo "$new_instances" | while read -r i; do echo "  + $i"; done
    fi

    if [[ -n "$removed_instances" ]]; then
        echo -e "${GREEN}Removed EC2 Instances:${NC}"
        echo "$removed_instances" | while read -r i; do echo "  - $i"; done
    fi

    # Security Groups
    local pre_sgs=$(jq -r '.resources.security_groups[]' "$pre_file" 2>/dev/null | sort)
    local post_sgs=$(jq -r '.resources.security_groups[]' "$post_file" 2>/dev/null | sort)

    local new_sgs=$(comm -13 <(echo "$pre_sgs") <(echo "$post_sgs") | grep -v '^$' || true)
    local removed_sgs=$(comm -23 <(echo "$pre_sgs") <(echo "$post_sgs") | grep -v '^$' || true)

    if [[ -n "$new_sgs" ]]; then
        echo -e "${YELLOW}NEW Security Groups:${NC}"
        echo "$new_sgs" | while read -r sg; do echo "  + $sg"; done
    fi

    if [[ -n "$removed_sgs" ]]; then
        echo -e "${GREEN}Removed Security Groups:${NC}"
        echo "$removed_sgs" | while read -r sg; do echo "  - $sg"; done
    fi

    # Key Pairs
    local pre_kps=$(jq -r '.resources.key_pairs[]' "$pre_file" 2>/dev/null | sort)
    local post_kps=$(jq -r '.resources.key_pairs[]' "$post_file" 2>/dev/null | sort)

    local new_kps=$(comm -13 <(echo "$pre_kps") <(echo "$post_kps") | grep -v '^$' || true)
    local removed_kps=$(comm -23 <(echo "$pre_kps") <(echo "$post_kps") | grep -v '^$' || true)

    if [[ -n "$new_kps" ]]; then
        echo -e "${YELLOW}NEW Key Pairs:${NC}"
        echo "$new_kps" | while read -r kp; do echo "  + $kp"; done
    fi

    if [[ -n "$removed_kps" ]]; then
        echo -e "${GREEN}Removed Key Pairs:${NC}"
        echo "$removed_kps" | while read -r kp; do echo "  - $kp"; done
    fi

    # Summary
    echo ""
    echo "───────────────────────────────────────────────────"

    local total_new=0
    [[ -n "$new_instances" ]] && total_new=$((total_new + $(echo "$new_instances" | wc -l)))
    [[ -n "$new_sgs" ]] && total_new=$((total_new + $(echo "$new_sgs" | wc -l)))
    [[ -n "$new_kps" ]] && total_new=$((total_new + $(echo "$new_kps" | wc -l)))

    if [[ $total_new -gt 0 ]]; then
        echo -e "${YELLOW}⚠ WARNING: $total_new new resource(s) detected${NC}"
        echo "  Run cleanup to remove test resources"
    else
        echo -e "${GREEN}✓ No orphaned resources detected${NC}"
    fi

    echo "═══════════════════════════════════════════════════"
    echo ""
}

#######################################
# Verify Clean State
# Check that no test resources exist
#######################################
verify_clean() {
    echo -e "${GREEN}[VERIFY]${NC} Checking for orphaned test resources..."

    local has_orphans=false

    # Check EC2 instances
    local test_instances=$(aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" "Name=instance-state-name,Values=running,stopped,pending" \
        --query 'Reservations[*].Instances[*].InstanceId' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$test_instances" ]]; then
        echo -e "${RED}✗ Found test EC2 instances:${NC}"
        echo "$test_instances" | tr '\t' '\n' | while read -r i; do echo "    $i"; done
        has_orphans=true
    fi

    # Check Security Groups
    local test_sgs=$(aws ec2 describe-security-groups \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'SecurityGroups[*].GroupId' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$test_sgs" ]]; then
        echo -e "${RED}✗ Found test Security Groups:${NC}"
        echo "$test_sgs" | tr '\t' '\n' | while read -r sg; do echo "    $sg"; done
        has_orphans=true
    fi

    # Check Key Pairs
    local test_kps=$(aws ec2 describe-key-pairs \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'KeyPairs[*].KeyName' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$test_kps" ]]; then
        echo -e "${RED}✗ Found test Key Pairs:${NC}"
        echo "$test_kps" | tr '\t' '\n' | while read -r kp; do echo "    $kp"; done
        has_orphans=true
    fi

    if [[ "$has_orphans" == "true" ]]; then
        echo ""
        echo -e "${RED}✗ Orphaned resources found!${NC}"
        echo "  Run: ./test-harness.sh cleanup"
        return 1
    else
        echo -e "${GREEN}✓ No orphaned test resources found${NC}"
        return 0
    fi
}

#######################################
# Usage
#######################################
usage() {
    cat << EOF
AWS Coworker Test Hooks

Usage: $0 <command> [args]

Commands:
  pre <test_id>              Take pre-test snapshot
  post <test_id> [pre_file]  Take post-test snapshot and diff
  diff <pre_file> <post_file> Compare two snapshots
  verify                      Check for orphaned test resources

Examples:
  # Before running T9 (EC2 launch test)
  pre_snapshot=\$($0 pre T9)

  # After running T9
  $0 post T9 \$pre_snapshot

  # Verify no orphans remain
  $0 verify

EOF
}

#######################################
# Main
#######################################
case "${1:-}" in
    pre)
        pre_test "${2:-unknown}"
        ;;
    post)
        post_test "${2:-unknown}" "${3:-}"
        ;;
    diff)
        diff_resources "${2:-}" "${3:-}"
        ;;
    verify)
        verify_clean
        ;;
    *)
        usage
        ;;
esac
