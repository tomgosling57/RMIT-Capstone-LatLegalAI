# PR Description Template

Use exactly this structure. No extra sections.

---

## What
<!-- One sentence: what does this PR do? -->

## Why
<!-- One sentence: why is this change needed? -->
Closes <ISSUE-KEY>

## Changes
<!-- One bullet per file: path — what changed -->
- `src/auth/oauth.ts` — Added OAuth2 token exchange logic
- `src/routes/login.ts` — Wired OAuth handler to /login route
- `src/auth/oauth.test.ts` — Unit tests for token exchange

---

## Anti-patterns to avoid

❌ "This PR implements the feature requested in the ticket above."  
❌ "See Jira for full context."  
❌ Long "How to test" sections — keep test notes in the ticket  
❌ Screenshot placeholders when there are no UI changes  
❌ Repeated boilerplate that says nothing  

## Good title format

`[PROJ-123] Short imperative sentence describing the change`

Examples:
- `[PROJ-123] Add OAuth2 login flow`
- `[PROJ-456] Fix null pointer on session expiry`
- `[PROJ-789] Upgrade React to v18`
