#!/bin/bash
#
# AWS Coworker Test Harness
# Tracks resources created during tests and ensures cleanup
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$(dirname "$SCRIPT_DIR")"
STATE_DIR="${TESTS_DIR}/state"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
STATE_FILE="${STATE_DIR}/test-run-${TIMESTAMP}.json"
LOG_FILE="${STATE_DIR}/test-run-${TIMESTAMP}.log"

# Defaults
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TTL_HOURS="${TTL_HOURS:-4}"
DRY_RUN="${DRY_RUN:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#######################################
# Logging
#######################################
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

#######################################
# State Management
#######################################
init_state() {
    mkdir -p "$STATE_DIR"
    cat > "$STATE_FILE" << EOF
{
  "test_run": "${TIMESTAMP}",
  "profile": "${AWS_PROFILE}",
  "region": "${AWS_REGION}",
  "ttl_hours": ${TTL_HOURS},
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "running",
  "resources": {
    "ec2_instances": [],
    "security_groups": [],
    "key_pairs": [],
    "s3_buckets": [],
    "ebs_volumes": [],
    "elastic_ips": [],
    "other": []
  },
  "cleanup_completed": false
}
EOF
    log "State file initialized: $STATE_FILE"
}

add_resource() {
    local resource_type="$1"
    local resource_id="$2"
    local resource_name="${3:-}"

    # Use jq to add resource to state
    local tmp_file=$(mktemp)
    jq --arg type "$resource_type" \
       --arg id "$resource_id" \
       --arg name "$resource_name" \
       --arg time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       '.resources[$type] += [{"id": $id, "name": $name, "created_at": $time, "cleaned": false}]' \
       "$STATE_FILE" > "$tmp_file" && mv "$tmp_file" "$STATE_FILE"

    log "Tracked resource: $resource_type/$resource_id"
}

mark_cleaned() {
    local resource_type="$1"
    local resource_id="$2"

    local tmp_file=$(mktemp)
    jq --arg type "$resource_type" \
       --arg id "$resource_id" \
       '(.resources[$type][] | select(.id == $id)).cleaned = true' \
       "$STATE_FILE" > "$tmp_file" && mv "$tmp_file" "$STATE_FILE"
}

#######################################
# Pre-Test Snapshot
#######################################
take_snapshot() {
    log "Taking pre-test snapshot..."

    local snapshot_file="${STATE_DIR}/snapshot-${TIMESTAMP}.json"

    # Get current resources
    cat > "$snapshot_file" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ec2_instances": $(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$AWS_REGION" \
      --query 'Reservations[*].Instances[*].InstanceId' --output json 2>/dev/null | jq -c 'flatten'),
  "security_groups": $(aws ec2 describe-security-groups --profile "$AWS_PROFILE" --region "$AWS_REGION" \
      --query 'SecurityGroups[*].GroupId' --output json 2>/dev/null | jq -c '.'),
  "key_pairs": $(aws ec2 describe-key-pairs --profile "$AWS_PROFILE" --region "$AWS_REGION" \
      --query 'KeyPairs[*].KeyName' --output json 2>/dev/null | jq -c '.'),
  "s3_buckets": $(aws s3api list-buckets --profile "$AWS_PROFILE" \
      --query 'Buckets[*].Name' --output json 2>/dev/null | jq -c '.')
}
EOF

    log_success "Snapshot saved: $snapshot_file"
    echo "$snapshot_file"
}

#######################################
# Resource Discovery (Find Test Resources)
#######################################
discover_test_resources() {
    log "Discovering resources tagged for cleanup..."

    # EC2 Instances
    local instances=$(aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`TestRun`].Value|[0]]' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$instances" ]]; then
        log "Found EC2 instances:"
        echo "$instances" | while read -r line; do
            echo "  - $line"
        done
    fi

    # Security Groups
    local sgs=$(aws ec2 describe-security-groups \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'SecurityGroups[*].[GroupId,GroupName]' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$sgs" ]]; then
        log "Found Security Groups:"
        echo "$sgs" | while read -r line; do
            echo "  - $line"
        done
    fi

    # S3 Buckets (need to check tags individually)
    log "Checking S3 buckets..."
    aws s3api list-buckets --profile "$AWS_PROFILE" --query 'Buckets[*].Name' --output text 2>/dev/null | \
    tr '\t' '\n' | while read -r bucket; do
        if [[ -n "$bucket" ]]; then
            local tags=$(aws s3api get-bucket-tagging --profile "$AWS_PROFILE" --bucket "$bucket" 2>/dev/null || echo "")
            if echo "$tags" | grep -q "aws-coworker-test"; then
                echo "  - s3://$bucket (tagged for cleanup)"
            fi
        fi
    done

    # Key Pairs
    local keypairs=$(aws ec2 describe-key-pairs \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'KeyPairs[*].KeyName' \
        --output text 2>/dev/null || echo "")

    if [[ -n "$keypairs" ]]; then
        log "Found Key Pairs:"
        echo "$keypairs" | tr '\t' '\n' | while read -r kp; do
            echo "  - $kp"
        done
    fi
}

#######################################
# Cleanup Functions
#######################################
cleanup_ec2_instances() {
    log "Cleaning up EC2 instances..."

    local instances=$(aws ec2 describe-instances \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" "Name=instance-state-name,Values=running,stopped,pending" \
        --query 'Reservations[*].Instances[*].InstanceId' \
        --output text 2>/dev/null || echo "")

    if [[ -z "$instances" ]]; then
        log_success "No EC2 instances to clean up"
        return
    fi

    for instance_id in $instances; do
        if [[ "$DRY_RUN" == "true" ]]; then
            log_warn "[DRY RUN] Would terminate: $instance_id"
        else
            log "Terminating instance: $instance_id"
            aws ec2 terminate-instances \
                --profile "$AWS_PROFILE" \
                --region "$AWS_REGION" \
                --instance-ids "$instance_id" > /dev/null
            log_success "Terminated: $instance_id"
        fi
    done
}

cleanup_security_groups() {
    log "Cleaning up Security Groups..."

    local sgs=$(aws ec2 describe-security-groups \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'SecurityGroups[*].GroupId' \
        --output text 2>/dev/null || echo "")

    if [[ -z "$sgs" ]]; then
        log_success "No Security Groups to clean up"
        return
    fi

    # Wait for instances to terminate first
    sleep 5

    for sg_id in $sgs; do
        if [[ "$DRY_RUN" == "true" ]]; then
            log_warn "[DRY RUN] Would delete: $sg_id"
        else
            log "Deleting security group: $sg_id"
            if aws ec2 delete-security-group \
                --profile "$AWS_PROFILE" \
                --region "$AWS_REGION" \
                --group-id "$sg_id" 2>/dev/null; then
                log_success "Deleted: $sg_id"
            else
                log_warn "Could not delete $sg_id (may be in use, will retry)"
            fi
        fi
    done
}

cleanup_key_pairs() {
    log "Cleaning up Key Pairs..."

    local keypairs=$(aws ec2 describe-key-pairs \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'KeyPairs[*].KeyName' \
        --output text 2>/dev/null || echo "")

    if [[ -z "$keypairs" ]]; then
        log_success "No Key Pairs to clean up"
        return
    fi

    for kp_name in $keypairs; do
        if [[ "$DRY_RUN" == "true" ]]; then
            log_warn "[DRY RUN] Would delete: $kp_name"
        else
            log "Deleting key pair: $kp_name"
            aws ec2 delete-key-pair \
                --profile "$AWS_PROFILE" \
                --region "$AWS_REGION" \
                --key-name "$kp_name" > /dev/null
            log_success "Deleted: $kp_name"

            # Also remove local key file if exists
            local key_file="$HOME/${kp_name}.pem"
            if [[ -f "$key_file" ]]; then
                rm -f "$key_file"
                log "Removed local key file: $key_file"
            fi
        fi
    done
}

cleanup_s3_buckets() {
    log "Cleaning up S3 buckets..."

    aws s3api list-buckets --profile "$AWS_PROFILE" --query 'Buckets[*].Name' --output text 2>/dev/null | \
    tr '\t' '\n' | while read -r bucket; do
        if [[ -n "$bucket" ]]; then
            local tags=$(aws s3api get-bucket-tagging --profile "$AWS_PROFILE" --bucket "$bucket" 2>/dev/null || echo "")
            if echo "$tags" | grep -q "aws-coworker-test"; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    log_warn "[DRY RUN] Would delete bucket: $bucket"
                else
                    log "Emptying and deleting bucket: $bucket"
                    aws s3 rm "s3://$bucket" --recursive --profile "$AWS_PROFILE" 2>/dev/null || true
                    aws s3api delete-bucket --profile "$AWS_PROFILE" --bucket "$bucket" 2>/dev/null || true
                    log_success "Deleted: $bucket"
                fi
            fi
        fi
    done
}

cleanup_elastic_ips() {
    log "Cleaning up Elastic IPs..."

    local eips=$(aws ec2 describe-addresses \
        --profile "$AWS_PROFILE" \
        --region "$AWS_REGION" \
        --filters "Name=tag:Purpose,Values=aws-coworker-test" \
        --query 'Addresses[*].AllocationId' \
        --output text 2>/dev/null || echo "")

    if [[ -z "$eips" ]]; then
        log_success "No Elastic IPs to clean up"
        return
    fi

    for eip_id in $eips; do
        if [[ "$DRY_RUN" == "true" ]]; then
            log_warn "[DRY RUN] Would release: $eip_id"
        else
            log "Releasing Elastic IP: $eip_id"
            aws ec2 release-address \
                --profile "$AWS_PROFILE" \
                --region "$AWS_REGION" \
                --allocation-id "$eip_id" > /dev/null
            log_success "Released: $eip_id"
        fi
    done
}

cleanup_all() {
    log "Starting full cleanup..."

    # Order matters - instances first, then dependent resources
    cleanup_ec2_instances

    # Wait for instances to fully terminate
    log "Waiting for instances to terminate..."
    sleep 10

    cleanup_security_groups
    cleanup_key_pairs
    cleanup_s3_buckets
    cleanup_elastic_ips

    log_success "Cleanup complete!"
}

#######################################
# Trap for Ctrl+C
#######################################
trap_handler() {
    echo ""
    log_warn "Interrupt received!"
    echo ""
    read -p "Do you want to run cleanup before exiting? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_all
    else
        log_warn "Skipping cleanup. Run './test-harness.sh cleanup' later."
    fi
    exit 1
}

trap trap_handler SIGINT SIGTERM

#######################################
# Main Commands
#######################################
cmd_start() {
    log "═══════════════════════════════════════════════════"
    log "  AWS Coworker Test Harness"
    log "  Profile: $AWS_PROFILE | Region: $AWS_REGION"
    log "  TTL: $TTL_HOURS hours | Run ID: $TIMESTAMP"
    log "═══════════════════════════════════════════════════"

    init_state
    take_snapshot

    echo ""
    log "Test environment ready. Resources will be tagged with:"
    echo "  Purpose=aws-coworker-test"
    echo "  TestRun=$TIMESTAMP"
    echo "  TTL=$TTL_HOURS"
    echo ""
    log "Run tests now. When done, run: $0 cleanup"
    log "Press Ctrl+C to interrupt and optionally cleanup."
}

cmd_status() {
    log "Current test resources:"
    discover_test_resources
}

cmd_cleanup() {
    log "═══════════════════════════════════════════════════"
    log "  Cleanup Mode"
    log "  Profile: $AWS_PROFILE | Region: $AWS_REGION"
    log "═══════════════════════════════════════════════════"

    discover_test_resources

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No resources will be deleted"
    fi

    read -p "Proceed with cleanup? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_all
    else
        log "Cleanup cancelled"
    fi
}

cmd_help() {
    cat << EOF
AWS Coworker Test Harness

Usage: $0 <command> [options]

Commands:
  start     Initialize test session, take snapshot, prepare for tests
  status    Show current test resources that would be cleaned up
  cleanup   Clean up all test resources (interactive)

Options:
  AWS_PROFILE=name    AWS profile to use (default: default)
  AWS_REGION=region   AWS region (default: us-east-1)
  TTL_HOURS=n         Time-to-live for resources (default: 4)
  DRY_RUN=true        Show what would be deleted without deleting

Examples:
  $0 start                          # Start test session
  $0 status                         # Show test resources
  $0 cleanup                        # Interactive cleanup
  DRY_RUN=true $0 cleanup           # Preview cleanup
  AWS_REGION=us-west-2 $0 cleanup   # Cleanup in specific region

EOF
}

#######################################
# Entry Point
#######################################
case "${1:-help}" in
    start)
        cmd_start
        ;;
    status)
        cmd_status
        ;;
    cleanup)
        cmd_cleanup
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
