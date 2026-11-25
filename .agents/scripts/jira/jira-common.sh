#!/bin/bash
# Common functions and configuration for Jira scripts

# Configuration file locations (in order of preference)
# Try to find project root by walking up from current directory
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/.agents/jira-config.json" ]]; then
            echo "$dir/.agents/jira-config.json"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    echo ""
}

PROJECT_CONFIG=$(find_project_root)

CONFIG_FILES=(
    "$PROJECT_CONFIG"                   # Project-specific (found by walking up)
    "$HOME/.agents/jira-config.json"    # User global
    "$HOME/.claude-skills/jira-config.json" # Legacy Claude location
)

# Load configuration
load_config() {
    local config_file
    for config_file in "${CONFIG_FILES[@]}"; do
        if [[ -f "$config_file" ]]; then
            CONFIG_FILE="$config_file"
            break
        fi
    done
    
    if [[ -z "$CONFIG_FILE" || ! -f "$CONFIG_FILE" ]]; then
        echo "Error: Jira configuration file not found." >&2
        echo "Checked locations:" >&2
        for config_file in "${CONFIG_FILES[@]}"; do
            echo "  - $config_file" >&2
        done
        echo "Run jira-setup to configure credentials." >&2
        exit 1
    fi
    
    echo "Using config: $CONFIG_FILE" >&2

    BASE_URL=$(jq -r '.base_url' "$CONFIG_FILE" 2>/dev/null)
    EMAIL=$(jq -r '.email' "$CONFIG_FILE" 2>/dev/null)
    API_TOKEN=$(jq -r '.api_token' "$CONFIG_FILE" 2>/dev/null)
    DEFAULT_PROJECT=$(jq -r '.default_project' "$CONFIG_FILE" 2>/dev/null)

    if [[ -z "$BASE_URL" || -z "$EMAIL" || -z "$API_TOKEN" ]]; then
        echo "Error: Missing required fields in configuration file." >&2
        exit 1
    fi

    # Generate auth header (remove newlines that base64 might add)
    AUTH=$(echo -n "$EMAIL:$API_TOKEN" | base64 | tr -d '\n')
}

# Make a Jira API request
jira_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    local curl_cmd=("curl" "-s" "-w" "%{http_code}" "-H" "Authorization: Basic $AUTH" "-H" "Accept: application/json")
    
    if [[ -n "$data" ]]; then
        curl_cmd+=("-H" "Content-Type: application/json" "-d" "$data")
    fi
    
    if [[ "$method" != "GET" ]]; then
        curl_cmd+=("-X" "$method")
    fi
    
    curl_cmd+=("$BASE_URL/rest/api/3/$endpoint")
    
    # Execute and capture response
    local response
    response=$("${curl_cmd[@]}" 2>/dev/null)
    
    # Separate HTTP status code from body
    local http_code="${response: -3}"
    local body="${response:0:${#response}-3}"
    
    echo "$http_code:$body"
}

# Parse response
parse_response() {
    local response="$1"
    local http_code="${response%%:*}"
    local body="${response#*:}"
    
    if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo "$body"
    else
        echo "Error: HTTP $http_code" >&2
        if [[ -n "$body" ]]; then
            echo "$body" | jq . 2>/dev/null || echo "$body" >&2
        fi
        return 1
    fi
}

# Pretty print JSON
pretty_json() {
    jq . 2>/dev/null || cat
}

# URL encode for JQL
url_encode() {
    python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

# Check if jq is installed
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is required but not installed." >&2
        echo "Install with: sudo apt-get install jq or brew install jq" >&2
        exit 1
    fi
}

# Initialize
check_dependencies