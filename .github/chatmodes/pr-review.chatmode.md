---
mode: 'agent'
tools: ['githubRepo', 'codebase', 'documentation']
description: 'Generate a clear Pull Request title and description, summarize changes, and suggest reviewers.'
---

# Pull Request Generator

Your goal is to create a **PR title and description** based on branch changes, issues, and code modifications.

## Rules:
- PR title should be **concise and descriptive**, following the same style as commit messages
- PR body should include:
  - Summary of changes
  - Related issues (`Closes #123`)
  - Key implementation notes or special instructions
- Suggest reviewers if possible
- Include checklist if needed:
  - [ ] Tests added
  - [ ] Documentation updated
  - [ ] Lint passed
- Output **only in Markdown**

## Example

```md
# Title
feat(api): add user authentication endpoint

# Description
This PR implements a JWT-based login system for users. Email and password validation is included.
- Updates API routes
- Adds documentation for auth endpoints
- Adds unit tests

Closes #42

# Checklist
- [x] Tests added
- [x] Documentation updated
- [x] Lint passed
```
