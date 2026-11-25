---
name: pr-creator
description: >
  Creates well-scoped, cleanly separated pull requests from a list of codebase changes,
  reading issue numbers and titles from Jira. Use this skill whenever an agent needs to:
  split a batch of changes into logical PRs, generate branch names in feature/ID/name format,
  create PR titles and descriptions tied to Jira issues, or organize commits into reviewable units.
  Trigger on phrases like "create PRs from changes", "split into pull requests", "open PRs for these
  changes", "make branches for these issues", or any task where multiple code changes need to become
  separate GitHub/GitLab pull requests linked to Jira tickets.
---

# PR Creator Skill

Turn a list of code changes into clean, well-scoped pull requests — each linked to a Jira issue,
with a properly formatted branch name and minimal, focused diff.

---

## Workflow

### 1. Read Jira Issues

For each issue number provided, fetch the Jira ticket to get:
- Issue key (e.g. `PROJ-123`)
- Summary / title
- Type (feature, bug, chore, etc.)

Use the Jira MCP if available. If not, ask the user to supply the issue title manually.

### 2. Group Changes by Issue

Map each changed file or logical change to a single Jira issue. Rules:
- One PR per Jira issue (1:1 mapping)
- If a change touches shared infrastructure (config, deps, migrations), create a separate chore PR
- Never mix unrelated issues in one PR
- If a file is touched by multiple issues, assign it to the issue most responsible for the change

### 3. Name the Branch

Format: `feature/<ISSUE-ID>/<short-slug>`

- `<ISSUE-ID>` — Jira key in lowercase, e.g. `proj-123`
- `<short-slug>` — 2–5 words from the issue title, kebab-cased, no filler words
- Prefix rules: use `feature/` for new functionality, `fix/` for bugs, `chore/` for tooling/deps

Examples:
```
feature/proj-123/user-auth-flow
fix/proj-456/null-pointer-login
chore/proj-789/upgrade-react-18
```

### 4. Write the PR

Keep it short. A PR description has three parts only:

```markdown
## What
One sentence. What does this change do?

## Why
One sentence. Which Jira issue does it close and why is it needed?
Closes PROJ-123

## Changes
- path/to/file.ts — what changed and why (one line per file)
```

Do not include: implementation details, how-to-test sections, screenshots placeholders,
or boilerplate that adds noise without value.

### 5. Output Format

Return a list of PR objects. For each:

```
Branch:      feature/proj-123/user-auth-flow
Title:       [PROJ-123] Add OAuth2 login flow
Base branch: main
Files:       src/auth/oauth.ts, src/routes/login.ts
Description: (the 3-part template above)
```

---

## Splitting Heuristics

When changes are ambiguous, apply these in order:

1. **Single responsibility** — each PR should do one thing a reviewer can understand in < 5 min
2. **No cross-concern mixing** — UI changes and API changes go in separate PRs unless inseparable
3. **Test files follow their source** — `auth.test.ts` goes with `auth.ts`, same PR
4. **Migrations are solo** — DB schema migrations always get their own PR
5. **Shared utils** — if a utility is added to serve one issue, it goes in that issue's PR

---

## Minimal Code Principle

Keep each PR as small as possible:
- Remove any change not required to close the linked issue
- Flag any change that looks like unrelated cleanup — suggest a separate chore PR
- Split large refactors from feature additions even if they touch the same file

---

## Reference

See `references/branch-examples.md` for more naming examples by issue type.
See `references/pr-template.md` for the canonical PR description template.
