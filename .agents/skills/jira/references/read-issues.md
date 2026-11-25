# Reading & Searching Jira Issues

## Get a Single Issue

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  -H "Accept: application/json" \
  "$BASE_URL/rest/api/3/issue/PROJ-123"
```

### Limit fields returned (faster)

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issue/PROJ-123?fields=summary,status,assignee,priority,description,comment"
```

### Key fields in the response

| JSON path | Description |
|---|---|
| `key` | Issue key e.g. `PROJ-123` |
| `fields.summary` | Issue title |
| `fields.status.name` | Current status |
| `fields.assignee.displayName` | Assigned user |
| `fields.priority.name` | Priority level |
| `fields.description` | Atlassian Document Format (ADF) body |
| `fields.comment.comments[]` | Array of comments |
| `fields.issuetype.name` | Bug, Story, Task, Epic, Subtask |
| `fields.labels[]` | Labels |
| `fields.story_points` (custom) | May vary by instance |

---

## Search with JQL

JQL (Jira Query Language) is the most powerful way to filter issues.

```bash
JQL="project = ENG AND status = 'In Progress' ORDER BY updated DESC"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$JQL")

curl -s \
  -H "Authorization: Basic $AUTH" \
  -H "Accept: application/json" \
  "$BASE_URL/rest/api/2/search?jql=$ENCODED&maxResults=50&fields=summary,status,assignee,priority"
```

### Common JQL patterns

| Goal | JQL |
|---|---|
| My open issues | `assignee = currentUser() AND statusCategory != Done` |
| Issues in current sprint | `sprint in openSprints() AND project = PROJ` |
| Recent bugs | `issuetype = Bug AND created >= -7d ORDER BY created DESC` |
| Issues by label | `labels = "backend" AND project = PROJ` |
| Unassigned issues | `assignee is EMPTY AND status = "To Do"` |
| Epics only | `issuetype = Epic AND project = PROJ` |
| Issues mentioning text | `text ~ "login timeout"` |
| Overdue issues | `due < now() AND statusCategory != Done` |

### Pagination

```bash
# Page 2 (0-indexed)
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/2/search?jql=$ENCODED&startAt=50&maxResults=50"
```

Response includes `total`, `startAt`, `maxResults` for pagination.

---

## Get Issues in a Board / Sprint

### List all boards

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/agile/1.0/board"
```

### Get sprints for a board

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/agile/1.0/board/BOARD_ID/sprint?state=active"
```

State options: `active`, `future`, `closed`

### Get issues in a sprint

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/agile/1.0/sprint/SPRINT_ID/issue?fields=summary,status,assignee"
```

### Get backlog

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/agile/1.0/board/BOARD_ID/backlog?fields=summary,status,priority"
```

---

## Get Issue Comments

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issue/PROJ-123/comment"
```

---

## Get Available Transitions (Status Options)

Needed before transitioning an issue's status:

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  "$BASE_URL/rest/api/3/issue/PROJ-123/transitions"
```

Returns array of `{ id, name }` — use the `id` when transitioning.

---

## Displaying Results to the User

Parse the JSON response and present it cleanly. Example format for a search result table:

```
| Key      | Summary                       | Status      | Assignee     |
|----------|-------------------------------|-------------|--------------|
| PROJ-12  | Fix login timeout             | In Progress | Alice Smith  |
| PROJ-8   | Update API docs               | To Do       | Unassigned   |
```

For a single issue, show a structured summary:

```
PROJ-123 — Fix login timeout
Status:    In Progress
Assignee:  Alice Smith
Priority:  High
Type:      Bug

Description:
  Users on mobile are getting session timeouts after 5 minutes...

Comments (2):
  [Bob Jones, 2 days ago] Reproduced on iOS 17.
  [Alice Smith, 1 day ago] Fix in PR #456.
```
