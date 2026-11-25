#!/bin/bash
# Jira credential setup script

# Determine where to save config
echo "=== Jira Credential Setup ==="
echo "This script will configure your Jira credentials for use with the Jira scripts."
echo
echo "Where would you like to save the configuration?"
echo "1. Project-specific (.agents/jira-config.json) - recommended for team projects"
echo "2. User global (~/.agents/jira-config.json) - for personal use across projects"
read -p "Choose [1 or 2]: " -n 1 -r
echo

if [[ $REPLY == "1" ]]; then
    CONFIG_DIR=".agents"
    CONFIG_FILE="$CONFIG_DIR/jira-config.json"
    echo "Using project-specific configuration."
elif [[ $REPLY == "2" ]]; then
    CONFIG_DIR="$HOME/.agents"
    CONFIG_FILE="$CONFIG_DIR/jira-config.json"
    echo "Using user-global configuration."
else
    echo "Invalid choice. Using project-specific by default."
    CONFIG_DIR=".agents"
    CONFIG_FILE="$CONFIG_DIR/jira-config.json"
fi

# Check if config already exists
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Existing configuration found:"
    cat "$CONFIG_FILE" | jq . 2>/dev/null || cat "$CONFIG_FILE"
    echo
    read -p "Do you want to overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Collect credentials
echo "Please provide your Jira credentials:"
echo

read -p "1. Jira Base URL (e.g., https://yourorg.atlassian.net): " BASE_URL
read -p "2. Email (your Atlassian account email): " EMAIL
read -p "3. API Token (generate at https://id.atlassian.com/manage-profile/security/api-tokens): " API_TOKEN
read -p "4. Default Project Key (optional, press Enter to skip): " DEFAULT_PROJECT

# Validate inputs
if [[ -z "$BASE_URL" || -z "$EMAIL" || -z "$API_TOKEN" ]]; then
    echo "Error: Base URL, Email, and API Token are required." >&2
    exit 1
fi

# Create config directory
mkdir -p "$CONFIG_DIR"

# Write config
cat > "$CONFIG_FILE" <<EOF
{
  "base_url": "$BASE_URL",
  "email": "$EMAIL",
  "api_token": "$API_TOKEN",
  "default_project": "$DEFAULT_PROJECT"
}
EOF

# Set secure permissions
chmod 600 "$CONFIG_FILE"

echo
echo "Configuration saved to $CONFIG_FILE"

# Test connectivity
echo
echo "Testing connectivity..."

AUTH=$(echo -n "$EMAIL:$API_TOKEN" | base64 | tr -d '\n')
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/myself")

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "✓ Successfully connected to Jira!"
    echo "You can now use the Jira scripts."
else
    echo "⚠ Connection test failed with HTTP code $HTTP_CODE"
    echo "Please verify your credentials and network connectivity."
    echo "Configuration was saved, but you may need to correct it."
fi