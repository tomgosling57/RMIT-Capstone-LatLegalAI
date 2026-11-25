import requests
import json
from requests.auth import HTTPBasicAuth

from config import BASE_URL, EMAIL, API_TOKEN, DEFAULT_PROJECT

if not all((BASE_URL, EMAIL, API_TOKEN)):
    raise SystemExit(
        "Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment first."
    )


def _format_as_console(issues):
    """Format issues as a human-readable console output."""
    lines = []
    for issue in issues:
        key = issue.get("key", "N/A")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = (
            fields.get("status", {}).get("name", "N/A")
            if fields.get("status")
            else "N/A"
        )
        assignee = (
            fields.get("assignee", {}).get("displayName", "Unassigned")
            if fields.get("assignee")
            else "Unassigned"
        )
        priority = (
            fields.get("priority", {}).get("name", "N/A")
            if fields.get("priority")
            else "N/A"
        )
        issue_type = (
            fields.get("issuetype", {}).get("name", "N/A")
            if fields.get("issuetype")
            else "N/A"
        )
        created = fields.get("created", "N/A")
        description = fields.get("description", "N/A")
        reporter = (
            fields.get("reporter", {}).get("displayName", "N/A")
            if fields.get("reporter")
            else "N/A"
        )
        labels = ", ".join(fields.get("labels", [])) or "None"
        duedate = fields.get("duedate", "N/A")

        lines.append(f"\n{'='*60}")
        lines.append(f"  {key}  [{issue_type}]  {status}")
        lines.append(f"{'='*60}")
        lines.append(f"  Summary:   {summary}")
        lines.append(f"  Priority:  {priority}")
        lines.append(f"  Assignee:  {assignee}")
        lines.append(f"  Reporter:  {reporter}")
        lines.append(f"  Created:   {created}")
        lines.append(f"  Due Date:  {duedate}")
        lines.append(f"  Labels:    {labels}")
        lines.append(f"  Description: {description}")
        lines.append(f"{'='*60}")

    return "\n".join(lines)


def _format_as_json(issues):
    """Format issues as pretty-printed JSON."""
    return json.dumps(issues, indent=2, default=str)


def _format_as_markdown(issues):
    """Format issues as Markdown suitable for issue creation or documentation."""
    blocks = []
    for issue in issues:
        key = issue.get("key", "N/A")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "N/A")
        status = (
            fields.get("status", {}).get("name", "N/A")
            if fields.get("status")
            else "N/A"
        )
        assignee = (
            fields.get("assignee", {}).get("displayName", "Unassigned")
            if fields.get("assignee")
            else "Unassigned"
        )
        priority = (
            fields.get("priority", {}).get("name", "N/A")
            if fields.get("priority")
            else "N/A"
        )
        issue_type = (
            fields.get("issuetype", {}).get("name", "N/A")
            if fields.get("issuetype")
            else "N/A"
        )
        created = fields.get("created", "N/A")
        description = fields.get("description", "")
        reporter = (
            fields.get("reporter", {}).get("displayName", "N/A")
            if fields.get("reporter")
            else "N/A"
        )
        labels = fields.get("labels", [])
        duedate = fields.get("duedate", "N/A")
        project_name = (
            fields.get("project", {}).get("name", "N/A")
            if fields.get("project")
            else "N/A"
        )

        # Build a clean markdown block
        block = f"""---
key: {key}
type: {issue_type}
status: {status}
project: {project_name}
---

# {summary}

| Field       | Value       |
|-------------|-------------|
| **Key**     | {key}       |
| **Type**    | {issue_type} |
| **Status**  | {status}    |
| **Priority**| {priority}  |
| **Assignee**| {assignee}  |
| **Reporter**| {reporter}  |
| **Created** | {created}   |
| **Due Date**| {duedate}   |
| **Labels**  | {', '.join(labels) if labels else 'None'} |

## Description

{description if description else '*No description provided.*'}

---
"""
        blocks.append(block)

    return "\n".join(blocks)


def get_batch_issues(
    id_list,
    domain=BASE_URL,
    email=EMAIL,
    token=API_TOKEN,
    project_key=DEFAULT_PROJECT,
    output_format="console",
):
    """
    Fetch full issue details for a list of issue numbers using the Jira Bulk Fetch API.

    Uses POST /rest/api/3/issue/bulkfetch which returns complete issue data
    including summary, status, assignee, priority, etc.

    Args:
        id_list: Comma-separated string of issue numbers (e.g. "74,75,76")
        domain: Jira instance domain
        email: User email for authentication
        token: API token
        project_key: Project key prefix (e.g. "AALA")
        output_format: Output format - 'console', 'json', or 'markdown'

    Returns:
        List of issue dicts from the API response
    """
    url = f"https://{domain}/rest/api/3/issue/bulkfetch"
    auth = HTTPBasicAuth(email, token)

    # Convert [74, 75] into ['AALA-74', 'AALA-75']
    issue_keys = [f"{project_key}-{i.strip()}" for i in id_list.split(",")]

    payload = {
        "issueIdsOrKeys": issue_keys,
        "fields": [
            "summary",
            "status",
            "assignee",
            "priority",
            "issuetype",
            "project",
            "created",
            "updated",
            "duedate",
            "description",
            "reporter",
            "labels",
            "fixVersions",
            "components",
        ],
        "fieldsByKeys": False,
    }

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers, auth=auth)

    if response.status_code == 200:
        result = response.json()
        issues = result.get("issues", [])
        errors = result.get("issueErrors", [])

        if errors:
            print(f"Errors fetching some issues: {json.dumps(errors, indent=2)}")

        # Format and print output based on the requested format
        if output_format == "json":
            print(_format_as_json(issues))
        elif output_format == "markdown":
            print(_format_as_markdown(issues))
        else:
            print(_format_as_console(issues))

        return issues
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


# Usage
# get_batch_issues("74,75,76")
# get_batch_issues("74,75,76", output_format='json')
# get_batch_issues("74,75,76", output_format='markdown')

if __name__ == "__main__":
    get_batch_issues("71,76,93,96")
