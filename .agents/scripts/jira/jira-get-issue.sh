#!/bin/bash
# Get a Jira issue by key

source "$(dirname "$0")/jira-common.sh"

usage() {
    echo "Usage: $0 <issue-key> [fields]"
    echo "  issue-key: e.g., PROJ-123"
    echo "  fields: comma-separated list of fields to return (optional)"
    echo "          default: summary,status,assignee,priority,description,comment"
    echo
    echo "Examples:"
    echo "  $0 ENG-123"
    echo "  $0 ENG-123 summary,status,assignee"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

ISSUE_KEY="$1"
FIELDS="${2:-summary,status,assignee,priority,description,comment}"

load_config

echo "Fetching issue $ISSUE_KEY..." >&2

response=$(jira_request "GET" "issue/$ISSUE_KEY?fields=$FIELDS")
parsed=$(parse_response "$response")

if [[ $? -eq 0 ]]; then
    echo "$parsed" | pretty_json
else
    exit 1
fi