---
name: fix-pr-comments
description: "Use when fixing code based on GitHub PR review comments."
---

# Fix PR Review Comments

## Keywords
fix pr comments, fix review, fix comment, resolve review, address feedback, pr feedback, code review fix, github review

## Overview

Fetch PR review comments from GitHub, understand the feedback, fix the code accordingly, then commit and push the changes. Follows the project's commit format convention.

## When to Use

- User says "fix pr comments", "fix review comments", "address pr feedback"
- User provides a PR URL or number and wants to resolve review feedback
- User wants to batch-fix all outstanding review comments on a PR

## Workflow

### Step 1: Identify PR and Repository Info

Extract PR number from user input. Detect repo and hostname from git remote:

```bash
# Get remote URL to extract owner/repo
git remote get-url origin

# Get GitHub Enterprise hostname from remote URL
# e.g., github.com -> use as --hostname value
```

### Step 2: Fetch PR Review Comments

Use `gh api` to fetch review comments:

```bash
gh api -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --hostname {github-hostname} 2>&1 | head -200
```

Also fetch PR review (top-level review comments):

```bash
gh api -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --hostname {github-hostname} 2>&1 | head -200
```

### Step 3: Parse Comments

Extract key fields from each comment using `python3 -c` or `jq`:

- `body` - Comment content (the actual feedback)
- `path` - File path the comment is on
- `line` / `original_line` - Line number
- `diff_hunk` - Code context around the comment
- `user.login` - Reviewer name
- `created_at` - When posted

### Step 4: Display Comments Summary

Present all comments in a clear format before fixing:

```
## PR #123 Review Comments

### Comment 1 - @reviewer (file.ts:42)
> Use `unknown` instead of `any` here

### Comment 2 - @reviewer (utils.ts:15)
> This should use dayjs().utc() instead of dayjs.utc()
```

### Step 5: Fix Code

For each comment:
1. Read the file mentioned in `path`
2. Navigate to the line referenced in `line`
3. Understand the reviewer's feedback from `body`
4. Apply the fix using the Edit tool
5. Follow all project conventions from CLAUDE.md (e.g., `unknown` instead of `any`, `dayjs().utc()`)

### Step 6: Commit and Push

After all fixes are applied:

1. Stage changed files:
```bash
git add <modified-files>
```

2. Commit with the project's format convention:
```bash
git commit -m "JIRA_TICKET: address pr review comments"
```

**IMPORTANT:**
- Extract the JIRA TICKET number from the branch name (format: `user/jiamyu/JIRA_TICKET description`)
- Commit message must be in English
- Format: `JIRA_TICKET: brief description`
- Do NOT include co-author in the commit message

3. Push:
```bash
git push
```

## Quick Reference

| Action | Command |
|--------|---------|
| Get PR comments | `gh api /repos/{owner}/{repo}/pulls/{n}/comments --hostname {host}` |
| Get PR reviews | `gh api /repos/{owner}/{repo}/pulls/{n}/reviews --hostname {host}` |
| Get branch ticket | `git branch --show-current \| grep -oP 'JIRA_TICKET |
| Push after fix | `git push` |

## Common Mistakes

- **Using WebFetch for GitHub**: Internal GitHub Enterprise cannot be accessed via WebFetch. Always use `gh api`.
- **Wrong commit format**: Must be `JIRA_TICKET: description` in English, no co-author.
- **Missing --hostname**: For GitHub Enterprise, always include `--hostname` flag with `gh api`.
- **Fixing without showing**: Always display the comments summary to the user first before making changes.
