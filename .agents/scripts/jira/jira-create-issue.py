#!/usr/bin/env python3
"""
Create Jira issues using the Jira REST API.
"""

import json
import base64
import sys
from pathlib import Path


def load_config():
    """Load Jira configuration from config file."""
    config_paths = [
        Path(".agents/jira-config.json"),
        Path.home() / ".agents/jira-config.json",
        Path.home() / ".claude-skills/jira-config.json",
    ]

    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break

    if not config_file:
        print("Error: Jira configuration file not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Using config: {config_file}", file=sys.stderr)

    with open(config_file, "r") as f:
        config = json.load(f)

    required_fields = ["base_url", "email", "api_token"]
    for field in required_fields:
        if field not in config or not config[field]:
            print(
                f"Error: Missing required field '{field}' in configuration.",
                file=sys.stderr,
            )
            sys.exit(1)

    return config


def create_issue(
    config, summary, description, issue_type="Task", project_key="SCRUM", labels=None
):
    """Create a Jira issue."""
    import urllib.request
    import urllib.error

    url = f"{config['base_url']}/rest/api/3/issue"

    # Prepare authentication
    auth_string = f"{config['email']}:{config['api_token']}"
    auth_bytes = auth_string.encode("ascii")
    auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

    # Prepare issue data
    issue_data = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
        }
    }

    if labels:
        issue_data["fields"]["labels"] = labels

    # Convert to JSON
    data = json.dumps(issue_data).encode("utf-8")

    # Create request
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode("utf-8"))
        print(f"Created issue: {response_data['key']}")
        print(f"URL: {config['base_url']}/browse/{response_data['key']}")
        return response_data["key"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Error creating issue: HTTP {e.code}", file=sys.stderr)
        print(f"Response: {error_body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error creating issue: {e}", file=sys.stderr)
        return None


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <summary> <description> [issue_type] [project_key]",
            file=sys.stderr,
        )
        print(
            f"Example: {sys.argv[0]} 'Fix bug' 'Description here' Task SCRUM",
            file=sys.stderr,
        )
        sys.exit(1)

    summary = sys.argv[1]
    description = sys.argv[2]
    issue_type = sys.argv[3] if len(sys.argv) > 3 else "Task"
    project_key = sys.argv[4] if len(sys.argv) > 4 else "SCRUM"

    config = load_config()
    create_issue(config, summary, description, issue_type, project_key)


if __name__ == "__main__":
    main()
