---
name: when-to-create-skills
description: Guidance on deciding when to create a new skill, when to extend an existing one, and when not to create a skill at all. Trigger this when a user asks whether something should be a skill, wants to understand the skill system, is wondering if their workflow is a good candidate for a skill, or before beginning any skill-writing process to ensure it's actually warranted.
---

# When to Create a New Skill

Skills live in `.agents/skills/`. Creating them takes effort — don't create one unless it genuinely earns its place.

---

## Create a Skill When...

### ✅ The workflow is complex and multi-step
If completing the task requires a non-obvious sequence of tools, decisions, or file operations that Claude would otherwise need to figure out from scratch each time, a skill is warranted.

> Example: "Build a PDF report from a template" requires picking the right library, templating approach, font handling, and output format — worth capturing.

### ✅ It will be reused across sessions or by multiple users
If the same workflow will be needed again (or by teammates), a skill makes it consistent and fast.

### ✅ The output must meet a specific standard
If there are specific quality bars, formatting rules, or conventions that aren't obvious from a plain prompt (e.g., a company style guide, a file schema, an API contract), a skill captures and enforces them.

### ✅ Institutional knowledge needs to be preserved
Workflows that encode hard-won lessons — workarounds, best practices, edge-case handling — are prime skill candidates. Without a skill, that knowledge is lost between sessions.

### ✅ The task is error-prone without structured guidance
If Claude frequently gets the task wrong without detailed step-by-step instructions, a skill is better than re-explaining every time.

---

## Don't Create a Skill When...

### ❌ The task is simple and one-shot
If Claude can do it well from a plain prompt — "translate this to French", "write me a haiku", "explain this error" — a skill adds friction without value.

### ❌ It's highly specific to a single context
One-off tasks tied to a unique file, project, or moment don't generalise. Solve them inline; don't codify them.

### ❌ The domain changes rapidly
If the tools, APIs, or conventions involved change frequently, the skill will become stale faster than it's worth maintaining.

### ❌ You'd be duplicating an existing skill
Always check `.agents/skills/` first. Extend or update existing skills rather than creating parallel ones.

### ❌ The "skill" is just a system prompt
If what you want is just to prime Claude's persona or tone, that belongs in the system prompt — not a skill.

---

## Extend vs. Create New

Prefer **extending** an existing skill when:
- The new use case is a variant or sub-case of an existing skill (e.g., a new output format for a document skill)
- The core workflow is the same but with different parameters
- Adding a reference file or a new section would cover it

Create a **new skill** when:
- The trigger condition is fundamentally different
- The workflow diverges significantly from the beginning
- Mixing it into an existing skill would make the SKILL.md unwieldy (>500 lines)

---

## Quick Decision Checklist

Before writing a new skill, confirm:

- [ ] Is this genuinely multi-step or complex?
- [ ] Will it be reused (by me, my team, or across sessions)?
- [ ] Does it encode knowledge Claude wouldn't have from a plain prompt?
- [ ] Have I checked that no existing skill in `.agents/skills/` already covers this?
- [ ] Is the domain stable enough that the skill won't be outdated in a week?

If you answered **no** to most of these, solve it inline rather than creating a skill.

---

## The "One Sentence Test"

Try to describe the skill in one sentence starting with a verb:

> "Convert uploaded Excel files into formatted PDF reports."
> "Scaffold a new FastAPI service with auth and tests."
> "Summarise customer support tickets into a weekly digest."

If you can't write that sentence clearly, the skill isn't well-defined yet. Go back and clarify before writing SKILL.md.

---

## Naming Conventions

- Use `kebab-case` for skill directory names and the `name` frontmatter field
- Names should be noun phrases describing the output or the action: `pdf-report`, `api-scaffold`, `ticket-digest`
- Avoid vague names: `helper`, `tool`, `misc`, `utils`

---

## Skill Storage

All skills are stored in `.agents/skills/<skill-name>/`. The required file is `SKILL.md`. Optional subdirectories:
- `scripts/` — executable helpers
- `references/` — documentation loaded into context on demand
- `assets/` — templates, fonts, sample files

See the `skill-creator-meta` skill for full authoring guidance.
