# Sprint Summary Template

This is the canonical template for sprint summary documents. It matches the format of [`docs/sprints/sprint-five-summary.md`](../../../../docs/sprints/sprint-five-summary.md).

```markdown
# Sprint <N> Summary — <Source> to <Target>

**Pull Request:** [#<PR_NUMBER> — <TITLE>](<PR_URL>)
**Branch:** `<SOURCE>` → `<TARGET>`
**Date:** <YYYY-MM-DD>
**Total Changes:** +<ADDITIONS> additions / −<DELETIONS> deletions across <FILES> files

---

## Overview

<Sprint overview paragraph — 2-3 sentences summarising the major themes of the sprint>

## Summary of Issues Completed

| Key | Summary | Type | Status | Assignee |
|-----|---------|------|--------|----------|
| <KEY> | <Summary> | <Type> | <Status> | <Assignee> |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total additions | <N> |
| Total deletions | <N> |
| Files changed | <N> |
| New files created | <N> |
| Files deleted | <N> |
| Issues completed | <N> |
| <Other sprint-specific metrics> | <N> |

---

## Files Changed Summary

### New Files (<N>)

| File | Lines | Category |
|------|-------|----------|
| `<path>` | <N> | <Category> |

### Deleted Files (<N>)

| File | Lines | Reason |
|------|-------|--------|
| `<path>` | <N> | <Reason> |

### Modified Files (<N>)

| File | Lines | Change |
|------|-------|--------|
| `<path>` | +N / −N | <Description> |

---

## Key Changes This Sprint
* <Bullet point summary of the most important changes this sprint>
  * <Supporting detail for the change above>
* <Next major change>
  * <Supporting detail>
* <Next major change>

---

## Architecture Diagram

```
<ASCII architecture diagram showing the system structure>
```

[<KEY>]: <JIRA_URL>

---

## 1. <Major Theme 1>

### 1.1 <Sub-topic> ([<KEY>])

**Issue:** <Issue Summary> — *<Status>*

<Narrative description of what changed, why, and how it works>

#### What Changed

<Detailed description>

#### New Endpoint Structure / Key Components

| <Header> | <Header> | <Header> |
|----------|----------|----------|
| <Value> | <Value> | <Value> |

#### Files Removed / Modified

| File | Change | Purpose |
|------|--------|---------|
| `<path>` | <Change> | <Purpose> |

---

## <N>. <Major Theme N>

...

---

## <N+1>. Bug Fixes

### <N+1>.1 <Bug Title> ([<KEY>])

**Issue:** <Issue Summary> — *<Status>*

**Symptoms:** <Description>

**Root Cause:** <Description>

**Fix:** <Description>

---

## <N+2>. Configuration & Housekeeping

### <N+2>.1 <Topic>

<Description of changes>
```
