# Skill: pr-size-audit

**Category**: Guard / Pre-flight  
**Run before**: Any `gh pr create` call  
**Goal**: Detect if a branch is too large to review and recommend a split strategy.

## When to use

Run this skill before opening any pull request. If the output exceeds the thresholds below, switch to one of the split strategy skills instead.

## Thresholds

| Signal | Threshold | Action |
|---|---|---|
| Total lines changed | > 400 | Split required |
| Top-level directories touched | > 2 | Use horizontal-layer-split |
| Commits | > 10 | Consider stacked-pr-chain |

## Commands

```bash
# 1. Summary stat — total insertions + deletions
git diff main --shortstat

# 2. Per-file breakdown
git diff main --stat

# 3. List all changed files
git diff main --name-only

# 4. Group by top-level directory (reveals layer spread)
git diff main --name-only | cut -d/ -f1 | sort | uniq -c | sort -rn

# 5. Count commits ahead of main
git log main.. --oneline | wc -l

# 6. Preview diff size per file (useful for spotting outliers)
git diff main --stat | sort -t'|' -k2 -rn | head -20
```

## Decision tree

```
shortstat > 400 lines?
├── yes → split needed
│   ├── touches db/ AND src/ AND components/?  → horizontal-layer-split
│   ├── code already written in one branch?    → interactive-hunk-split
│   └── new planned work?                      → stacked-pr-chain
└── no  → safe to open PR
```

## Example output to watch for

```
# Bad — multi-layer, too large:
   3 db/migrate/
  12 src/services/
   8 src/components/
   2 src/pages/

# Good — single concern:
   5 src/services/
```
