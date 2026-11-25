# Creating Jira Issues

## Basic Issue Creation

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": { "key": "PROJ" },
      "summary": "Issue title here",
      "issuetype": { "name": "Task" },
      "description": {
        "type": "doc",
        "version": 1,
        "content": [{
          "type": "paragraph",
          "content": [{ "type": "text", "text": "Describe the issue here." }]
        }]
      }
    }
  }' \
  "$BASE_URL/rest/api/3/issue"
```

### Response

```json
{
  "id": "10042",
  "key": "PROJ-123",
  "self": "https://yourorg.atlassian.net/rest/api/3/issue/10042"
}
```

Tell the user: `Created PROJ-123 → https://yourorg.atlassian.net/browse/PROJ-123`

---

## Issue Types

Common values for `issuetype.name`:

| Name | Use for |
|---|---|
| `Task` | General work item |
| `Bug` | Something broken |
| `Story` | User-facing feature |
| `Epic` | Large body of work |
| `Subtask` | Child of another issue (requires `parent`) |

To get valid issue types for a project:

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/project/PROJ"
```

---

## Full Fields Reference

```json
{
  "fields": {
    "project": { "key": "PROJ" },
    "summary": "Short title",
    "issuetype": { "name": "Bug" },
    "description": { ... },         // ADF format (see below)
    "assignee": { "accountId": "USER_ACCOUNT_ID" },
    "priority": { "name": "High" }, // Highest, High, Medium, Low, Lowest
    "labels": ["backend", "auth"],
    "duedate": "2025-12-31",        // YYYY-MM-DD
    "parent": { "key": "PROJ-100" } // For subtasks or child issues
  }
}
```

### Priority values

`Highest` | `High` | `Medium` | `Low` | `Lowest`

---

## Atlassian Document Format (ADF) for Descriptions

The Jira Cloud API v3 requires descriptions in ADF, not plain text.

### Plain paragraph

```json
{
  "type": "doc",
  "version": 1,
  "content": [{
    "type": "paragraph",
    "content": [{ "type": "text", "text": "Your text here." }]
  }]
}
```

### Bullet list

```json
{
  "type": "doc",
  "version": 1,
  "content": [{
    "type": "bulletList",
    "content": [
      {
        "type": "listItem",
        "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item one" }] }]
      },
      {
        "type": "listItem",
        "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Item two" }] }]
      }
    ]
  }]
}
```

### Heading + paragraph

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 2 },
      "content": [{ "type": "text", "text": "Steps to Reproduce" }]
    },
    {
      "type": "paragraph",
      "content": [{ "type": "text", "text": "1. Go to login page..." }]
    }
  ]
}
```

---

## Finding a User's accountId (for assignee)

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/user/search?query=alice@yourcompany.com"
```

Returns array of users with `accountId` field.

---

## Create a Subtask

A subtask requires the `parent` field and `issuetype` set to `Subtask`:

```json
{
  "fields": {
    "project": { "key": "PROJ" },
    "parent": { "key": "PROJ-100" },
    "summary": "Subtask title",
    "issuetype": { "name": "Subtask" }
  }
}
```

---

## Bulk Create Issues

To create multiple issues at once:

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "issueUpdates": [
      { "fields": { "project": { "key": "PROJ" }, "summary": "Issue 1", "issuetype": { "name": "Task" } } },
      { "fields": { "project": { "key": "PROJ" }, "summary": "Issue 2", "issuetype": { "name": "Bug" } } }
    ]
  }' \
  "$BASE_URL/rest/api/3/issue/bulk"
```

---

## Getting Available Projects

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/project"
```

Returns array of projects with `key` and `name`.
