---
mode: ask
tools: [git]
description: Generate a clear, conventional commit message based on the changes in the current branch or staged files.
---

# Commit Message Generator

Your goal is to generate a **concise, meaningful, and conventional commit message**.

## Rules:
- Use **Conventional Commits style**: `type(scope): short description`
  - Types: feat, fix, docs, style, refactor, test, chore
- Scope is optional but should describe the area of the project affected
- Include a longer description in the body if necessary
- Reference related Issues or PRs if available (`#123`)
- Always use **present tense**: e.g., "Add feature" not "Added feature"
- Output **only the commit message** in Markdown code block

## Example

```text
feat(api): add user authentication endpoint

- Implement JWT-based login
- Validate email and password
- Update documentation
- Closes #42
```
