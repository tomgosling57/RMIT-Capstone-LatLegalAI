"""Jira connection settings, read from the environment.

Set these before running any of the ``jira_*.py`` scripts:

    export JIRA_BASE_URL="yourorg.atlassian.net"
    export JIRA_EMAIL="you@example.com"
    export JIRA_API_TOKEN="your-api-token"

Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens.
"""

import os

API_TOKEN: str = os.environ.get("JIRA_API_TOKEN", "")
EMAIL: str = os.environ.get("JIRA_EMAIL", "")
BASE_URL: str = os.environ.get("JIRA_BASE_URL", "")
DEFAULT_PROJECT: str = os.environ.get("JIRA_PROJECT", "")
