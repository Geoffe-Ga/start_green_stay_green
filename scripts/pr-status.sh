#!/usr/bin/env bash
# scripts/pr-status.sh - Monitor PR status, CI checks, and reviews
# Usage: ./scripts/pr-status.sh [PR_NUMBERS...] [--verbose] [--json] [--watch] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
JSON_OUTPUT=false
WATCH_MODE=false
WATCH_INTERVAL=30
START_TIME=$(date +%s)

# Parse command line arguments
PR_NUMBERS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --interval)
            WATCH_INTERVAL="$2"
            shift 2
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help)
            cat << HELP
Usage: $(basename "$0") [PR_NUMBERS...] [OPTIONS]

Monitor GitHub PR status including CI checks and Claude reviews.

ARGUMENTS:
    PR_NUMBERS      One or more PR numbers to check (e.g., 63 64 65)
                    If not provided, checks all open PRs

OPTIONS:
    --verbose       Show detailed output
    --json          Output results in JSON format
    --watch         Continuously monitor (refresh every 30s)
    --interval N    Set watch interval to N seconds (default: 30)
    --version       Show version and exit
    --help          Display this help message

EXIT CODES:
    0               All PRs passing or status retrieved successfully
    1               One or more PRs failing
    2               Error (missing dependencies, invalid arguments)

EXAMPLES:
    $(basename "$0") 63 64 65           # Check specific PRs
    $(basename "$0") --verbose          # Check all open PRs with details
    $(basename "$0") 63 --watch         # Continuously monitor PR #63
    $(basename "$0") 63 64 --json       # JSON output for PRs 63 and 64

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
HELP
            exit 0
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
        *)
            PR_NUMBERS+=("$1")
            shift
            ;;
    esac
done

# Check for gh CLI
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed" >&2
    echo "Install: https://cli.github.com/" >&2
    exit 2
fi

# Get repository info
REPO_OWNER=$(gh repo view --json owner --jq '.owner.login' 2>/dev/null || echo "")
REPO_NAME=$(gh repo view --json name --jq '.name' 2>/dev/null || echo "")

if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
    echo "Error: Not in a GitHub repository or gh CLI not authenticated" >&2
    exit 2
fi

# If no PR numbers provided, get all open PRs
if [[ ${#PR_NUMBERS[@]} -eq 0 ]]; then
    mapfile -t PR_NUMBERS < <(gh pr list --state open --json number --jq '.[].number')
    if [[ ${#PR_NUMBERS[@]} -eq 0 ]]; then
        echo "No open PRs found"
        exit 0
    fi
fi

# Function to check a single PR
check_pr() {
    local pr_number="$1"
    local pr_data
    local ci_checks
    local review_comments
    
    # Get PR details
    pr_data=$(gh pr view "$pr_number" --json number,title,state,mergeable,url,author 2>/dev/null || echo "")
    
    if [[ -z "$pr_data" ]]; then
        echo "Error: PR #$pr_number not found" >&2
        return 1
    fi
    
    local pr_title=$(echo "$pr_data" | jq -r '.title')
    local pr_state=$(echo "$pr_data" | jq -r '.state')
    local pr_mergeable=$(echo "$pr_data" | jq -r '.mergeable')
    local pr_url=$(echo "$pr_data" | jq -r '.url')
    local pr_author=$(echo "$pr_data" | jq -r '.author.login')
    
    # Get CI checks
    ci_checks=$(gh pr checks "$pr_number" 2>&1 || echo "no checks reported")
    
    # Get Claude review comments
    review_comments=$(gh api "repos/$REPO_OWNER/$REPO_NAME/issues/$pr_number/comments" \
        --jq '.[] | select(.user.login == "claude[bot]") | {created_at: .created_at, body: .body}' 2>/dev/null || echo "")
    
    # Count check statuses
    local total_checks=0
    local passing_checks=0
    local failing_checks=0
    local pending_checks=0

    if [[ "$ci_checks" != "no checks reported"* ]]; then
        total_checks=$(echo "$ci_checks" | wc -l | xargs)
        passing_checks=$(echo "$ci_checks" | grep -c "pass" 2>/dev/null || true)
        failing_checks=$(echo "$ci_checks" | grep -c "fail" 2>/dev/null || true)
        pending_checks=$(echo "$ci_checks" | grep -c "pending" 2>/dev/null || true)
        # Ensure counts are integers
        passing_checks=${passing_checks:-0}
        failing_checks=${failing_checks:-0}
        pending_checks=${pending_checks:-0}
        total_checks=${total_checks:-0}
    fi
    
    # Determine overall status
    local overall_status="unknown"
    if [[ "$ci_checks" == "no checks reported"* ]]; then
        overall_status="no_ci"
    elif [[ $pending_checks -gt 0 ]]; then
        overall_status="pending"
    elif [[ $failing_checks -gt 0 ]]; then
        overall_status="failing"
    elif [[ $passing_checks -gt 0 ]]; then
        overall_status="passing"
    fi
    
    # Check for Claude LGTM
    local claude_lgtm="not_found"
    if [[ -n "$review_comments" ]]; then
        if echo "$review_comments" | grep -qi "LGTM\|looks good to merge\|ready to merge\|approved"; then
            claude_lgtm="approved"
        else
            claude_lgtm="commented"
        fi
    fi
    
    # Output based on format
    if $JSON_OUTPUT; then
        cat << JSON
{
  "pr_number": $pr_number,
  "title": $(echo "$pr_title" | jq -R .),
  "state": "$pr_state",
  "mergeable": "$pr_mergeable",
  "url": "$pr_url",
  "author": "$pr_author",
  "ci_status": {
    "overall": "$overall_status",
    "total_checks": $total_checks,
    "passing": $passing_checks,
    "failing": $failing_checks,
    "pending": $pending_checks
  },
  "claude_review": "$claude_lgtm"
}
JSON
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "PR #$pr_number: $pr_title"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Author:    $pr_author"
        echo "State:     $pr_state"
        echo "Mergeable: $pr_mergeable"
        echo "URL:       $pr_url"
        echo ""
        
        # CI Status
        echo "CI Status: "
        case $overall_status in
            passing)
                echo "  ✅ ALL CHECKS PASSING ($passing_checks/$total_checks)"
                ;;
            failing)
                echo "  ❌ CHECKS FAILING ($failing_checks failures, $passing_checks passing)"
                ;;
            pending)
                echo "  ⏳ CHECKS PENDING ($pending_checks pending, $passing_checks passing)"
                ;;
            no_ci)
                echo "  ⏸️  NO CI CHECKS REPORTED YET"
                ;;
            *)
                echo "  ❓ UNKNOWN STATUS"
                ;;
        esac
        
        # Show individual checks in verbose mode
        if $VERBOSE && [[ "$ci_checks" != "no checks reported"* ]]; then
            echo ""
            echo "Check Details:"
            echo "$ci_checks" | while IFS=$'\t' read -r name status time url; do
                case $status in
                    pass)
                        echo "  ✅ $name ($time)"
                        ;;
                    fail)
                        echo "  ❌ $name"
                        ;;
                    pending)
                        echo "  ⏳ $name"
                        ;;
                    *)
                        echo "  ⏸️  $name ($status)"
                        ;;
                esac
            done
        fi
        
        # Claude Review Status
        echo ""
        echo "Claude Review:"
        case $claude_lgtm in
            approved)
                echo "  ✅ LGTM - Ready to merge"
                ;;
            commented)
                echo "  💬 Comments provided (review details)"
                ;;
            not_found)
                echo "  ⏳ No review yet"
                ;;
        esac
        
        # Show review comments in verbose mode
        if $VERBOSE && [[ -n "$review_comments" ]]; then
            echo ""
            echo "Review Comments:"
            echo "$review_comments" | jq -r '.body' | head -20 | sed 's/^/  │ /'
            echo "  └─ [truncated, see PR for full review]"
        fi
        
        echo ""
    fi
    
    # Return failure if checks are failing
    if [[ "$overall_status" == "failing" ]]; then
        return 1
    fi
    
    return 0
}

# Main execution
main() {
    local exit_code=0
    local iteration=1
    
    while true; do
        if $WATCH_MODE && [[ $iteration -gt 1 ]]; then
            clear
            echo "🔄 Refreshing... (Iteration $iteration, Interval: ${WATCH_INTERVAL}s)"
            echo ""
        fi
        
        if ! $JSON_OUTPUT; then
            echo "Monitoring ${#PR_NUMBERS[@]} PR(s) in $REPO_OWNER/$REPO_NAME"
        fi
        
        if $JSON_OUTPUT; then
            echo "["
        fi
        
        local first=true
        for pr in "${PR_NUMBERS[@]}"; do
            if $JSON_OUTPUT && ! $first; then
                echo ","
            fi
            
            if ! check_pr "$pr"; then
                exit_code=1
            fi
            
            first=false
        done
        
        if $JSON_OUTPUT; then
            echo "]"
        fi
        
        # Show timing in verbose mode
        if $VERBOSE && ! $JSON_OUTPUT; then
            local end_time=$(date +%s)
            local duration=$((end_time - START_TIME))
            echo "Execution time: ${duration}s"
        fi
        
        # Break if not in watch mode
        if ! $WATCH_MODE; then
            break
        fi
        
        # Wait before next iteration
        if ! $JSON_OUTPUT; then
            echo ""
            echo "⏰ Waiting ${WATCH_INTERVAL}s before next check... (Press Ctrl+C to stop)"
        fi
        sleep "$WATCH_INTERVAL"
        iteration=$((iteration + 1))
    done
    
    return $exit_code
}

# Run main function
main

