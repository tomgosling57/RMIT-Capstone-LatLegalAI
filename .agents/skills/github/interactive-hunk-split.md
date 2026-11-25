# Skill: interactive-hunk-split

**Category**: Rescue — Code Already Written  
**Best for**: You have one large branch and need to split it retroactively  
**Key tool**: `git add -p` and `git checkout -p`

## When to use

- You already wrote 1,000+ lines in a single branch
- You want to avoid manual copy-paste (which causes merge conflicts)
- You need to surgically move specific hunks to different branches

## Core concepts

- `git add -p` — interactively stage individual hunks from working tree
- `git checkout -p <branch>` — interactively cherry-pick hunks from another branch
- Hunk answers: `y` = yes/stage, `n` = no/skip, `s` = split hunk further, `e` = edit hunk manually, `q` = quit

## Commands

```bash
# --- Setup: stash everything from your large branch ---
git stash
# Your working tree is now clean

# --- Branch 1: Refactor / cleanup ---
git checkout -b refactor/cleanup main
git stash pop                    # restore your changes to working tree

git add -p                       # go hunk by hunk:
                                 #   y = this hunk is a refactor, stage it
                                 #   n = this is new feature code, skip
                                 #   s = split this hunk into smaller pieces

git commit -m "refactor: cleanup and renames"
git push -u origin refactor/cleanup
gh pr create --base main --title "refactor: cleanup"

# --- Branch 2: New feature (cherry-pick hunks from your original branch) ---
git stash                        # stash remaining unstaged changes
git checkout -b feat/new-feature main

# Pull specific hunks from the refactor branch interactively
git checkout -p refactor/cleanup
#   y = I want this hunk in the feature branch too
#   n = skip

# Or restore from stash and stage selectively
git stash pop
git add -p                       # stage only feature hunks

git commit -m "feat: implement new feature"
git push -u origin feat/new-feature
gh pr create --base main --title "feat: new feature"
```

## Editing a hunk manually

When a single hunk mixes refactor + feature code, answer `e` to edit it:

```bash
# In the hunk editor that opens:
# - Delete lines you DON'T want staged (lines starting with +)
# - Leave lines you DO want staged
# - Save and close
```

## Tips

- Work in order of least-dependent to most-dependent (refactors first)
- Use `git diff --cached` after each `add -p` session to verify what's staged
- Use `git diff` (unstaged) to see what's left to assign
- If you make a mistake: `git reset HEAD` to unstage everything and start the session over
- `git stash list` shows all stashes if you need to recover
