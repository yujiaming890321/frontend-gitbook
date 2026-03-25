---
name: jira-issue-get
description: "Fetch a Jira issue by key from JIRA_URL."
---

# Get Jira Issue

## Keywords
get jira, fetch issue, view ticket, look up jira, jira details, issue details, ticket info, jira issue

## Overview

Fetch and display a Jira issue from Tesla's internal Jira instance (`JIRA_URL`) using the REST API with Bearer token authentication.

## When to Use

- User provides a Jira issue key like `JIRA_TICKET`
- User asks to "get", "fetch", "view", "look up", or "show" a Jira issue
- User wants to understand a ticket's details, status, or description

## Workflow

### Step 1: Extract Issue Key

Identify the Jira issue key from user input. Format: `PROJECT-NUMBER` (e.g., `CN-12345`).

### Step 2: Fetch Issue via REST API

Use `curl` to call the Jira REST API:

```bash
curl -s -H "Authorization: Bearer JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  "https://JIRA_URL/rest/api/2/issue/ISSUE-KEY?expand=renderedFields"
```

### Step 3: Parse and Display

Extract and display key fields from the JSON response using `python3 -c` or `jq`:

**Key fields to extract:**
- `fields.summary` - Issue title
- `fields.status.name` - Current status
- `fields.assignee.displayName` - Assignee
- `fields.reporter.displayName` - Reporter
- `fields.priority.name` - Priority
- `fields.issuetype.name` - Issue type
- `fields.created` - Created date
- `fields.updated` - Last updated
- `fields.description` - Description (may be long, truncate if needed)
- `fields.labels` - Labels
- `fields.components` - Components
- `fields.fixVersions` - Fix versions
- `fields.comment.comments` - Comments (show last 5)

### Step 4: Format Output

Present the issue in a clean, readable format:

```
## ISSUE-KEY: Summary

| Field       | Value           |
|-------------|-----------------|
| Status      | In Progress     |
| Type        | Bug             |
| Priority    | High            |
| Assignee    | John Doe        |
| Reporter    | Jane Smith      |
| Created     | 2026-03-01      |
| Updated     | 2026-03-15      |
| Labels      | mobile, ios     |
| Components  | Phone Key       |

### Description
[Truncated description content]

### Recent Comments (last 3)
**Author** - 2026-03-14:
Comment text...
```

## Quick Reference

| Action | Command |
|--------|---------|
| Get issue | `curl -s -H "Authorization: Bearer TOKEN" "https://JIRA_URL/rest/api/2/issue/KEY"` |
| With rendered fields | Add `?expand=renderedFields` |
| Get comments only | `.../issue/KEY/comment` |
| Get transitions | `.../issue/KEY/transitions` |

## Common Mistakes

- **Using WebFetch**: `JIRA_URL` is internal and cannot be accessed via WebFetch. Always use `curl`.
- **Missing auth header**: Always include the Bearer token in the Authorization header.
- **Large responses**: Jira responses can be large. Use `python3 -c` to parse JSON and extract only needed fields.
