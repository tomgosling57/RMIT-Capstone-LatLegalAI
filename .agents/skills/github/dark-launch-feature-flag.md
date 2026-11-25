# Skill: dark-launch-feature-flag

**Category**: Strategy — Partial / Incomplete Features  
**Best for**: Merging code that isn't ready to be user-facing yet  
**Key rule**: Code behind a flag that defaults to OFF is always safe to merge.

## When to use

- You want to merge backend logic now and ship UI later
- You need to keep main green while a feature spans multiple sprints
- You want to test in production with a small group before full rollout

## Concept

```
Week 1: merge backend  (flag = OFF → invisible to users)
Week 2: merge UI       (flag = OFF → invisible to users)
Week 3: enable flag    (flag = ON  → feature goes live)
```

At no point is main ever in a "broken" state.

## Implementation pattern

```javascript
// config/flags.js (or equivalent for your stack)
module.exports = {
  NEW_CHECKOUT_FLOW: process.env.NEW_CHECKOUT_FLOW === 'true' || false,
}

// Usage in code
const flags = require('../config/flags')
if (flags.NEW_CHECKOUT_FLOW) {
  // new code path
} else {
  // existing code path
}
```

## Commands

```bash
# --- Step 1: Verify flag defaults to OFF ---
grep -r "NEW_CHECKOUT_FLOW" config/
# Confirm the default value is false / absent

# --- Step 2: Ship backend behind flag ---
git checkout -b feat/checkout-backend main
git add src/services/checkout* config/flags.js
git commit -m "feat: checkout backend service (flag off)"
git push -u origin feat/checkout-backend
gh pr create \
  --base main \
  --title "feat: checkout backend (dark launch)" \
  --label "feature-flag" \
  --body "$(cat <<'BODY'
## What this does
Adds the new checkout service layer behind the `NEW_CHECKOUT_FLOW` feature flag.

## Safety
Flag defaults to `false` — no user-facing change. Safe to merge at any time.

## Testing
To test locally: `NEW_CHECKOUT_FLOW=true npm start`
BODY
)"

# --- Step 3: Ship UI behind same flag (separate PR) ---
git checkout -b feat/checkout-ui main
git add src/components/Checkout* src/pages/checkout*
git commit -m "feat: checkout UI (flag off)"
git push -u origin feat/checkout-ui
gh pr create \
  --base main \
  --title "feat: checkout UI (dark launch)" \
  --label "feature-flag" \
  --body "UI for new checkout flow. Gated behind NEW_CHECKOUT_FLOW flag."

# --- Step 4: Enable the flag (final PR) ---
git checkout -b chore/enable-checkout-flag main
# Edit config/flags.js: NEW_CHECKOUT_FLOW: true
git add config/flags.js
git commit -m "chore: enable NEW_CHECKOUT_FLOW flag"
git push -u origin chore/enable-checkout-flag
gh pr create \
  --base main \
  --title "chore: enable NEW_CHECKOUT_FLOW" \
  --label "release" \
  --body "Flips the flag ON. All backend + UI PRs must be merged first."
```

## Checking flag status across PRs

```bash
# See all open PRs with the feature-flag label
gh pr list --label "feature-flag"

# Check if flag is enabled in any environment
gh run list --workflow=deploy.yml   # check recent deploys
```

## Tips

- Name flags in SCREAMING_SNAKE_CASE so they're easy to grep for
- Add a comment above every flag usage with a link to the tracking issue
- Clean up old flags after the feature fully ships — flag debt is real
- For env-based flags: document in `.env.example` with a comment explaining the flag
