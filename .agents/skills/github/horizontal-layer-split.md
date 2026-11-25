# Skill: horizontal-layer-split

**Category**: Strategy — Separation of Concerns  
**Best for**: Changes that span multiple layers of the stack  
**Key rule**: Split by responsibility, not by time. Each PR owns one layer.

## When to use

- Your branch touches the database, backend, AND frontend
- You have a mix of refactors and new features
- Migrations or config changes should land independently

## Recommended split order

1. **Migrations & config** — schema changes, env vars, feature flags (no logic dependencies)
2. **Refactors** — renames, cleanup, no behaviour change (easy to approve)
3. **Backend / services** — new logic, API endpoints
4. **Frontend / UI** — components, pages, data fetching

## Commands

```bash
# --- PR A: Migrations & config (targets main, no dependencies) ---
git checkout -b feat/db-migrations main
git add db/migrate/ .env.example config/
git commit -m "chore: schema migrations and new env vars"
git push -u origin feat/db-migrations
gh pr create \
  --base main \
  --title "chore: db migrations + config" \
  --label "migrations" \
  --body "No logic changes. Safe to merge independently."

# --- PR B: Refactor (targets main) ---
git checkout -b refactor/cleanup main
git add -p   # interactively stage only refactor hunks
git commit -m "refactor: rename variables and remove dead code"
git push -u origin refactor/cleanup
gh pr create \
  --base main \
  --title "refactor: code cleanup" \
  --label "refactor"

# --- PR C: Backend services (targets main or feat/db-migrations if dependent) ---
git checkout -b feat/backend-services main
git add src/services/ src/api/
git commit -m "feat: add service layer"
git push -u origin feat/backend-services
gh pr create \
  --base main \
  --title "feat: backend services" \
  --label "backend"

# --- PR D: Frontend (targets backend branch if it depends on new APIs) ---
git checkout -b feat/frontend-views feat/backend-services
git add src/components/ src/pages/
git commit -m "feat: add UI views"
git push -u origin feat/frontend-views
gh pr create \
  --base feat/backend-services \
  --title "feat: frontend views" \
  --label "frontend"
```

## Adding labels via GitHub CLI

```bash
# Create labels first if they don't exist
gh label create "migrations" --color "0075ca"
gh label create "refactor"   --color "e4e669"
gh label create "backend"    --color "d93f0b"
gh label create "frontend"   --color "0e8a16"
```

## Tips

- `git add <path>` is your friend — stage by directory, not by hunk
- Refactor PRs are fastest to review; ship them first to unblock others
- If the frontend truly depends on new backend APIs, stack it (`--base feat/backend-services`) rather than targeting main
