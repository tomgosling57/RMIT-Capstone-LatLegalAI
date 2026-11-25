# Jira Credential Setup — Detailed Guide

## Generating an API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Give it a label (e.g. "Claude Skill")
4. Copy the token immediately — Atlassian only shows it once

## Finding Your Base URL

Your Jira base URL is the domain you see in your browser when using Jira:
- Atlassian Cloud: `https://yourorg.atlassian.net`
- Server / Data Center (self-hosted): `https://jira.yourcompany.com` (or similar)

## Config File Location

Configuration can be stored in multiple locations (checked in order):
1. **Project-specific**: `.agents/jira-config.json` (recommended for team projects)
2. **User global**: `~/.agents/jira-config.json` (for personal use across projects)
3. **Legacy**: `~/.claude-skills/jira-config.json` (backward compatibility)

### Full config schema

```json
{
  "base_url": "https://yourorg.atlassian.net",
  "email": "you@yourcompany.com",
  "api_token": "YOUR_TOKEN_HERE",
  "default_project": "ENG"
}
```

`default_project` is optional. When set, Claude will use it when creating or searching issues without an explicit project key.

## Updating / Rotating Credentials

To update any field, either:

**Option A — Manually edit the file:**
```bash
# For project-specific config
nano .agents/jira-config.json

# For user global config
nano ~/.agents/jira-config.json
```

**Option B — Use the setup script:**
```bash
./.agents/scripts/jira/jira-setup.sh
```

**Option C — Ask Claude:**
> "Update my Jira token to [new token]"
> "Change my Jira base URL to [new url]"

Claude will patch only the field you specify.

## Testing Connectivity

```bash
# Load config (using project-specific as example)
CONFIG=$(cat .agents/jira-config.json)
URL=$(echo $CONFIG | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")
EMAIL=$(echo $CONFIG | python3 -c "import sys,json; print(json.load(sys.stdin)['email'])")
TOKEN=$(echo $CONFIG | python3 -c "import sys,json; print(json.load(sys.stdin)['api_token'])")
AUTH=$(echo -n "$EMAIL:$TOKEN" | base64)

# Test
curl -s \
  -H "Authorization: Basic $AUTH" \
  -H "Accept: application/json" \
  "$URL/rest/api/3/myself" | python3 -m json.tool
```

A successful response looks like:
```json
{
  "emailAddress": "you@yourcompany.com",
  "displayName": "Your Name",
  "accountId": "..."
}
```

## Troubleshooting Auth Errors

| Problem | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` | Wrong email or token | Regenerate token at id.atlassian.com |
| `403 Forbidden` | Correct auth but no permission | Check Jira project roles |
| `curl: Could not resolve host` | Wrong base URL | Double-check URL format |

## Security

- The config file is set to `chmod 600` (only your user can read it)
- Never share your API token
- Tokens can be revoked at https://id.atlassian.com/manage-profile/security/api-tokens at any time
