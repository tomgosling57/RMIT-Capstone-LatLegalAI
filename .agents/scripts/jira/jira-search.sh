#!/bin/bash
# Search Jira issues with JQL

source "$(dirname "$0")/jira-common.sh"

usage() {
    cat <<EOF
Usage: $0 <jql-query> [options]
  jql-query: JQL query string (enclose in quotes if it contains spaces)
  
Options:
  -f, --fields <fields>    Comma-separated fields to return (default: summary,status,assignee,priority)
  -m, --max <number>       Maximum results (default: 50)
  -p, --pretty             Pretty print output
  -r, --raw                Raw JSON output
  
Examples:
  $0 'project = ENG AND status = "In Progress"'
  $0 'assignee = currentUser() ORDER BY updated DESC' -f summary,status -m 10
  $0 'text ~ "bug"' --pretty
EOF
    exit 1
}

# Default values
JQL=""
FIELDS="summary,status,assignee,priority"
MAX_RESULTS=50
PRETTY=false
RAW=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -f|--fields)
            FIELDS="$2"
            shift 2
            ;;
        -m|--max)
            MAX_RESULTS="$2"
            shift 2
            ;;
        -p|--pretty)
            PRETTY=true
            shift
            ;;
        -r|--raw)
            RAW=true
            shift
            ;;
        *)
            if [[ -z "$JQL" ]]; then
                JQL="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                usage
            fi
            shift
            ;;
    esac
done

if [[ -z "$JQL" ]]; then
    echo "Error: JQL query is required." >&2
    usage
fi

load_config

echo "Searching with JQL: $JQL" >&2

# URL encode the JQL
ENCODED_JQL=$(url_encode "$JQL")

response=$(jira_request "GET" "search/jql?jql=$ENCODED_JQL&maxResults=$MAX_RESULTS&fields=$FIELDS")
parsed=$(parse_response "$response")

if [[ $? -ne 0 ]]; then
    exit 1
fi

if [[ "$RAW" = true ]]; then
    echo "$parsed"
elif [[ "$PRETTY" = true ]]; then
    echo "$parsed" | pretty_json
else
    # Extract and display a summary table
    echo "$parsed" | jq -r "
        .issues[] | 
        \"\(.key) | \(.fields.summary // \"N/A\") | \(.fields.status.name // \"N/A\") | \(.fields.assignee.displayName // \"Unassigned\")\"
    " | column -t -s '|'
    
    # Show total count
    total=$(echo "$parsed" | jq '.total')
    echo
    echo "Total issues: $total (showing up to $MAX_RESULTS)"
fi