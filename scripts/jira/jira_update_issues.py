import requests
import json
from requests.auth import HTTPBasicAuth

from config import BASE_URL, EMAIL, API_TOKEN, DEFAULT_PROJECT

if not all((BASE_URL, EMAIL, API_TOKEN)):
    raise SystemExit(
        "Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in the environment first."
    )


def _format_as_json(results):
    """Format results as pretty-printed JSON."""
    return json.dumps(results, indent=2, default=str)


def _format_as_markdown(results):
    """Format results as Markdown."""
    lines = ["# Updated Issues\n"]
    lines.append("| Key | Status |\n|-----|--------|")
    for key, status_code in results:
        status = "✅ Updated" if status_code == 204 else f"❌ Error {status_code}"
        lines.append(f"| {key} | {status} |")
    return "\n".join(lines)


def _format_as_console(results):
    """Format results as human-readable console output."""
    lines = [f"\n{'='*50}", "  UPDATE RESULTS", f"{'='*50}"]
    for key, status_code in results:
        if status_code == 204:
            lines.append(f"  ✓ {key} — updated successfully")
        else:
            lines.append(f"  ✗ {key} — error {status_code}")
    lines.append(f"{'='*50}")
    return "\n".join(lines)


def update_issues_batch(
    update_list,
    domain=BASE_URL,
    email=EMAIL,
    token=API_TOKEN,
    project_key=DEFAULT_PROJECT,
    output_format="console",
):
    """
    Update issues in batch using the Jira Edit Issue API.

    Args:
        update_list: List of dicts with 'key' and fields to update.
                     Example: [{"key": "AALA-74", "summary": "New Title"}]
        domain: Jira instance domain
        email: User email for authentication
        token: API token
        project_key: Not used directly but kept for API consistency across scripts
        output_format: Output format - 'console', 'json', or 'markdown'

    Returns:
        List of (issue_key, status_code) tuples
    """
    auth = HTTPBasicAuth(email, token)
    results = []

    for item in update_list:
        issue_key = item.get("key")
        if issue_key is None:
            print(f"  ✗ Skipping item — missing 'key' field: {item}")
            continue
        url = f"https://{domain}/rest/api/3/issue/{issue_key}"

        # Build the update payload — exclude 'key' from fields
        fields = {k: v for k, v in item.items() if k != "key"}
        payload = {"fields": fields}

        response = requests.put(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            auth=auth,
        )
        results.append((issue_key, response.status_code))

    if output_format == "json":
        print(_format_as_json(results))
    elif output_format == "markdown":
        print(_format_as_markdown(results))
    else:
        print(_format_as_console(results))

    return results


# Usage Example
if __name__ == "__main__":
    updates = [{"key": "AALA-74", "summary": "Updated via API"}]
    update_issues_batch(updates)
