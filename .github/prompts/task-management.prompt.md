---
mode: ask
tools: [github]
description: Manage project tasks using GitHub Issues if accessible, or fallback to Markdown checklists.
---

# Task Management Prompt

1. Check if the GitHub repository and Issues are accessible:
   - If accessible:
     - Look for the relevant Issue.
     - If the Issue exists, summarize its current status and progress.
     - If the Issue does not exist, create a new Issue with the planned task and register it.
   - If Issues cannot be accessed at all, create a Markdown task list as a fallback.

2. Organize tasks according to project milestones or long-term plans.

3. Provide clear task descriptions, labels, and assignees if applicable.

4. Suggest the next actionable task based on priority and dependencies.

5. Output tasks in Markdown format with checkboxes:
   - `- [ ] Task description` → Not started
   - `- [x] Task description` → Completed

6. Include references to existing Issues when applicable.
