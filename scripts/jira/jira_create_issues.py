import requests
from requests.auth import HTTPBasicAuth

from config import BASE_URL, EMAIL, API_TOKEN, DEFAULT_PROJECT

if not all((BASE_URL, EMAIL, API_TOKEN)):
    raise SystemExit(
        "Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment first."
    )


def _format_as_json(result):
    """Format the API result as pretty-printed JSON."""
    return json.dumps(result, indent=2, default=str)


def _format_as_markdown(result):
    """Format the API result as Markdown."""
    issues = result.get("issues", [])
    errors = result.get("errors", [])

    lines = ["# Created Issues\n"]

    if issues:
        lines.append("| Key | Status |\n|-----|--------|")
        for issue in issues:
            key = issue.get("key", "N/A")
            status_code = (
                issue.get("transition", {}).get("status", "N/A")
                if issue.get("transition")
                else "Created"
            )
            lines.append(f"| {key} | {status_code} |")

    if errors:
        lines.append("\n## Errors\n")
        for err in errors:
            lines.append(f"- {json.dumps(err)}")

    return "\n".join(lines)


def _format_as_console(result):
    """Format the API result as human-readable console output."""
    issues = result.get("issues", [])
    errors = result.get("errors", [])

    lines = []
    if issues:
        lines.append(f"\n{'='*50}")
        lines.append("  CREATED ISSUES")
        lines.append(f"{'='*50}")
        for issue in issues:
            key = issue.get("key", "N/A")
            lines.append(f"  ✓ {key}")
        lines.append(f"{'='*50}")

    if errors:
        lines.append(f"\n  Errors: {len(errors)}")
        for err in errors:
            lines.append(f"  ✗ {err}")

    return "\n".join(lines)


def create_issues_bulk(
    issue_data,
    domain=BASE_URL,
    email=EMAIL,
    token=API_TOKEN,
    project_key=DEFAULT_PROJECT,
    output_format="console",
):
    """
    Create issues in bulk using the Jira Bulk Create API.

    Args:
        issue_data: List of dicts with 'summary' and optional 'description' keys
        domain: Jira instance domain
        email: User email for authentication
        token: API token
        project_key: Project key prefix (e.g. "AALA")
        output_format: Output format - 'console', 'json', or 'markdown'

    Returns:
        API response dict with 'issues' and 'errors' keys
    """
    url = f"https://{domain}/rest/api/3/issue/bulk"
    auth = HTTPBasicAuth(email, token)

    payload = {"issueUpdates": []}

    for item in issue_data:
        fields = {
            "project": {"key": project_key},
            "summary": item["summary"],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": item.get("description", ""),
                                "type": "text",
                            }
                        ],
                    }
                ],
            },
            "issuetype": {"name": item.get("issuetype", "Task")},
        }

        # Add priority if provided
        if "priority" in item:
            fields["priority"] = {"name": item["priority"]}

        payload["issueUpdates"].append({"fields": fields})

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        auth=auth,
    )

    result = response.json()

    if response.status_code == 201:
        if output_format == "json":
            print(_format_as_json(result))
        elif output_format == "markdown":
            print(_format_as_markdown(result))
        else:
            print(_format_as_console(result))
    else:
        print(f"Error: {response.status_code}")
        print(json.dumps(result, indent=2))

    return result


# Example usage
if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path

    # Load issues from JSON file (first CLI arg or default)
    json_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/jira/sprint-9-tasks.json"
    with open(json_path) as f:
        data = json.load(f)

    # Run creation and capture result
    result = create_issues_bulk(data, output_format="json")

    # Save result to a file alongside the input
    output_path = Path(json_path).with_suffix(".result.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")
