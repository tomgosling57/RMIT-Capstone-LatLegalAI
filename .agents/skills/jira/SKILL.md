---
name: jira
description: >
  Use this skill whenever the user wants to interact with Jira — reading issues,
  creating issues, editing/updating issues, managing sprints, searching with JQL,
  transitioning issue status, adding comments, assigning issues, or setting up
  Jira credentials/configuration. Trigger on any mention of "Jira", "JIRA",
  "issue", "ticket", "sprint", "backlog", "board", "epic", "story", "bug report",
  or any Jira-specific field like "JQL", "issue key", "assignee", or "story points".
  Always use this skill if the user wants to do anything with their Jira board,
  even if they only say something casual like "add a ticket" or "check my issues".
---

# Jira Skill

Helps Claude read, create, and edit Jira issues via the Jira REST API.

---

## Step 1 — Load Credentials

Before any API call, retrieve stored credentials from the skill config file. The system checks in this order:

1. Project-specific: `.agents/jira-config.json` (recommended for team projects)
2. User global: `~/.agents/jira-config.json` (for personal use across projects)
3. Legacy: `~/.claude-skills/jira-config.json` (backward compatibility)

If no config file exists, run the **Setup Flow** below before proceeding.

### Reading the config

```bash
# Check for config in order of preference
if [[ -f ".agents/jira-config.json" ]]; then
    CONFIG_FILE=".agents/jira-config.json"
elif [[ -f "$HOME/.agents/jira-config.json" ]]; then
    CONFIG_FILE="$HOME/.agents/jira-config.json"
elif [[ -f "$HOME/.claude-skills/jira-config.json" ]]; then
    CONFIG_FILE="$HOME/.claude-skills/jira-config.json"
fi

cat "$CONFIG_FILE"
```

Expected fields:

| Field | Description |
|---|---|
| `base_url` | Your Jira instance URL, e.g. `https://yourorg.atlassian.net` |
| `email` | Atlassian account email |
| `api_token` | Jira API token (see setup) |
| `default_project` | Optional default project key, e.g. `ENG` |

Build the auth header as Basic `base64(email:api_token)`:

```bash
AUTH=$(echo -n "EMAIL:API_TOKEN" | base64)
# Use in all requests:
# -H "Authorization: Basic $AUTH"
# -H "Content-Type: application/json"
```

---

## Step 2 — Setup Flow (first-time / missing config)

Tell the user:

> "I need your Jira credentials to get started. Here's what you'll need:
> 1. **Jira base URL** — e.g. `https://yourorg.atlassian.net`
> 2. **Email** — the email you log into Jira with
> 3. **API Token** — generate one at https://id.atlassian.com/manage-profile/security/api-tokens

You can choose where to save the configuration:
- **Project-specific** (`.agents/jira-config.json`) - recommended for team projects
- **User global** (`~/.agents/jira-config.json`) - for personal use across projects

Run the setup script for interactive configuration:
```bash
./.agents/scripts/jira/jira-setup.sh
```

Or manually create the config file:

```bash
mkdir -p .agents
cat > .agents/jira-config.json <<EOF
{
  "base_url": "PLACEHOLDER_URL",
  "email": "PLACEHOLDER_EMAIL",
  "api_token": "PLACEHOLDER_TOKEN",
  "default_project": ""
}
EOF
chmod 600 .agents/jira-config.json
```

Verify connectivity:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Basic $(echo -n 'EMAIL:TOKEN' | base64)" \
  "BASE_URL/rest/api/3/myself"
```

A `200` response confirms success. Tell the user and proceed with their original request.

> **Security note**: The config file is `chmod 600` (owner read/write only). Never print the API token back to the user. If they want to rotate or update credentials, re-run the setup flow.

For more detail, see [`references/setup.md`](references/setup.md).

---

## Step 3 — Operations

Choose the right operation based on the user's request. See the reference files for full field lists and examples.

### Read / Search Issues → [`references/read-issues.md`](references/read-issues.md)

Use when the user wants to:
- View a specific issue by key (`PROJ-123`)
- Search issues with JQL or natural language
- List issues in a sprint, backlog, or for an assignee
- Get issue details (status, description, comments, attachments)

Quick example — fetch a single issue:

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  "BASE_URL/rest/api/3/issue/ISSUE_KEY"
```

---

### Create Issues → [`references/create-issues.md`](references/create-issues.md)

Use when the user wants to:
- Create a new bug, story, task, epic, or subtask
- Bulk-create multiple issues
- Create an issue and immediately assign / set priority

Quick example — create a task:

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": { "key": "PROJ" },
      "summary": "Issue title here",
      "description": { "type": "doc", "version": 1, "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Description here" }] }] },
      "issuetype": { "name": "Task" }
    }
  }' \
  "BASE_URL/rest/api/3/issue"
```

---

### Edit / Update Issues → [`references/edit-issues.md`](references/edit-issues.md)

Use when the user wants to:
- Change summary, description, assignee, priority, labels, story points
- Transition status (e.g. "In Progress" → "Done")
- Add or update a comment
- Link two issues

Quick example — update summary:

```bash
curl -s -X PUT \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{ "fields": { "summary": "New title" } }' \
  "BASE_URL/rest/api/3/issue/ISSUE_KEY"
```

---

## Error Handling

| HTTP Code | Meaning | Action |
|---|---|---|
| `200 / 201` | Success | Parse and display result |
| `400` | Bad request / invalid fields | Show error body to user, ask them to correct input |
| `401` | Auth failure | Re-run setup flow; token may be expired |
| `403` | No permission | Inform user; they may need to check Jira project permissions |
| `404` | Issue / project not found | Confirm the key is correct |
| `429` | Rate limited | Wait and retry |

Always show the user a clean summary of what happened, not raw JSON unless they ask.

---

## Output Format

- After **reading** an issue: show key, summary, status, assignee, priority, and description in a readable format.
- After **creating** an issue: show the new issue key and a link: `BASE_URL/browse/PROJ-123`.
- After **editing** an issue: confirm what changed and show the updated issue key link.
- For **searches**: show a table with key, summary, status, assignee.
