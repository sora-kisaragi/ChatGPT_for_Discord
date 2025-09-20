# GitHub Copilot Instructions Standardization Template

This document provides templates and guidelines for maintaining consistency across all Copilot instruction files.

## File Naming Conventions

- Use **kebab-case** for all filenames: `file-name.extension.md`
- Use consistent extensions based on file type:
  - `.instructions.md` - For language/framework-specific coding guidelines
  - `.prompt.md` - For general-purpose prompts and templates
  - `.chatmode.md` - For agent-based chat mode configurations

## Directory Structure

```
.github/
├── instructions/
│   ├── coding/           # Language-specific coding standards
│   ├── framework/        # Framework-specific guidelines
│   ├── documentation.instructions.md
│   ├── git-flow.instructions.md
│   └── task-management.instructions.md
├── prompts/              # General-purpose prompts
│   ├── commit-message.prompt.md
│   ├── code-review.prompt.md
│   └── task-management.prompt.md
└── chatmodes/            # Agent-based chat configurations
    ├── agent-planning.chatmode.md
    ├── agent-qa.chatmode.md
    └── pr-review.chatmode.md
```

## Metadata Templates

### Instructions Files (`*.instructions.md`)
```yaml
---
applyTo: "**/*.ext"
---
```

### Prompt Files (`*.prompt.md`)
```yaml
---
mode: ask
tools: [tool1, tool2]
description: Brief description of the prompt's purpose.
---
```

### Chat Mode Files (`*.chatmode.md`)
```yaml
---
mode: 'agent'
tools: ['tool1', 'tool2', 'tool3']
description: 'Detailed description of the agent mode capabilities and usage.'
---
```

## Content Structure Template

### Instructions Files
```markdown
# File Title

Brief introduction explaining the purpose and scope.

## File Structure and Organization
- Standard project organization patterns
- File naming conventions

## Naming Conventions
- Class/function/variable naming rules
- Language-specific conventions

## Coding Style
- Syntax preferences
- Best practices
- Framework-specific patterns

## Comments and Documentation
- Main comments in English
- Optional clarifications in 日本語 / 中文 / 한국어
- Documentation standards

## Testing
- Testing frameworks and tools
- Test organization patterns

## Tools and Formatting
- Linters, formatters, and development tools
```

### Prompt Files
```markdown
# Prompt Title

Clear explanation of the prompt's goal and usage.

## Rules:
- Specific guidelines for the prompt
- Format requirements
- Output expectations

## Example
```text
Example output or usage
```
```

### Chat Mode Files
```markdown
# Mode Title

Purpose and capabilities description.

- Key features and behaviors
- Usage guidelines
- Tool integration notes

# Agent Instructions

- Specific instructions for agent behavior
- Tool usage guidelines
- Output format requirements
```

## Quality Standards

### Content Detail Level
- **High Detail**: Language/framework instruction files should include comprehensive guidelines covering structure, naming, style, testing, and tools
- **Medium Detail**: General instruction files should cover essential practices and patterns
- **Concise**: Prompt and chat mode files should be focused and actionable

### Multi-language Support
Include comment examples in multiple languages where appropriate:
```markdown
- Main comments in English
  主要なコメントは英語で記述
  主要注释使用英语
  주요 주석은 영어로 작성
```

### Heading Structure
- Use non-numbered headings: `## Section Name`
- Maintain consistent hierarchy
- Avoid deep nesting (max 3 levels recommended)

## Validation Checklist

Before adding new instruction files, verify:

- [ ] Filename follows kebab-case convention
- [ ] File extension matches content type
- [ ] Metadata format matches template
- [ ] Content structure follows template
- [ ] Detail level is appropriate for file type
- [ ] Multi-language examples included where relevant
- [ ] Headings use consistent format
- [ ] Directory placement is logical