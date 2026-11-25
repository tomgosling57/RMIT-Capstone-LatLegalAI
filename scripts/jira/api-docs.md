    About
    Version
    Authentication and authorization
    Permissions
    Expansion, pagination, and ordering
    Timestamps
    Special headers
    Anonymous operations
    Asynchronous operations
    Experimental features
    Status codes

    Announcement banner
    App data policies
    App migration
    App properties
    Application roles
    Audit records
    Avatars
    Classification levels
    Dashboards
    Dynamic modules
    Field schemes
    Filter sharing
    Filters
    Group and user picker
    Groups
    Issue attachments
    Issue comment properties
    Issue comments
    Issue custom field associations
    Issue custom field configuration (apps)
    Issue custom field contexts
    Issue custom field options
    Issue custom field options (apps)
    Issue custom field values (apps)
    Issue field configurations
    Issue fields
    Issue link types
    Issue links
    Issue navigator settings
    Issue notification schemes
    Issue panels
    Issue priorities
    Issue properties
    Issue redaction
    Issue remote links
    Issue resolutions
    Issue search
    Issue security level
    Issue security schemes
    Issue type properties
    Issue type schemes
    Issue type screen schemes
    Issue types
    Issue votes
    Issue watchers
    Issue worklog properties
    Issue worklogs
    Issues
        POSTBulk fetch changelogs
        GETGet events
        POSTCreate issue
        PUTArchive issue(s) by issue ID/key
        POSTArchive issue(s) by JQL
        POSTBulk create issue
        POSTBulk fetch issues
        GETGet create issue metadata
        GETGet create metadata issue types for a project
        GETGet create field metadata for a project and issue type id
        GETGet issue limit report
        PUTUnarchive issue(s) by issue keys/ID
        GETGet issue
        PUTEdit issue
        DELDelete issue
        PUTAssign issue
        GETGet changelogs
        POSTGet changelogs by IDs
        GETGet edit issue metadata
        POSTSend notification for issue
        GETGet transitions
        POSTTransition issue
        PUTExport archived issue(s)
    JQL
    JQL functions (apps)
    Jira expressions
    Jira settings
    Labels
    License metrics
    Migration of Connect modules to Forge
    Myself
    Permission schemes
    Permissions
    Plans
    Priority schemes
    Project avatars
    Project categories
    Project classification levels
    Project components
    Project email
    Project features
    Project key and name validation
    Project permission schemes
    Project properties
    Project role actors
    Project roles
    Project templates
    Project types
    Project versions
    Projects
    Screen schemes
    Screen tab fields
    Screen tabs
    Screens
    Server info
    Service Registry
    Status
    Tasks
    Teams in plan
    Time tracking
    UI modifications (apps)
    User properties
    User search
    Users
    Webhooks
    Workflow scheme drafts
    Workflow scheme project associations
    Workflow schemes
    Workflow status categories
    Workflow statuses
    Workflow transition properties
    Workflow transition rules
    Workflows
    Other operations

Cloud
Jira Cloud platform / Reference / REST API v2
Issues
Postman Collection
OpenAPI

This resource represents Jira issues. Use it to:

    create or edit issues, individually or in bulk.
    retrieve metadata about the options for creating or editing issues.
    delete an issue.
    assign a user to an issue.
    get issue changelogs.
    send notifications about an issue.
    get details of the transitions available for an issue.
    transition an issue.
    Archive issues.
    Unarchive issues.
    Export archived issues.

Operations
POST/rest/api/2/changelog/bulkfetch
GET/rest/api/2/events
POST/rest/api/2/issue
PUT/rest/api/2/issue/archive
POST/rest/api/2/issue/archive
POST/rest/api/2/issue/bulk
POST/rest/api/2/issue/bulkfetch
GET/rest/api/2/issue/createmeta
GET/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes
GET/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}
GET/rest/api/2/issue/limit/report
PUT/rest/api/2/issue/unarchive
GET/rest/api/2/issue/{issueIdOrKey}
PUT/rest/api/2/issue/{issueIdOrKey}
DEL/rest/api/2/issue/{issueIdOrKey}
PUT/rest/api/2/issue/{issueIdOrKey}/assignee
GET/rest/api/2/issue/{issueIdOrKey}/changelog
POST/rest/api/2/issue/{issueIdOrKey}/changelog/list
GET/rest/api/2/issue/{issueIdOrKey}/editmeta
POST/rest/api/2/issue/{issueIdOrKey}/notify
GET/rest/api/2/issue/{issueIdOrKey}/transitions
POST/rest/api/2/issue/{issueIdOrKey}/transitions
PUT/rest/api/2/issues/archive/export
POST
Bulk fetch changelogs

Bulk fetch changelogs for multiple issues and filter by fields

Returns a paginated list of all changelogs for given issues sorted by changelog date and issue IDs, starting from the oldest changelog and smallest issue ID.

Issues are identified by their ID or key, and optionally changelogs can be filtered by their field IDs. You can request the changelogs of up to 1000 issues and can filter them by up to 10 field IDs.

Permissions required:

    Browse projects project permission for the projects that the issues are in.
    If issue-level security is configured, issue-level security permission to view the issues.

Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:avatar:jira, read:issue.changelog:jira

Connect apps cannot access this REST resource.
Request
Request bodyapplication/json

A JSON object containing the bulk fetch changelog request filters such as issue IDs and field IDs.
fieldIds

array<string>
issueIdsOrKeys

array<string>
Required
maxResults

integer
nextPageToken

string
Responses

Returned if the request is successful.
application/json
BulkChangelogResponseBean

A page of changelogs which is designed to handle multiple issues
POST/rest/api/2/changelog/bulkfetch
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/changelog/bulkfetch"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "fieldIds": [
    "<string>"
  ],
  "issueIdsOrKeys": [
    "<string>"
  ],
  "maxResults": 46,
  "nextPageToken": "<string>"
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "issueChangeLogs": [
    {
      "changeHistories": [
        {
          "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "active": true,
            "avatarUrls": {
              "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
              "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
              "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
              "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
            },
            "displayName": "Mia Krystof",
            "emailAddress": "mia@example.com",
            "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g",
            "timeZone": "Australia/Sydney"
          },
          "created": 1492070429,
          "id": "10001",
          "items": [
            {
              "field": "fields",
              "fieldId": "fieldId",
              "fieldtype": "jira",
              "fromString": "old summary",
              "toString": "new summary"
            }
          ]
        },
        {
          "author": {
            "accountId": "5b10a2844c20165700ede21g",
            "active": true,
            "avatarUrls": {
              "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
              "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
              "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
              "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
            },
            "displayName": "Mia Krystof",
            "emailAddress": "mia@example.com",
            "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g",
            "timeZone": "Australia/Sydney"
          },
          "created": 1492071429,
          "id": "10002",
          "items": [
            {
              "field": "fields",
              "fieldId": "fieldId",
              "fieldtype": "jira",
              "fromString": "old summary 2",
              "toString": "new summary 2"
            }
          ]
        }
      ],
      "issueId": "10100"
    }
  ],
  "nextPageToken": "UxAQBFRF"
}
GET
Get eventsExperimental

Returns all issue events.

Permissions required: Administer Jira global permission.
Data Security Policy: Exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:manage:jira-configuration
Granular:read:issue-event:jira

Connect app scope required: ADMIN
Request

This request has no parameters.
Responses

Returned if the request is successful.
application/json

array<IssueEvent>
GET/rest/api/2/events
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/events"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
[
  {
    "id": 1,
    "name": "Issue Created"
  },
  {
    "id": 2,
    "name": "Issue Updated"
  }
]
POST
Create issue

Creates an issue or, where the option to create subtasks is enabled in Jira, a subtask. A transition may be applied, to move the issue or subtask to a workflow step other than the default start step, and issue properties set.

The content of the issue or subtask is defined using update and fields. The fields that can be set in the issue or subtask are determined using the Get create issue metadata. These are the same fields that appear on the issue's create screen.

Creating a subtask differs from creating an issue as follows:

    issueType must be set to a subtask issue type (use Get create issue metadata to find subtask issue types).
    parent must contain the ID or key of the parent issue.

Permissions required: Browse projects and Create issues project permissions for the project in which the issue or subtask is created.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira, write:comment:jira, write:comment.property:jira, write:attachment:jira, read:issue:jira

Connect app scope required: WRITE
Request
Query parameters
updateHistory

boolean
Request bodyapplication/json
fields

object
historyMetadata

HistoryMetadata
properties

array<EntityProperty>
transition

IssueTransition
update

object
Additional Properties

any
Responses

Returned if the request is successful.
application/json
CreatedIssue

Details about a created issue or subtask.
POST/rest/api/2/issue
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "fields": {
    "assignee": {
      "id": "5b109f2e9729b51b54dc274d"
    },
    "components": [
      {
        "id": "10000"
      }
    ],
    "customfield_10000": "09/Jun/19",
    "customfield_20000": "06/Jul/19 3:25 PM",
    "customfield_30000": [
      "10000",
      "10002"
    ],
    "customfield_40000": "Occurs on all orders",
    "customfield_50000": "Could impact day-to-day work.",
    "customfield_60000": "jira-software-users",
    "customfield_70000": [
      "jira-administrators",
      "jira-software-users"
    ],
    "customfield_80000": {
      "value": "red"
    },
    "description": "Order entry fails when selecting supplier.",
    "duedate": "2019-03-11",
    "environment": "UAT",
    "fixVersions": [
      {
        "id": "10001"
      }
    ],
    "issuetype": {
      "id": "10000"
    },
    "labels": [
      "bugfix",
      "blitz_test"
    ],
    "parent": {
      "key": "PROJ-123"
    },
    "priority": {
      "id": "20000"
    },
    "project": {
      "id": "10000"
    },
    "reporter": {
      "id": "5b10a2844c20165700ede21g"
    },
    "security": {
      "id": "10000"
    },
    "summary": "Main order flow broken",
    "timetracking": {
      "originalEstimate": "10",
      "remainingEstimate": "5"
    },
    "versions": [
      {
        "id": "10000"
      }
    ]
  },
  "update": {
    "worklog": [
      {
        "add": {
          "started": "2019-07-05T11:05:00.000+0000",
          "timeSpent": "60m"
        }
      }
    ]
  }
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
201Response
{
  "id": "10000",
  "key": "ED-24",
  "self": "https://your-domain.atlassian.net/rest/api/2/issue/10000",
  "transition": {
    "status": 200,
    "errorCollection": {
      "errorMessages": [],
      "errors": {}
    }
  }
}
PUT
Archive issue(s) by issue ID/keyExperimental

Enables admins to archive up to 1000 issues in a single request using issue ID/key, returning details of the issue(s) archived in the process and the errors encountered, if any.

Note that:

    you can't archive subtasks directly, only through their parent issues
    you can only archive issues from software, service management, and business projects

Permissions required: Jira admin or site admin: global permission

License required: Premium or Enterprise

Signed-in users only: This API can't be accessed anonymously.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira

Connect app scope required: WRITE
Request
Request bodyapplication/json

Contains a list of issue keys or IDs to be archived.
issueIdsOrKeys

array<string>
Responses

Returned if there is at least one valid issue to archive in the request. The return message will include the count of archived issues and subtasks, as well as error details for issues which failed to get archived.
application/json
IssueArchivalSyncResponse

Number of archived/unarchived issues and list of errors that occurred during the action, if any.
PUT/rest/api/2/issue/archive
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/archive"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "issueIdsOrKeys": [
    "PR-1",
    "1001",
    "PROJECT-2"
  ]
} )

response = requests.request(
   "PUT",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "errors": {
    "issueIsSubtask": {
      "count": 3,
      "issueIdsOrKeys": [
        "ST-1",
        "ST-2",
        "ST-3"
      ],
      "message": "Issue is subtask."
    },
    "issuesInArchivedProjects": {
      "count": 2,
      "issueIdsOrKeys": [
        "AR-1",
        "AR-2"
      ],
      "message": "Issue exists in archived project."
    },
    "issuesInUnlicensedProjects": {
      "count": 3,
      "issueIdsOrKeys": [
        "UL-1",
        "UL-2",
        "UL-3"
      ],
      "message": "Issues with these IDs are in unlicensed projects."
    },
    "issuesNotFound": {
      "count": 3,
      "issueIdsOrKeys": [
        "PR-1",
        "PR-2",
        "PR-3"
      ],
      "message": "Issue not found."
    }
  },
  "numberOfIssuesUpdated": 10
}
POST
Archive issue(s) by JQLExperimental

Enables admins to archive up to 100,000 issues in a single request using JQL, returning the URL to check the status of the submitted request.

You can use the get task and cancel task APIs to manage the request.

Note that:

    you can't archive subtasks directly, only through their parent issues
    you can only archive issues from software, service management, and business projects

Permissions required: Jira admin or site admin: global permission

License required: Premium or Enterprise

Signed-in users only: This API can't be accessed anonymously.

Rate limiting: Only a single request per jira instance can be active at any given time.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira

Connect app scope required: WRITE
Request
Request bodyapplication/json

A JQL query specifying the issues to archive. Note that subtasks can only be archived through their parent issues.
jql

string
Responses

Returns the URL to check the status of the submitted request.
application/json

string
POST/rest/api/2/issue/archive
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/archive"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "jql": "project = FOO AND updated < -2y"
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
202Response
"https://your-domain.atlassian.net/rest/api/2/task/1010"
POST
Bulk create issue

Creates upto 50 issues and, where the option to create subtasks is enabled in Jira, subtasks. Transitions may be applied, to move the issues or subtasks to a workflow step other than the default start step, and issue properties set.

The content of each issue or subtask is defined using update and fields. The fields that can be set in the issue or subtask are determined using the Get create issue metadata. These are the same fields that appear on the issues' create screens.

Creating a subtask differs from creating an issue as follows:

    issueType must be set to a subtask issue type (use Get create issue metadata to find subtask issue types).
    parent the must contain the ID or key of the parent issue.

Permissions required: Browse projects and Create issues project permissions for the project in which each issue or subtask is created.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira, write:comment:jira, write:comment.property:jira, write:attachment:jira, read:issue:jira

Connect app scope required: WRITE
Request
Request bodyapplication/json
issueUpdates

array<IssueUpdateDetails>
Additional Properties

any
Responses

Returned if any of the issue or subtask creation requests were successful. A request may be unsuccessful when it:

    is missing required fields.
    contains invalid field values.
    contains fields that cannot be set for the issue type.
    is by a user who does not have the necessary permission.
    is to create a subtype in a project different that of the parent issue.
    is for a subtask when the option to create subtasks is disabled.
    is invalid for any other reason.

application/json
CreatedIssues

Details about the issues created and the errors for requests that failed.
POST/rest/api/2/issue/bulk
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/bulk"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "issueUpdates": [
    {
      "fields": {
        "assignee": {
          "id": "5b109f2e9729b51b54dc274d"
        },
        "components": [
          {
            "id": "10000"
          }
        ],
        "customfield_10000": "09/Jun/19",
        "customfield_20000": "06/Jul/19 3:25 PM",
        "customfield_30000": [
          "10000",
          "10002"
        ],
        "customfield_40000": "Occurs on all orders",
        "customfield_50000": "Could impact day-to-day work.",
        "customfield_60000": "jira-software-users",
        "customfield_70000": [
          "jira-administrators",
          "jira-software-users"
        ],
        "customfield_80000": {
          "value": "red"
        },
        "description": "Order entry fails when selecting supplier.",
        "duedate": "2019-03-11",
        "environment": "UAT",
        "fixVersions": [
          {
            "id": "10001"
          }
        ],
        "issuetype": {
          "id": "10000"
        },
        "labels": [
          "bugfix",
          "blitz_test"
        ],
        "parent": {
          "key": "PROJ-123"
        },
        "priority": {
          "id": "20000"
        },
        "project": {
          "id": "10000"
        },
        "reporter": {
          "id": "5b10a2844c20165700ede21g"
        },
        "security": {
          "id": "10000"
        },
        "summary": "Main order flow broken",
        "timetracking": {
          "originalEstimate": "10",
          "remainingEstimate": "5"
        },
        "versions": [
          {
            "id": "10000"
          }
        ]
      },
      "update": {
        "worklog": [
          {
            "add": {
              "started": "2019-07-05T11:05:00.000+0000",
              "timeSpent": "60m"
            }
          }
        ]
      }
    },
    {
      "fields": {
        "assignee": {
          "id": "5b109f2e9729b51b54dc274d"
        },
        "components": [
          {
            "id": "10000"
          }
        ],
        "customfield_10000": "09/Jun/19",
        "customfield_20000": "06/Jul/19 3:25 PM",
        "customfield_30000": [
          "10000",
          "10002"
        ],
        "customfield_40000": "Occurs on all orders",
        "customfield_50000": "Could impact day-to-day work.",
        "customfield_60000": "jira-software-users",
        "customfield_70000": [
          "jira-administrators",
          "jira-software-users"
        ],
        "customfield_80000": {
          "value": "red"
        },
        "description": "Order remains pending after approved.",
        "duedate": "2019-04-16",
        "environment": "UAT",
        "fixVersions": [
          {
            "id": "10001"
          }
        ],
        "issuetype": {
          "id": "10000"
        },
        "labels": [
          "new_release"
        ],
        "parent": {
          "id": "10034"
        },
        "priority": {
          "id": "20000"
        },
        "project": {
          "id": "1000"
        },
        "reporter": {
          "id": "5b10a2844c20165700ede21g"
        },
        "security": {
          "id": "10000"
        },
        "summary": "Order stuck in pending",
        "timetracking": {
          "originalEstimate": "15",
          "remainingEstimate": "5"
        },
        "versions": [
          {
            "id": "10000"
          }
        ]
      },
      "update": {}
    }
  ]
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
201Response
{
  "issues": [
    {
      "id": "10000",
      "key": "ED-24",
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/10000",
      "transition": {
        "status": 200,
        "errorCollection": {
          "errorMessages": [],
          "errors": {}
        }
      }
    },
    {
      "id": "10001",
      "key": "ED-25",
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/10001"
    }
  ],
  "errors": []
}
POST
Bulk fetch issues

Returns the details for a set of requested issues. You can request up to 100 issues.

Each issue is identified by its ID or key, however, if the identifier doesn't match an issue, a case-insensitive search and check for moved issues is performed. If a matching issue is found its details are returned, a 302 or other redirect is not returned.

Issues will be returned in ascending id order. If there are errors, Jira will return a list of issues which couldn't be fetched along with error messages.

This operation can be accessed anonymously.

Permissions required: Issues are included in the response where the user has:

    Browse projects project permission for the project that the issue is in.
    If issue-level security is configured, issue-level security permission to view the issue.

Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:issue-security-level:jira, read:issue.vote:jira, read:issue.changelog:jira, read:avatar:jira ...(Show more)

Connect app scope required: WRITE
Request
Request bodyapplication/json

A JSON object containing the information about which issues and fields to fetch.
expand

array<string>
fields

array<string>
fieldsByKeys

boolean
issueIdsOrKeys

array<string>
Required
properties

array<string>
Responses

Returned if the request is successful. A response may contain both successful issues and issue errors.
application/json
BulkIssueResults

The list of requested issues & fields.
POST/rest/api/2/issue/bulkfetch
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/bulkfetch"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "expand": [
    "names"
  ],
  "fields": [
    "summary",
    "project",
    "assignee"
  ],
  "fieldsByKeys": false,
  "issueIdsOrKeys": [
    "EX-1",
    "EX-2",
    "10005"
  ],
  "properties": []
} )

response = requests.request(
   "POST",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "expand": "schema,names",
  "issueErrors": [],
  "issues": [
    {
      "expand": "",
      "fields": {
        "summary": "My first example issue",
        "project": {
          "avatarUrls": {
            "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000",
            "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000",
            "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000",
            "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000"
          },
          "id": "10000",
          "insight": {
            "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000",
            "totalIssueCount": 100
          },
          "key": "EX",
          "name": "Example",
          "projectCategory": {
            "description": "First Project Category",
            "id": "10000",
            "name": "FIRST",
            "self": "https://your-domain.atlassian.net/rest/api/2/projectCategory/10000"
          },
          "self": "https://your-domain.atlassian.net/rest/api/2/project/EX",
          "simplified": false,
          "style": "classic"
        },
        "assignee": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": true,
          "avatarUrls": {
            "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
            "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
            "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
            "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
          },
          "displayName": "Mia Krystof",
          "emailAddress": "mia@example.com",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g",
          "timeZone": "Australia/Sydney"
        }
      },
      "id": "10002",
      "key": "EX-1",
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/10002"
    },
    {
      "expand": "",
      "fields": {
        "summary": "My second example issue",
        "project": {
          "avatarUrls": {
            "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10001",
            "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10001",
            "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10001",
            "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10001"
          },
          "id": "10001",
          "insight": {
            "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000",
            "totalIssueCount": 100
          },
          "key": "ABC",
          "name": "Alphabetical",
          "projectCategory": {
            "description": "First Project Category",
            "id": "10000",
            "name": "FIRST",
            "self": "https://your-domain.atlassian.net/rest/api/2/projectCategory/10000"
          },
          "self": "https://your-domain.atlassian.net/rest/api/2/project/ABC",
          "simplified": false,
          "style": "classic"
        },
        "assignee": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": true,
          "avatarUrls": {
            "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
            "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
            "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
            "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
          },
          "displayName": "Mia Krystof",
          "emailAddress": "mia@example.com",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g",
          "timeZone": "Australia/Sydney"
        }
      },
      "id": "10005",
      "key": "EX-2",
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/10003"
    },
    {
      "expand": "",
      "fields": {
        "summary": "My fourth example issue",
        "project": {
          "avatarUrls": {
            "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10002",
            "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10002",
            "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10002",
            "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10002"
          },
          "deleted": true,
          "deletedBy": {
            "accountId": "5b10a2844c20165700ede21g",
            "accountType": "atlassian",
            "active": false,
            "avatarUrls": {
              "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
              "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
              "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
              "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
            },
            "displayName": "Mia Krystof",
            "key": "",
            "name": "",
            "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
          },
          "deletedDate": "2022-11-11T13:35:29.000+0000",
          "id": "10002",
          "insight": {
            "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000",
            "totalIssueCount": 100
          },
          "key": "MKY",
          "name": "Example",
          "projectCategory": {
            "description": "First Project Category",
            "id": "10000",
            "name": "FIRST",
            "self": "https://your-domain.atlassian.net/rest/api/2/projectCategory/10000"
          },
          "retentionTillDate": "2023-01-10T13:35:29.000+0000",
          "self": "https://your-domain.atlassian.net/rest/api/2/project/MKY",
          "simplified": false,
          "style": "classic"
        },
        "assignee": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": true,
          "avatarUrls": {
            "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
            "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
            "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
            "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
          },
          "displayName": "Mia Krystof",
          "emailAddress": "mia@example.com",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g",
          "timeZone": "Australia/Sydney"
        }
      },
      "id": "10005",
      "key": "EX-4",
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/10005"
    }
  ]
}
GET
Get create issue metadataDeprecated

Returns details of projects, issue types within projects, and, when requested, the create screen fields for each issue type for the user. Use the information to populate the requests in Create issue and Create issues.

Deprecated, see Create Issue Meta Endpoint Deprecation Notice.

The request can be restricted to specific projects or issue types using the query parameters. The response will contain information for the valid projects, issue types, or project and issue type combinations requested. Note that invalid project, issue type, or project and issue type combinations do not generate errors.

This operation can be accessed anonymously.

Permissions required: Create issues project permission in the requested projects.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:avatar:jira, read:field-configuration:jira

Connect app scope required: READ
Request
Query parameters
projectIds

array<string>
projectKeys

array<string>
issuetypeIds

array<string>
issuetypeNames

array<string>
expand

string
Responses

Returned if the request is successful.
application/json
IssueCreateMetadata

The wrapper for the issue creation metadata for a list of projects.
GET/rest/api/2/issue/createmeta
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/createmeta"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "projects": [
    {
      "avatarUrls": {
        "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000&avatarId=10011",
        "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000&avatarId=10011",
        "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000&avatarId=10011",
        "48x48": "https://your-domain.atlassian.net/secure/projectavatar?pid=10000&avatarId=10011"
      },
      "id": "10000",
      "issuetypes": [
        {
          "description": "An error in the code",
          "fields": {
            "issuetype": {
              "allowedValues": [
                "set"
              ],
              "autoCompleteUrl": "issuetype",
              "hasDefaultValue": false,
              "key": "issuetype",
              "name": "Issue Type",
              "required": true
            }
          },
          "iconUrl": "https://your-domain.atlassian.net/images/icons/issuetypes/bug.png",
          "id": "1",
          "name": "Bug",
          "self": "https://your-domain.atlassian.net/rest/api/2/issueType/1",
          "subtask": false
        }
      ],
      "key": "ED",
      "name": "Edison Project",
      "self": "https://your-domain.atlassian.net/rest/api/2/project/ED"
    }
  ]
}
GET
Get create metadata issue types for a project

Returns a page of issue type metadata for a specified project. Use the information to populate the requests in Create issue and Create issues.

This operation can be accessed anonymously.

Permissions required: Create issues project permission in the requested projects.
Data Security Policy: Exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:avatar:jira, read:field-configuration:jira

Connect app scope required: READ
Request
Path parameters
projectIdOrKey

string
Required
Query parameters
startAt

integer
maxResults

integer
Responses

Returned if the request is successful.
application/json
PageOfCreateMetaIssueTypes

A page of CreateMetaIssueTypes.
GET/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "issueTypes": [
    {
      "description": "An error in the code",
      "iconUrl": "https://your-domain.atlassian.net/images/icons/issuetypes/bug.png",
      "id": "1",
      "name": "Bug",
      "self": "https://your-domain.atlassian.net/rest/api/2/issueType/1",
      "subtask": false
    }
  ],
  "maxResults": 1,
  "startAt": 0,
  "total": 1
}
GET
Get create field metadata for a project and issue type id

Returns a page of field metadata for a specified project and issuetype id. Use the information to populate the requests in Create issue and Create issues.

This operation can be accessed anonymously.

Permissions required: Create issues project permission in the requested projects.
Data Security Policy: Exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:avatar:jira, read:field-configuration:jira

Connect app scope required: READ
Request
Path parameters
projectIdOrKey

string
Required
issueTypeId

string
Required
Query parameters
startAt

integer
maxResults

integer
Responses

Returned if the request is successful.
application/json
PageOfCreateMetaIssueTypeWithField

A page of CreateMetaIssueType with Field.
GET/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "fields": [
    {
      "fieldId": "assignee",
      "hasDefaultValue": false,
      "key": "assignee",
      "name": "Assignee",
      "operations": [
        "set"
      ],
      "required": true
    }
  ],
  "maxResults": 1,
  "startAt": 0,
  "total": 1
}
GET
Get issue limit reportExperimental

Returns all issues breaching and approaching per-issue limits.

Permissions required:

    Browse projects project permission is required for the project the issues are in. Results may be incomplete otherwise
    Administer Jira global permission.

Data Security Policy
: Exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:project:jira, read:issue:jira

Connect app scope required
: READ
Request
Query parameters
isReturningKeys

boolean
Responses

Returned if the request is successful.
application/json
IssueLimitReportResponseBean
GET/rest/api/2/issue/limit/report
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/limit/report"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

query = {
  'isReturningKeys': '{isReturningKeys}'
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   params=query,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "issuesApproachingLimit": {
    "attachment": {
      "15070L": 1822,
      "15111L": 1999
    },
    "comment": {
      "10000L": 4997,
      "15073L": 4999,
      "15110L": 5000
    },
    "remoteIssueLinks": {
      "15107L": 2000
    },
    "worklog": {
      "15101L": 10342
    }
  },
  "issuesBreachingLimit": {
    "attachment": {
      "15057L": 2005,
      "15116L": 2065,
      "15117L": 3005
    },
    "comment": {
      "15055L": 5202
    },
    "issuelinks": {
      "15058L": 2120
    },
    "remoteIssueLinks": {
      "15059L": 2094
    },
    "worklog": {
      "15056L": 10085,
      "15169L": 120864
    }
  },
  "limits": {
    "attachment": 2000,
    "comment": 5000,
    "issuelinks": 2000,
    "remoteIssueLinks": 2000,
    "worklog": 10000
  }
}
PUT
Unarchive issue(s) by issue keys/IDExperimental

Enables admins to unarchive up to 1000 issues in a single request using issue ID/key, returning details of the issue(s) unarchived in the process and the errors encountered, if any.

Note that:

    you can't unarchive subtasks directly, only through their parent issues
    you can only unarchive issues from software, service management, and business projects

Permissions required: Jira admin or site admin: global permission

License required: Premium or Enterprise

Signed-in users only: This API can't be accessed anonymously.
Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira

Connect app scope required: WRITE
Request
Request bodyapplication/json

Contains a list of issue keys or IDs to be unarchived.
issueIdsOrKeys

array<string>
Responses

Returned if there is at least one valid issue to unarchive in the request. It will return the count of unarchived issues, which also includes the count of the subtasks unarchived, and it will show the detailed errors for those issues which are not unarchived.
application/json
IssueArchivalSyncResponse

Number of archived/unarchived issues and list of errors that occurred during the action, if any.
PUT/rest/api/2/issue/unarchive
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/unarchive"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "issueIdsOrKeys": [
    "PR-1",
    "1001",
    "PROJECT-2"
  ]
} )

response = requests.request(
   "PUT",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "errors": {
    "issueIsSubtask": {
      "count": 3,
      "issueIdsOrKeys": [
        "ST-1",
        "ST-2",
        "ST-3"
      ],
      "message": "Issue is subtask."
    },
    "issuesInArchivedProjects": {
      "count": 2,
      "issueIdsOrKeys": [
        "AR-1",
        "AR-2"
      ],
      "message": "Issue exists in archived project."
    },
    "issuesNotFound": {
      "count": 3,
      "issueIdsOrKeys": [
        "PR-1",
        "PR-2",
        "PR-3"
      ],
      "message": "Issue not found."
    }
  },
  "numberOfIssuesUpdated": 10
}
GET
Get issue

Returns the details for an issue.

The issue is identified by its ID or key, however, if the identifier doesn't match an issue, a case-insensitive search and check for moved issues is performed. If a matching issue is found its details are returned, a 302 or other redirect is not returned. The issue key returned in the response is the key of the issue found.

This operation can be accessed anonymously.

Permissions required:

    Browse projects project permission for the project that the issue is in.
    If issue-level security is configured, issue-level security permission to view the issue.

Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:read:jira-work
Granular:read:issue-meta:jira, read:issue-security-level:jira, read:issue.vote:jira, read:issue.changelog:jira, read:avatar:jira ...(Show more)

Connect app scope required: READ
Request
Path parameters
issueIdOrKey

string
Required
Query parameters
fields

array<string>
fieldsByKeys

boolean
expand

string
properties

array<string>
updateHistory

boolean
failFast

boolean
Responses

Returned if the request is successful.
application/json
IssueBean

Details about an issue.
GET/rest/api/2/issue/{issueIdOrKey}
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/{issueIdOrKey}"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json"
}

response = requests.request(
   "GET",
   url,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
200Response
{
  "fields": {
    "watcher": {
      "isWatching": false,
      "self": "https://your-domain.atlassian.net/rest/api/2/issue/EX-1/watchers",
      "watchCount": 1
    },
    "attachment": [
      {
        "author": {
          "accountId": "5b10a2844c20165700ede21g",
          "accountType": "atlassian",
          "active": false,
          "avatarUrls": {
            "16x16": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=16&s=16",
            "24x24": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=24&s=24",
            "32x32": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=32&s=32",
            "48x48": "https://avatar-management--avatars.server-location.prod.public.atl-paas.net/initials/MK-5.png?size=48&s=48"
          },
          "displayName": "Mia Krystof",
          "key": "",
          "name": "",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
        },
        "content": "https://your-domain.atlassian.net/jira/rest/api/3/attachment/content/10001",
        "created": "2023-06-24T19:24:50.000+0000",
        "filename": "debuglog.txt",
        "id": 10001,
        "mimeType": "text/plain",
        "self": "https://your-domain.atlassian.net/rest/api/2/attachments/10001",
        "size": 2460
      }
    ],
    "sub-tasks": [
      {
        "id": "10000",
        "outwardIssue": {
          "fields": {
            "status": {
              "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png",
              "name": "Open"
            }
          },
          "id": "10003",
          "key": "ED-2",
          "self": "https://your-domain.atlassian.net/rest/api/2/issue/ED-2"
        },
        "type": {
          "id": "10000",
          "inward": "Parent",
          "name": "",
          "outward": "Sub-task"
        }
      }
    ],
    "description": "Main order flow broken",
    "project": {
      "avatarUrls": {
        "16x16": "https://your-domain.atlassian.net/secure/projectavatar?size=xsmall&pid=10000",
        "24x24": "https://your-domain.atlassian.net/secure/projectavatar?size=small&pid=10000",
        "32x32": "https://your-domain.atlassian.net/secure/projectavatar?size=medium&pid=10000",
        "48x48": "https://your-domain.atlassian.net/secure/projectavatar?size=large&pid=10000"
      },
      "id": "10000",
      "insight": {
        "lastIssueUpdateTime": "2021-04-22T05:37:05.000+0000",
        "totalIssueCount": 100
      },
      "key": "EX",
      "name": "Example",
      "projectCategory": {
        "description": "First Project Category",
        "id": "10000",
        "name": "FIRST",
        "self": "https://your-domain.atlassian.net/rest/api/2/projectCategory/10000"
      },
      "self": "https://your-domain.atlassian.net/rest/api/2/project/EX",
      "simplified": false,
      "style": "classic"
    },
    "comment": [
      {
        "author": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": false,
          "displayName": "Mia Krystof",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
        },
        "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque eget venenatis elit. Duis eu justo eget augue iaculis fermentum. Sed semper quam laoreet nisi egestas at posuere augue semper.",
        "created": "2021-01-17T12:34:00.000+0000",
        "id": "10000",
        "self": "https://your-domain.atlassian.net/rest/api/2/issue/10010/comment/10000",
        "updateAuthor": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": false,
          "displayName": "Mia Krystof",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
        },
        "updated": "2021-01-18T23:45:00.000+0000",
        "visibility": {
          "identifier": "Administrators",
          "type": "role",
          "value": "Administrators"
        }
      }
    ],
    "issuelinks": [
      {
        "id": "10001",
        "outwardIssue": {
          "fields": {
            "status": {
              "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png",
              "name": "Open"
            }
          },
          "id": "10004L",
          "key": "PR-2",
          "self": "https://your-domain.atlassian.net/rest/api/2/issue/PR-2"
        },
        "type": {
          "id": "10000",
          "inward": "depends on",
          "name": "Dependent",
          "outward": "is depended by"
        }
      },
      {
        "id": "10002",
        "inwardIssue": {
          "fields": {
            "status": {
              "iconUrl": "https://your-domain.atlassian.net/images/icons/statuses/open.png",
              "name": "Open"
            }
          },
          "id": "10004",
          "key": "PR-3",
          "self": "https://your-domain.atlassian.net/rest/api/2/issue/PR-3"
        },
        "type": {
          "id": "10000",
          "inward": "depends on",
          "name": "Dependent",
          "outward": "is depended by"
        }
      }
    ],
    "worklog": [
      {
        "author": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": false,
          "displayName": "Mia Krystof",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
        },
        "comment": "I did some work here.",
        "id": "100028",
        "issueId": "10002",
        "self": "https://your-domain.atlassian.net/rest/api/2/issue/10010/worklog/10000",
        "started": "2021-01-17T12:34:00.000+0000",
        "timeSpent": "3h 20m",
        "timeSpentSeconds": 12000,
        "updateAuthor": {
          "accountId": "5b10a2844c20165700ede21g",
          "active": false,
          "displayName": "Mia Krystof",
          "self": "https://your-domain.atlassian.net/rest/api/2/user?accountId=5b10a2844c20165700ede21g"
        },
        "updated": "2021-01-18T23:45:00.000+0000",
        "visibility": {
          "identifier": "276f955c-63d7-42c8-9520-92d01dca0625",
          "type": "group",
          "value": "jira-developers"
        }
      }
    ],
    "updated": 1,
    "timetracking": {
      "originalEstimate": "10m",
      "originalEstimateSeconds": 600,
      "remainingEstimate": "3m",
      "remainingEstimateSeconds": 200,
      "timeSpent": "6m",
      "timeSpentSeconds": 400
    }
  },
  "id": "10002",
  "key": "ED-1",
  "self": "https://your-domain.atlassian.net/rest/api/2/issue/10002"
}
PUT
Edit issue

Edits an issue. Issue properties may be updated as part of the edit. Please note that issue transition is not supported and is ignored here. To transition an issue, please use Transition issue.

The edits to the issue's fields are defined using update and fields. The fields that can be edited are determined using Get edit issue metadata.

The parent field may be set by key or ID. For standard issue types, the parent may be removed by setting update.parent.set.none to true.

Connect apps having an app user with Administer Jira global permission, and Forge apps acting on behalf of users with Administer Jira global permission, can override the screen security configuration using overrideScreenSecurity and overrideEditableFlag.

This operation can be accessed anonymously.

Permissions required:

    Browse projects and Edit issues project permission for the project that the issue is in.
    If issue-level security is configured, issue-level security permission to view the issue.

Data Security Policy: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira

Connect app scope required: WRITE
Request
Path parameters
issueIdOrKey

string
Required
Query parameters
notifyUsers

boolean
overrideScreenSecurity

boolean
overrideEditableFlag

boolean
returnIssue

boolean
expand

string
Request bodyapplication/json
fields

object
historyMetadata

HistoryMetadata
properties

array<EntityProperty>
transition

IssueTransition
update

object
Additional Properties

any
Responses

Returned if the request is successful and the returnIssue parameter is true
application/json

any
PUT/rest/api/2/issue/{issueIdOrKey}
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth
import json

url = "https://your-domain.atlassian.net/rest/api/2/issue/{issueIdOrKey}"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

payload = json.dumps( {
  "fields": {
    "customfield_10000": "Investigation underway",
    "customfield_10010": 1,
    "summary": "Completed orders still displaying in pending"
  },
  "historyMetadata": {
    "activityDescription": "Complete order processing",
    "actor": {
      "avatarUrl": "http://mysystem/avatar/tony.jpg",
      "displayName": "Tony",
      "id": "tony",
      "type": "mysystem-user",
      "url": "http://mysystem/users/tony"
    },
    "cause": {
      "id": "myevent",
      "type": "mysystem-event"
    },
    "description": "From the order testing process",
    "extraData": {
      "Iteration": "10a",
      "Step": "4"
    },
    "generator": {
      "id": "mysystem-1",
      "type": "mysystem-application"
    },
    "type": "myplugin:type"
  },
  "properties": [
    {
      "key": "key1",
      "value": "Order number 10784"
    },
    {
      "key": "key2",
      "value": "Order number 10923"
    }
  ],
  "update": {
    "components": [
      {
        "set": ""
      }
    ],
    "labels": [
      {
        "add": "triaged"
      },
      {
        "remove": "blocker"
      }
    ],
    "summary": [
      {
        "set": "Bug in business logic"
      }
    ],
    "timetracking": [
      {
        "edit": {
          "originalEstimate": "1w 1d",
          "remainingEstimate": "4d"
        }
      }
    ]
  }
} )

response = requests.request(
   "PUT",
   url,
   data=payload,
   headers=headers,
   auth=auth
)

print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
DEL
Delete issue

Deletes an issue.

An issue cannot be deleted if it has one or more subtasks. To delete an issue with subtasks, set deleteSubtasks. This causes the issue's subtasks to be deleted with the issue.

This operation can be accessed anonymously.

Permissions required:

    Browse projects and Delete issues project permission for the project containing the issue.
    If issue-level security is configured, issue-level security permission to view the issue.

Data Security Policy
: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:delete:issue:jira

Connect app scope required
: DELETE
Request
Path parameters
issueIdOrKey

string
Required
Query parameters
deleteSubtasks

string
Responses

Returned if the request is successful.
DEL/rest/api/2/issue/{issueIdOrKey}
Forge
curl
Node.js
Java
Python
PHP
# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
from requests.auth import HTTPBasicAuth

url = "https://your-domain.atlassian.net/rest/api/2/issue/{issueIdOrKey}"

auth = HTTPBasicAuth("email@example.com", "<api_token>")

response = requests.request(
   "DELETE",
   url,
   auth=auth
)

print(response.text)
PUT
Assign issue

Assigns an issue to a user. Use this operation when the calling user does not have the Edit Issues permission but has the Assign issue permission for the project that the issue is in.

If name or accountId is set to:

    "-1", the issue is assigned to the default assignee for the project.
    null, the issue is set to unassigned.

This operation can be accessed anonymously.

Permissions required:

    Browse Projects and Assign Issues project permission for the project that the issue is in.
    If issue-level security is configured, issue-level security permission to view the issue.

Data Security Policy
: Not exempt from app access rules
Scopes
OAuth 2.0 scopes required:
ClassicRECOMMENDED:write:jira-work
Granular:write:issue:jira

Connect app scope required
: WRITE