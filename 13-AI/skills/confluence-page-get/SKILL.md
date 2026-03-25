---
name: confluence-page-get
description: "Fetch a Confluence page by ID or URL from CONFLUENCE_URL."
---

# Get Confluence Page

## Keywords
confluence, wiki, page, fetch page, view page, search confluence, confluence search, CQL

## Overview

Fetch and display Confluence pages from Tesla's internal Confluence instance (`CONFLUENCE_URL`) using the REST API with Bearer token authentication.

## When to Use

- User provides a Confluence page URL like `https://CONFLUENCE_URL/display/SPACE/Page+Title` or `https://CONFLUENCE_URL/pages/viewpage.action?pageId=123456`
- User provides a Confluence page ID
- User asks to "get", "fetch", "view", "read", or "show" a Confluence page
- User asks to search Confluence for a topic

## Workflow

### Fetch Page by ID

```bash
curl -s -H "Authorization: Bearer CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  "https://CONFLUENCE_URL/rest/api/content/PAGE_ID?expand=body.storage,version,space,ancestors"
```

### Fetch Page by Space Key and Title

```bash
curl -s -H "Authorization: Bearer CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  "https://CONFLUENCE_URL/rest/api/content?spaceKey=SPACE&title=Page+Title&expand=body.storage,version"
```

### Search Pages via CQL

```bash
curl -s -H "Authorization: Bearer CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  "https://CONFLUENCE_URL/rest/api/content/search?cql=text~\"keyword\"&limit=10&expand=space,version"
```

### Extract Page ID from URL

- URL format `pages/viewpage.action?pageId=123456` -> page ID is `123456`
- URL format `display/SPACE/Page+Title` -> use space key + title to fetch

### Parse and Display

Extract key fields from the JSON response using `python3 -c` or `jq`:

**Key fields:**
- `title` - Page title
- `space.key` / `space.name` - Space info
- `version.number` - Version
- `version.when` - Last modified date
- `version.by.displayName` - Last modifier
- `body.storage.value` - Page content (HTML, convert to readable text)
- `ancestors` - Parent pages (breadcrumb)

### Format Output

```
## Page Title

| Field        | Value              |
|--------------|--------------------|
| Space        | SPACE (Space Name) |
| Version      | 12                 |
| Last Updated | 2026-03-15         |
| Updated By   | John Doe           |
| Parent       | Parent Page Title  |

### Content
[Converted page content - strip HTML tags for readability]
```

For search results:

```
## Confluence Search Results: "keyword"

| # | Title | Space | Updated |
|---|-------|-------|---------|
| 1 | Page Title | SPACE | 2026-03-15 |
| 2 | Another Page | PROJ | 2026-03-14 |
```

## Quick Reference

| Action | Endpoint |
|--------|----------|
| Get page by ID | `/rest/api/content/{id}?expand=body.storage,version,space` |
| Get page by space+title | `/rest/api/content?spaceKey=X&title=Y&expand=body.storage` |
| Search (CQL) | `/rest/api/content/search?cql=text~"keyword"&limit=10` |
| Search in space | `cql=space=SPACE AND text~"keyword"` |
| Get child pages | `/rest/api/content/{id}/child/page` |
| Get page comments | `/rest/api/content/{id}/child/comment?expand=body.storage` |
| Get attachments | `/rest/api/content/{id}/child/attachment` |

## Common Mistakes

- **Using WebFetch**: `CONFLUENCE_URL` is internal and cannot be accessed via WebFetch. Always use `curl`.
- **Missing auth header**: Always include the Bearer token in the Authorization header.
- **HTML content**: `body.storage.value` returns HTML. Use `python3` with html or BeautifulSoup to strip tags for readable output.
- **URL encoding**: Page titles in URLs use `+` for spaces. Use proper URL encoding when searching by title.
- **Large pages**: Page content can be very large. Truncate if needed and show a summary.
