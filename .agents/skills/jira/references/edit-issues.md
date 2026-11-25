# Editing & Updating Jira Issues

## Update Fields (PUT)

Use a `PUT` to replace field values:

```bash
curl -s -X PUT \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "summary": "Updated title here"
    }
  }' \
  "$BASE_URL/rest/api/3/issue/PROJ-123"
```

A successful update returns `HTTP 204 No Content` (no response body).

---

## Common Field Updates

### Change summary

```json
{ "fields": { "summary": "New title" } }
```

### Change assignee

```json
{ "fields": { "assignee": { "accountId": "USER_ACCOUNT_ID" } } }
```

Unassign: `{ "fields": { "assignee": null } }`

### Change priority

```json
{ "fields": { "priority": { "name": "High" } } }
```

### Change due date

```json
{ "fields": { "duedate": "2025-12-31" } }
```

### Update labels (replaces all labels)

```json
{ "fields": { "labels": ["backend", "auth", "urgent"] } }
```

### Update description (ADF)

```json
{
  "fields": {
    "description": {
      "type": "doc",
      "version": 1,
      "content": [{
        "type": "paragraph",
        "content": [{ "type": "text", "text": "Updated description here." }]
      }]
    }
  }
}
```

---

## Transition Issue Status

Status changes require a transition, not a direct field update.

### Step 1: Get available transitions

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issue/PROJ-123/transitions"
```

Example response:

```json
{
  "transitions": [
    { "id": "21", "name": "In Progress" },
    { "id": "31", "name": "In Review" },
    { "id": "41", "name": "Done" }
  ]
}
```

### Step 2: Apply the transition

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{ "transition": { "id": "41" } }' \
  "$BASE_URL/rest/api/3/issue/PROJ-123/transitions"
```

If the user says something like "mark PROJ-123 as Done", always fetch transitions first to get the correct `id`.

---

## Add a Comment

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "type": "doc",
      "version": 1,
      "content": [{
        "type": "paragraph",
        "content": [{ "type": "text", "text": "Your comment text here." }]
      }]
    }
  }' \
  "$BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

### Update an existing comment

```bash
curl -s -X PUT \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{ "body": { "type": "doc", "version": 1, "content": [{ "type": "paragraph", "content": [{ "type": "text", "text": "Updated comment." }] }] } }' \
  "$BASE_URL/rest/api/3/issue/PROJ-123/comment/COMMENT_ID"
```

---

## Link Two Issues

First, get available link types:

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issueLinkType"
```

Common types: `Blocks`, `Clones`, `Duplicate`, `Relates`

Then create the link:

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "type": { "name": "Blocks" },
    "inwardIssue": { "key": "PROJ-100" },
    "outwardIssue": { "key": "PROJ-101" }
  }' \
  "$BASE_URL/rest/api/3/issueLink"
```

---

## Delete an Issue

```bash
curl -s -X DELETE \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issue/PROJ-123"
```

Always confirm with the user before deleting. Returns `HTTP 204` on success.

---

## Move Issue to a Sprint

First, get the sprint ID (see read-issues.md). Then:

```bash
curl -s -X POST \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{ "issues": ["PROJ-123", "PROJ-124"] }' \
  "$BASE_URL/rest/agile/1.0/sprint/SPRINT_ID/issue"
```

---

## Assign to Current Sprint (Move from Backlog)

Same endpoint as above — use the active sprint's ID.

---

## Using `update` Instead of `fields` (for append operations)

Some fields support `update` for incremental changes (e.g. adding a label without replacing all):

```json
{
  "update": {
    "labels": [
      { "add": "new-label" }
    ]
  }
}
```

Other `update` operations: `set`, `add`, `remove`, `copy`, `edit`, `replace`.

---

## Confirming Changes to the User

After a successful update:
- State what changed: "Updated PROJ-123: status → Done, assignee → Alice Smith"
- Include a browse link: `BASE_URL/browse/PROJ-123`
- If `HTTP 204`, the update succeeded even with no response body
