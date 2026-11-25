# Skill: stacked-pr-chain

**Category**: Strategy — New Work  
**Best for**: Layered features (infrastructure → logic → UI)  
**Key rule**: Each PR targets the *previous branch*, not `main` — so reviewers only see the relevant diff.

## When to use

- You are starting a feature that has clear layers (models → services → UI)
- You want reviewers to approve each layer independently
- The feature is too large to ship in one PR

## Concept

```
main
 └── feat/layer-1-models        ← PR 1 targets main
      └── feat/layer-2-services ← PR 2 targets layer-1
           └── feat/layer-3-ui  ← PR 3 targets layer-2
```

When layer-1 merges into main, GitHub automatically retargets PR 2 to main.

## Commands

```bash
# --- Layer 1: Base infrastructure / data models ---
git checkout -b feat/layer-1-models main
# ... do work ...
git add .
git commit -m "feat: add data models and API contracts"
git push -u origin feat/layer-1-models
gh pr create \
  --base main \
  --title "feat: layer 1 — data models" \
  --body "Base layer. Subsequent PRs build on this branch."

# --- Layer 2: Services / business logic ---
git checkout -b feat/layer-2-services feat/layer-1-models
# ... do work ...
git add .
git commit -m "feat: add service layer"
git push -u origin feat/layer-2-services
gh pr create \
  --base feat/layer-1-models \
  --title "feat: layer 2 — services" \
  --body "Stacked on feat/layer-1-models. Review only the service diff."

# --- Layer 3: UI / final integration ---
git checkout -b feat/layer-3-ui feat/layer-2-services
# ... do work ...
git add .
git commit -m "feat: add UI components and integration"
git push -u origin feat/layer-3-ui
gh pr create \
  --base feat/layer-2-services \
  --title "feat: layer 3 — UI integration" \
  --body "Stacked on feat/layer-2-services."
```

## Keeping stacked branches in sync

```bash
# If layer-1 gets new commits, rebase layer-2 onto it:
git checkout feat/layer-2-services
git rebase feat/layer-1-models
git push --force-with-lease origin feat/layer-2-services
```

## Tips

- Add a "Stack" section to each PR body listing all PRs in the chain
- Merge in order: layer-1 first, then layer-2, then layer-3
- Use `gh pr list --author @me` to track the chain status
