---
name: github-pr-code-review
description: >
  Generate comprehensive, actionable, and constructive GitHub pull request reviews.
  Use this skill when asked to review a PR, analyze a code diff, provide code feedback,
  or comment on a GitHub pull request. Produces structured, professional, mentor-quality
  reviews with labeled feedback, code suggestions, and a supportive collaborative tone.
  When a PR number is provided, can automatically fetch PR details using GitHub CLI
  and post the review directly to GitHub. Triggers: "review this PR", "review my code",
  "give feedback on this diff", "code review", "review these changes", or any request
  to analyze a pull request.
---

## Overview

This skill produces ready-to-post GitHub PR review comments. The review is structured,
mentor-quality, and tailored to foster both learning and codebase improvement. It balances
rigorous technical analysis with a supportive, collaborative tone.

When a PR number is provided, the skill can automatically fetch PR details using GitHub CLI,
generate a comprehensive review, and post it directly to the GitHub pull request.

---

## Inputs

The user must supply **at least one** of the following. Request clarification if none are provided:

| Input | Description | Required |
|---|---|---|
| PR number | GitHub PR number (e.g., "#26" or "26") | Optional (enables GitHub CLI automation) |
| PR title & description | The PR's stated objective | Strongly recommended |
| File diffs / changed files | The actual code changes | Required for full review |
| Language / framework | e.g. TypeScript + React, Python + FastAPI | Recommended |
| Project conventions | Style guides, linting rules, architecture patterns | Optional |
| Review focus | e.g. "focus on security" or "quick sanity check only" | Optional |

If critical inputs are missing, ask before generating the review:
> "To give you a thorough review, could you share the code diff / changed files?"

**Note:** If a PR number is provided and GitHub CLI is available, the skill will automatically fetch PR details and post the review. See "GitHub CLI Integration" below.

---

## GitHub CLI Integration

When the user provides a PR number (e.g., "#26" or "26"), use the GitHub CLI to automatically fetch PR details and post the review. Follow these steps:

1. **Fetch PR details:**
   ```bash
   gh pr view <PR_NUMBER> --json title,body,state,author,createdAt,updatedAt,headRefName,baseRefName,files
   ```
   This provides metadata about the PR.

2. **Fetch the diff:**
   ```bash
   gh pr diff <PR_NUMBER>
   ```
   This provides the actual code changes to review.

3. **Generate the review** using the standard output structure below.

4. **Write the review to a temporary file:**
   ```bash
   echo "<REVIEW_CONTENT>" > /tmp/pr-review-<PR_NUMBER>.md
   ```
   Or use a script to write the Markdown content.

5. **Post the review using GitHub CLI:**
   ```bash
   gh pr comment <PR_NUMBER> --body-file /tmp/pr-review-<PR_NUMBER>.md
   ```

6. **Clean up the temporary file:**
   ```bash
   rm /tmp/pr-review-<PR_NUMBER>.md
   ```

**Note:** Ensure GitHub CLI (`gh`) is installed and authenticated before attempting these commands. If not available, fall back to manual review generation.

---

## Output Structure

Produce the review as a single Markdown block, ready to paste into GitHub.
Follow this exact section order:

---

### 1. Context & Summary

Open with a 3–5 sentence summary that:
- Restates the PR's goal in your own words (confirms understanding)
- Describes what changed at a high level (files touched, approach taken)
- Notes any immediately apparent scope concerns or ambiguities

**Template:**
```
## 📋 Review Summary

This PR introduces [brief description of change]. The primary goal appears to be [objective].
Changes span [N files], primarily affecting [area/module]. Overall, the approach is
[sound/reasonable/worth discussing] — see detailed notes below.
```

---

### 2. Structured Analysis Sections

Use the following `##` headers in this order. Omit a section only if genuinely not applicable
(and briefly say why). Each point within a section must reference a specific file/line where possible.

#### 2a. High-Level Feedback
Assess:
- Architecture alignment (does this fit the existing patterns?)
- Design pattern usage (appropriate abstraction, separation of concerns)
- Scope creep or missing scope
- Impact on other modules or downstream consumers

#### 2b. Code Quality & Best Practices
Assess:
- Readability (naming, function length, cognitive complexity)
- Adherence to language idioms and project style guides
- SOLID / DRY / YAGNI principle violations
- Magic numbers, unclear constants, commented-out code
- Error handling completeness

#### 2c. Security & Performance
Assess:
- Input validation and sanitisation
- Authentication / authorisation gaps
- Injection vulnerabilities (SQL, XSS, command injection)
- Sensitive data exposure (secrets in code, logging PII)
- N+1 queries, expensive loops, blocking I/O
- Memory leaks, unbounded growth, missing pagination

#### 2d. Testing & Reliability
Assess:
- Test coverage for new/changed logic
- Edge cases and boundary conditions
- Quality of mocks and test isolation
- Flaky test risks (time-dependent, order-dependent tests)
- Missing integration or contract tests for API changes

#### 2e. Suggestions for Improvement
For each actionable suggestion:
1. State the issue clearly and concisely
2. Explain the rationale (why it matters)
3. Provide a before/after code snippet when possible
4. Label the severity inline: `[CRITICAL]`, `[NEEDS_IMPROVEMENT]`, `[NIT]`

**Snippet format:**
```
**Issue:** [one-line description]
**Why it matters:** [1–2 sentences]
**Suggestion:**
```language
// Before
<problematic code>

// After
<improved code>
```
```

---

### 3. Tone & Delivery Rules

Always follow these rules when writing review text:

| Rule | Example |
|---|---|
| Lead with positives before critiques | "Great work extracting this into a service. For the error path, consider..." |
| Frame issues as opportunities | "This could be even more robust if we..." |
| Use softening openers for non-critical items | "Consider...", "It might be worth...", "One small thing..." |
| Be direct for critical issues | "This is a security vulnerability — we must address before merge." |
| Avoid "you" accusations | ❌ "You forgot to validate input" → ✅ "Input validation is missing here" |
| Explain the *why* always | Never leave a bare "fix this" without rationale |
| Acknowledge uncertainty | "I'm not sure of the full context, but..." |

---

### 4. Actionable Labels Block

End every review with a label summary block in this exact format.
Include all four label types; write `None identified` if a category has no findings.

```markdown
---
## 🏷️ Review Labels

| Label | Count | Justification |
|---|---|---|
| 🔴 `CRITICAL` | N | [Brief summary of critical findings, or "None identified"] |
| 🟡 `NEEDS_IMPROVEMENT` | N | [Brief summary of improvements needed, or "None identified"] |
| 🔵 `NIT / QUESTION` | N | [Brief summary of nits/questions, or "None identified"] |
| 🟢 `POSITIVE` | N | [Brief summary of standout positives, or "None identified"] |

**Overall recommendation:** `APPROVE` / `REQUEST_CHANGES` / `COMMENT`
> [One sentence rationale for the recommendation]
```

Use these criteria for the overall recommendation:
- `APPROVE` — No CRITICAL issues; NEEDS_IMPROVEMENT items are minor or addressed inline
- `REQUEST_CHANGES` — One or more CRITICAL issues, or several significant NEEDS_IMPROVEMENT items
- `COMMENT` — Questions or nitpicks only; no blocking concerns but feedback worth discussing

---

## Full Example Output

Below is a complete example review to use as a quality reference.

---

> **PR:** `feat: add user authentication via JWT`
> **Files changed:** `auth/jwt.py`, `routes/users.py`, `tests/test_auth.py`

---

## 📋 Review Summary

This PR adds JWT-based authentication to the user routes. The goal is to protect
`/users` endpoints behind token verification. Changes span 3 files: a new `jwt.py`
utility, updated route guards in `users.py`, and a new test file. The overall approach
is sound, but there are a few security and reliability items to address before merge.

---

## 🏗️ High-Level Feedback

The decision to centralise JWT logic in `auth/jwt.py` is a great call — it keeps
token handling out of the route layer and will make future algorithm changes straightforward.
One broader concern: the current implementation tightly couples token creation *and*
validation in the same module. Consider separating these into `auth/jwt_issuer.py` and
`auth/jwt_verifier.py` as the surface area grows, keeping the single-responsibility
principle intact.

---

## 🧹 Code Quality & Best Practices

- **`jwt.py` line 14** — The `SECRET_KEY` is hardcoded as a string literal. Even in
  non-production code this is risky to commit. Consider reading from environment variables:
  ```python
  import os
  SECRET_KEY = os.environ["JWT_SECRET_KEY"]
  ```
- **`routes/users.py` line 32** — The magic number `3600` (token expiry) appears without
  explanation. A named constant improves readability:
  ```python
  TOKEN_EXPIRY_SECONDS = 3600  # 1 hour
  ```
- **`jwt.py` line 28** — The function `make_token()` is 47 lines long. It might be
  beneficial to extract the payload-building step into a private `_build_payload()` helper.

---

## 🔒 Security & Performance

`[CRITICAL]` **`jwt.py` line 22** — The `verify_token()` function catches all exceptions
with a bare `except Exception` and returns `None` silently. This masks tampered-token
errors from monitoring and could hide active attacks. Catch `jwt.ExpiredSignatureError`
and `jwt.InvalidTokenError` explicitly and log them:
```python
# Before
try:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
except Exception:
    return None

# After
import logging
logger = logging.getLogger(__name__)

try:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
except jwt.ExpiredSignatureError:
    logger.warning("JWT expired", extra={"token_prefix": token[:8]})
    raise
except jwt.InvalidTokenError as e:
    logger.error("JWT validation failed: %s", e)
    raise
```

`[NEEDS_IMPROVEMENT]` **`routes/users.py` line 58** — The `/users` list endpoint has no
pagination. With a large user table this will load all rows into memory. Consider adding
`limit` / `offset` query parameters before this merges.

---

## 🧪 Testing & Reliability

Great work adding `tests/test_auth.py` — the happy-path coverage is solid.

- **Missing edge cases:**
  - Expired token (past `exp` claim) — should return 401
  - Tampered signature — should return 401
  - Token with missing `sub` claim — should return 400
- **`test_auth.py` line 41** — `datetime.now()` in the test makes expiry assertions
  time-dependent and potentially flaky. Consider freezing time with `freezegun`:
  ```python
  from freezegun import freeze_time

  @freeze_time("2024-01-01 12:00:00")
  def test_token_expires():
      ...
  ```

---

## 💡 Suggestions for Improvement

1. **Add algorithm pinning to decode call** `[NEEDS_IMPROVEMENT]`
   PyJWT supports the `none` algorithm by default in some versions. Explicitly
   whitelist `HS256` to prevent algorithm-confusion attacks:
   ```python
   jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   ```
   This is already partially done — just ensure it's consistent across all decode calls.

2. **Return typed responses from `verify_token`** `[NIT]`
   Returning `None` on failure makes callers check `if result is None` everywhere.
   A `Union[Payload, None]` type hint or raising a custom `InvalidTokenError` exception
   would make the contract explicit and easier to type-check with mypy.

---

## 🏷️ Review Labels

| Label | Count | Justification |
|---|---|---|
| 🔴 `CRITICAL` | 1 | Silent exception swallowing in `verify_token` masks security events |
| 🟡 `NEEDS_IMPROVEMENT` | 3 | Hardcoded secret, missing pagination, missing test edge cases |
| 🔵 `NIT / QUESTION` | 2 | Return type clarity, magic number for expiry |
| 🟢 `POSITIVE` | 2 | Clean module separation, good happy-path test coverage |

**Overall recommendation:** `REQUEST_CHANGES`
> The hardcoded secret key and silent exception handling are blocking issues that must be
> resolved before this is safe to merge.

---

## Execution Checklist

Before generating the review, mentally verify:

- [ ] I have read the full diff, not just the first file
- [ ] I understand the PR's stated goal and haven't reviewed for a different objective
- [ ] Every CRITICAL item is genuinely blocking (not just a preference)
- [ ] Every code snippet compiles / runs correctly in the target language
- [ ] The tone is collaborative — no blaming language
- [ ] At least one POSITIVE label is assigned if any good work is present
- [ ] The overall recommendation (`APPROVE` / `REQUEST_CHANGES` / `COMMENT`) is justified

**When using GitHub CLI:**
- [ ] Check that GitHub CLI (`gh`) is installed and authenticated
- [ ] Fetch PR details using `gh pr view <PR_NUMBER> --json ...`
- [ ] Fetch the diff using `gh pr diff <PR_NUMBER>`
- [ ] Write the review to a temporary file
- [ ] Post the review using `gh pr comment <PR_NUMBER> --body-file <FILE>`
- [ ] Clean up the temporary file after posting

---

## Language-Specific Guidance

Apply these additional heuristics when the language is known:

### Python
- Check for bare `except:` clauses
- Flag mutable default arguments (`def f(x=[])`)
- Note missing type hints in new functions
- Check for `os.environ.get` vs `os.environ[]` (silent vs loud missing keys)

### TypeScript / JavaScript
- Flag `any` type usage — suggest specific types or `unknown`
- Check for unhandled promise rejections (missing `await` or `.catch`)
- Note `console.log` left in production paths
- Flag direct DOM manipulation in React components

### Go
- Check that errors are not silently discarded (`_ = err`)
- Note missing `defer cancel()` after `context.WithCancel`
- Flag goroutine leaks (goroutines without exit conditions)

### Java / Kotlin
- Flag unclosed resources (streams, connections without try-with-resources)
- Note missing `@NonNull` / `@Nullable` annotations in public APIs
- Check for `NullPointerException` risks in optional chaining

### SQL / Database migrations
- Flag missing rollback scripts
- Note missing indexes on foreign keys or frequently-queried columns
- Check for destructive operations (`DROP`, `TRUNCATE`) without backup notes