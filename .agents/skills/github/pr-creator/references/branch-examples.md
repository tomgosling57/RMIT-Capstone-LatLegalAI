# Branch Naming Examples

## Features
| Jira Issue | Title | Branch |
|---|---|---|
| PROJ-101 | Add user profile page | `feature/proj-101/user-profile-page` |
| PROJ-202 | Implement search with filters | `feature/proj-202/search-filters` |
| PROJ-303 | OAuth2 Google login | `feature/proj-303/google-oauth` |

## Bug Fixes
| Jira Issue | Title | Branch |
|---|---|---|
| PROJ-401 | Fix null pointer on logout | `fix/proj-401/null-pointer-logout` |
| PROJ-402 | Token expiry not handled | `fix/proj-402/token-expiry` |

## Chores / Infra
| Jira Issue | Title | Branch |
|---|---|---|
| PROJ-501 | Upgrade to React 18 | `chore/proj-501/upgrade-react-18` |
| PROJ-502 | Add ESLint config | `chore/proj-502/eslint-config` |
| N/A | Shared migration for auth tables | `chore/db-migration/auth-tables` |

## Slug Rules
- Max 5 words
- Drop: "the", "a", "an", "for", "with", "and", "of"
- Replace spaces with `-`
- Lowercase only
- No special characters
