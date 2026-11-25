# .agents/skills — Agent Skills

A collection of agent skills for various workflows. Each skill lives in its own subdirectory with a `SKILL.md` entry point and optional reference files.

## Skills

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `jira` | Read, create, edit Jira issues via REST API | User mentions Jira, issues, tickets, sprints |
| `sprint-summary` | Generate sprint summary docs from PR diff + Jira issues | User asks for sprint report, summary, or review |
| `pr-size-audit` | Audit a branch before opening a PR | Always run first |
| `stacked-pr-chain` | Create layered branches that build on each other | New work, layered features |
| `horizontal-layer-split` | Split by stack responsibility (db → backend → frontend) | Multi-layer changes |
| `interactive-hunk-split` | Carve an existing large branch into smaller ones | Code already written |
| `dark-launch-feature-flag` | Merge partial features safely behind a flag | Incomplete features |

## PR Size Guidelines

- **Lines of code**: Aim for < 400 lines per PR
- **Review time**: Should take a peer 15–20 minutes max
- **Scope**: One PR = one logical change
- **Split signal**: If `git diff main --name-only` touches > 2 top-level directories, split horizontally

## Workflow

```
1. Run pr-size-audit to assess the branch
2. If > 400 lines or multi-layer → choose a split strategy
3. New work?      → stacked-pr-chain or horizontal-layer-split
4. Already coded? → interactive-hunk-split
5. Partial feature? → dark-launch-feature-flag
```

## Directory Structure

```
.agents/
└── skills/
    ├── README.md                      ← this file
    ├── jira/                          ← Jira API skill
    │   ├── SKILL.md
    │   └── references/
    ├── sprint-summary/                ← Sprint summary generation skill
    │   ├── SKILL.md
    │   └── references/
    ├── pr-size-audit.md
    ├── stacked-pr-chain.md
    ├── horizontal-layer-split.md
    ├── interactive-hunk-split.md
    └── dark-launch-feature-flag.md
```
