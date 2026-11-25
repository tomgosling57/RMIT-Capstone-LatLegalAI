---
name: skill-creator-meta
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. Trigger this skill whenever someone says "make a skill", "create a skill", "write a skill", "add a skill", or wants to turn a workflow or set of instructions into a reusable skill.
---

# Skill Creator (Meta Skill)

A skill for creating new skills and iteratively improving them.

Skills live in the `.agents/skills/` directory. All paths in this document referring to skills use `.agents/skills/` — not `.claude/skills/`.

## High-Level Process

1. Decide what the skill should do and roughly how
2. Write a draft of the skill in `.agents/skills/<skill-name>/SKILL.md`
3. Create test prompts and run claude-with-the-skill on them
4. Evaluate results qualitatively and quantitatively
5. Rewrite the skill based on feedback
6. Repeat until satisfied
7. Expand test set and run at larger scale

Your job: figure out where the user is in this process and help them move forward.

---

## Communicating with the User

Users range from non-technical to highly technical. Watch for cues:
- "Evaluation" and "benchmark" are OK by default
- For "JSON" and "assertion", look for technical cues before using without explanation

---

## Creating a Skill

### 1. Capture Intent

Before writing anything, understand:
1. What should this skill enable Claude to do?
2. When should it trigger? (which user phrases / contexts)
3. What is the expected output format?
4. Are test cases needed? (objectively verifiable outputs benefit from them; subjective outputs often don't)

If the conversation already contains a workflow the user wants to capture, extract the steps, tools used, and corrections from history — and confirm before proceeding.

### 2. Interview & Research

Ask about: edge cases, input/output formats, example files, success criteria, dependencies.

Research proactively (via MCP or subagents if available) before putting burden on the user.

### 3. Write the SKILL.md

Components to fill in:
- **name** – Skill identifier (kebab-case)
- **description** – When to trigger AND what the skill does. Make descriptions slightly "pushy" to combat Claude's tendency to undertrigger.
- **compatibility** – Required tools / dependencies (optional, rarely needed)
- **body** – Step-by-step instructions, reference pointers, and examples

#### File Layout

```
.agents/skills/<skill-name>/
├── SKILL.md               ← required
├── scripts/               ← executable helpers (optional)
├── references/            ← docs loaded into context as needed (optional)
└── assets/                ← templates, fonts, icons (optional)
```

#### Progressive Disclosure

Skills use three loading levels:
1. **Metadata** (name + description) — always in context (~100 words)
2. **SKILL.md body** — in context when skill triggers (<500 lines ideal)
3. **Bundled resources** — loaded/executed as needed (unlimited)

Keep SKILL.md under 500 lines. If approaching the limit, add hierarchy and clear pointers to sub-files.

#### Principle of Least Surprise

Skills should behave predictably. Prefer explicit instructions over clever inference. When in doubt, spell it out.

#### Writing Style

- Use second person ("you") for instructions
- Use present tense
- Prefer bullet lists for options; numbered lists for sequences
- Keep examples concrete and runnable

---

## Testing the Skill

### Designing Test Cases

Test prompts should be substantive — simple one-liners won't trigger skills reliably since Claude can handle them directly. Aim for multi-step or specialized queries.

Write test cases to `.agents/skills/<skill-name>/evals/evals.json`:
```json
[
  {
    "id": "tc-001",
    "prompt": "...",
    "assertions": [
      { "type": "contains", "value": "expected output fragment" }
    ]
  }
]
```

### Running Tests

In Claude.ai (no subagents): read the SKILL.md yourself, then attempt each test case one at a time. Skip baselines. Review outputs inline and ask the user for feedback.

In Claude Code / Cowork: spawn subagents for parallel execution, run baselines, grade with `agents/grader.md`.

---

## Iterating

After each test run:
1. Generate the eval viewer (if available): `python eval-viewer/generate_review.py`
2. Present results to the user — get qualitative feedback before revising
3. Update the SKILL.md
4. Re-run tests
5. Repeat

**Always generate the eval viewer BEFORE evaluating outputs yourself. Get human eyes on examples first.**

---

## Optimizing the Description (Claude Code / Cowork only)

Once the skill body is solid, optimize the triggering description:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path .agents/skills/<skill-name> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

Apply `best_description` from the JSON output to the SKILL.md frontmatter. Show the user before/after scores.

---

## Updating an Existing Skill

- **Preserve the original name.** Keep the directory name and `name` frontmatter unchanged.
- **Copy to a writeable location first** if the installed path is read-only (e.g., copy to `/tmp/skill-name/`, edit, then package).

---

## Packaging

```bash
python -m scripts.package_skill .agents/skills/<skill-name>
```

Present the resulting `.skill` file to the user via `present_files`.

---

## Reference Files

- `agents/grader.md` — Evaluate assertions against outputs
- `agents/comparator.md` — Blind A/B comparison
- `agents/analyzer.md` — Analyze why one version beat another
- `references/schemas.md` — JSON schemas for evals, grading, etc.

---

## Core Loop (summary)

1. Understand what the skill is about
2. Draft or edit the skill in `.agents/skills/<skill-name>/SKILL.md`
3. Run test prompts
4. Show results to user → gather feedback
5. Revise
6. Repeat until satisfied
7. Package and deliver
