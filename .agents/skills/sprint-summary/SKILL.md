---
name: sprint-summary
description: >
  Use this skill whenever the user wants to create a sprint summary document
  from a pull request diff and Jira issues. Trigger on phrases like "create
  sprint summary", "generate sprint report", "write sprint notes", "summarise
  sprint", "sprint retrospective document", or "make a sprint review". This
  skill fetches Jira issue details, analyses a PR diff, and produces a
  structured markdown summary in the format of docs/sprints/sprint-five-summary.md.
  Always use this skill when the user asks for a sprint summary, sprint report,
  or sprint review document — even if they only mention a PR number or branch name.
---

# Sprint Summary Skill

Generates a structured sprint summary markdown document from a pull request diff and a list of Jira issue keys. The output follows the format established in [`docs/sprints/sprint-five-summary.md`](../../../docs/sprints/sprint-five-summary.md).

---

## Prerequisites

- **Jira credentials** must be configured in `.agents/jira-config.json` (see the [Jira skill](../jira/SKILL.md) for setup).
- **Git** must be available to fetch the PR diff.
- **GitHub CLI (`gh`)** is recommended for fetching PR diffs from GitHub, but a direct URL or pasted diff also works.

---

## Step 1 — Gather Inputs

Ask the user for:

1. **Pull Request identifier** — one of:
   - A GitHub PR URL (e.g. `https://github.com/your-org/latmatrix/pull/63`)
   - A PR number + repository (e.g. `#63` in `your-org/latmatrix`)
   - A branch name (e.g. `develop`)
   - A raw diff (paste the diff output directly)

2. **Jira issue keys** — a list of issue keys completed in the sprint (e.g. `AALA-71, AALA-74, AALA-75`). If the user doesn't have the full list, ask if they want to:
   - Fetch issues from a specific Jira sprint
   - Search by fix version or label
   - Provide them manually

3. **Sprint metadata**:
   - Sprint number / name (e.g. "Sprint 5")
   - Source and target branches (default: `develop` → `main`)
   - Date of the merge/release

---

## Step 2 — Fetch the PR Diff

### Option A: GitHub PR URL (recommended)

```bash
# Fetch the diff for a GitHub PR
gh pr diff <PR_NUMBER> --repo <ORG/REPO>
```

If `gh` is not authenticated, fall back to:

```bash
curl -sL "https://github.com/<ORG>/<REPO>/pull/<PR_NUMBER>.diff"
```

### Option B: Branch comparison

```bash
git fetch origin
git diff origin/main...origin/<BRANCH> --stat
git diff origin/main...origin/<BRANCH>
```

### Option C: Raw diff provided by the user

Use the diff text directly.

### Parse the diff output to extract:

| Metric | How to extract |
|--------|---------------|
| Total additions | Sum of `+` lines from `git diff --stat` or PR summary |
| Total deletions | Sum of `-` lines from `git diff --stat` or PR summary |
| Files changed | Count of files from `git diff --stat` or PR summary |
| New files | Files with `diff --git a/... b/...` where `a/dev/null` or `new file mode` |
| Deleted files | Files with `deleted file mode` |
| Modified files | All other changed files |
| Lines per file | Parse the `+N,-M` stat for each file |

### Categorise files

Group changed files into categories based on their path:

| Path pattern | Category |
|---|---|
| `backend/src/` | Backend |
| `backend/src/routes/` | Routes |
| `backend/src/tests/` | Testing |
| `backend/src/services/` | Services |
| `backend/src/controllers/` | Controllers |
| `chat/src/` | Chat UI |
| `website/` | Website |
| `scripts/` | Scripts / Automation |
| `scripts/jira/` | Jira Automation |
| `scripts/API_Tests/` | API Testing |
| `docs/` | Documentation |
| `tests/` | E2E / Load Tests |
| `legacy_frontend/` | Legacy Frontend |
| `.flake8`, `.gitignore`, `pyproject.toml`, etc. | Configuration |

---

## Step 3 — Fetch Jira Issue Details

Use the Jira skill infrastructure to fetch details for each issue key.

### Build the auth header

```bash
CONFIG_FILE=".agents/jira-config.json"
BASE_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['base_url'])")
EMAIL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['email'])")
TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['api_token'])")
AUTH=$(echo -n "$EMAIL:$TOKEN" | base64)
```

### Fetch a single issue

```bash
curl -s \
  -H "Authorization: Basic $AUTH" \
  -H "Accept: application/json" \
  "$BASE_URL/rest/api/3/issue/ISSUE_KEY?fields=summary,status,assignee,priority,issuetype"
```

### Parse the response

Extract these fields for each issue:

| Field | JSON path | Notes |
|-------|-----------|-------|
| Key | `key` | e.g. `AALA-71` |
| Summary | `fields.summary` | Issue title |
| Type | `fields.issuetype.name` | Bug, Task, Story, etc. |
| Status | `fields.status.name` | Done, In Review, To Do, etc. |
| Assignee | `fields.assignee.displayName` | Falls back to "Unassigned" if null |

### Handle errors

| HTTP Code | Action |
|-----------|--------|
| 200 | Parse and add to issue list |
| 401 | Re-run Jira setup; token may be expired |
| 404 | Log as "Unknown — issue not found" and continue |
| 429 | Wait 5 seconds and retry |

---

## Step 4 — Analyse the Diff for Detailed Sections

For each major category of changes, extract enough detail to write narrative sections. Look for:

### Backend changes
- New modules created (config, exceptions, logging, middleware, routes)
- Route restructuring (files moved, consolidated, removed)
- New endpoints added (method, path, purpose)
- Error handling improvements (exception hierarchy, handlers)
- Logging improvements (formatters, handlers, middleware)
- Controller/service changes

### Test infrastructure
- New test files and their purpose
- Test infrastructure (fixtures, config, runners)
- Coverage areas

### Scripts / Automation
- New scripts and their purpose
- Output formats supported

### Frontend / UI changes
- New components or pages
- Removed or consolidated pages
- Bug fixes

### Configuration & housekeeping
- Linting config changes
- Gitignore updates
- Dependency updates
- Documentation updates

### Bug fixes
- Symptoms described
- Root cause identified
- Fix applied

### Key Changes This Sprint (bullet list)
After writing the detailed narrative sections, synthesise a concise bullet-list summary of the most important changes. This section appears between "Files Changed Summary" and "Architecture Diagram". Each bullet should capture one major theme with supporting sub-bullets. For example:

```
* Middleware for generalized response and request handling and logging in the AI service
  * Standardized request parameters and response codes for varying request types
  * Implemented modular rotating logging system for monitoring and debugging
* Improved error handling in the AI service
  * Implemented domain specific exception types for the application and client context
  * Identified potential unguarded code blocks and implemented try catch measures
* UI/UX improvements for the chat interface: text prompting and clickable home navigation
* Revised routing structure for the AI service
  * Standardized the route naming format
  * Removed redundant routes and created clear explanations of each route's purpose
```

---

## Step 5 — Generate the Summary Document

Write the output to `docs/sprints/sprint-<N>-summary.md` following this template:

```markdown
# Sprint <N> Summary — <Source> to <Target>

**Pull Request:** [#<PR_NUMBER> — <TITLE>](<PR_URL>)
**Branch:** `<SOURCE>` → `<TARGET>`
**Date:** <YYYY-MM-DD>
**Total Changes:** +<ADDITIONS> additions / −<DELETIONS> deletions across <FILES> files

---

## Overview

<Sprint overview paragraph — 2-3 sentences summarising the major themes of the sprint>

## Summary of Issues Completed

| Key | Summary | Type | Status | Assignee |
|-----|---------|------|--------|----------|
| <KEY> | <Summary> | <Type> | <Status> | <Assignee> |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total additions | <N> |
| Total deletions | <N> |
| Files changed | <N> |
| New files created | <N> |
| Files deleted | <N> |
| Issues completed | <N> |
| <Other sprint-specific metrics> | <N> |

---

## Files Changed Summary

### New Files (<N>)

| File | Lines | Category |
|------|-------|----------|
| `<path>` | <N> | <Category> |

### Deleted Files (<N>)

| File | Lines | Reason |
|------|-------|--------|
| `<path>` | <N> | <Reason> |

### Modified Files (<N>)

| File | Lines | Change |
|------|-------|--------|
| `<path>` | +N / −N | <Description> |

---

## Key Changes This Sprint
* <Bullet point summary of the most important changes this sprint>
  * <Supporting detail for the change above>
* <Next major change>
  * <Supporting detail>
* <Next major change>

---

## Architecture Diagram

\`\`\`
<ASCII architecture diagram showing the system structure>
\`\`\`

[<KEY>]: <JIRA_URL>

---

## 1. <Major Theme 1>

### 1.1 <Sub-topic> ([<KEY>])

**Issue:** <Issue Summary> — *<Status>*

<Narrative description of what changed, why, and how it works>

#### What Changed

<Detailed description>

#### New Endpoint Structure / Key Components

| <Header> | <Header> | <Header> |
|----------|----------|----------|
| <Value> | <Value> | <Value> |

#### Files Removed / Modified

| File | Change | Purpose |
|------|--------|---------|
| `<path>` | <Change> | <Purpose> |

---

## <N>. <Major Theme N>

...

---

## <N+1>. Bug Fixes

### <N+1>.1 <Bug Title> ([<KEY>])

**Issue:** <Issue Summary> — *<Status>*

**Symptoms:** <Description>

**Root Cause:** <Description>

**Fix:** <Description>

---

## <N+2>. Configuration & Housekeeping

### <N+2>.1 <Topic>

<Description of changes>
```

### Formatting rules

1. **Issue links** — Each issue key in the table must be a clickable markdown link. Add reference-style links at the bottom of the document:
   ```markdown
   [AALA-71]: https://yourorg.atlassian.net/browse/AALA-71
   ```
2. **File links** — All file references must be clickable relative paths: [`backend/src/routes/api.py`](backend/src/routes/api.py)
3. **Code blocks** — Use triple backticks with language specifiers for code examples
4. **Tables** — Use GitHub-flavoured markdown tables with alignment
5. **Architecture diagram** — Use a simple ASCII diagram in a fenced code block
6. **Key Changes This Sprint** — A bullet-list summary of the most important changes, placed between "Files Changed Summary" and "Architecture Diagram". Use top-level bullets for each major theme and indented sub-bullets for supporting details.

---

## Step 6 — Present the Result

1. Confirm the file was written to `docs/sprints/sprint-<N>-summary.md`
2. Show the user a brief summary of what was generated:
   - Sprint number and date
   - Number of issues covered
   - Total changes (additions/deletions/files)
   - Major themes identified
3. Ask if they'd like any adjustments (e.g. reorder sections, add/remove issues, tweak wording)

---

## Reference Files

- [`docs/sprints/sprint-five-summary.md`](../../../docs/sprints/sprint-five-summary.md) — Example sprint summary to match format
- [`../jira/SKILL.md`](../jira/SKILL.md) — Jira skill for fetching issue details
- [`../jira/references/read-issues.md`](../jira/references/read-issues.md) — Jira API reference for reading issues
- [`../../../.agents/jira-config.json`](../../../.agents/jira-config.json) — Jira credentials config
