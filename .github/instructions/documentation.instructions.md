---
applyTo: "docs/**/*.md"
---

# Documentation Instructions for Copilot

## Format Rules
- Generate all documents in Markdown (`.md`).
- Use code blocks for code examples with proper language tag.
- Include author, date, and version at the top of each file.

## Diagram Rules
- For diagrams, use Mermaid syntax.
  - Flowcharts, ER diagrams, state transitions, sequence diagrams.
- Only create diagrams when necessary.
- Label nodes clearly and consistently.

## Math / Formula Rules
- Use LaTeX for complex formulas or calculations.
- Inline: `$ ... $`, Block: `$$ ... $$`

## Required Documents
- Requirements (`requirements/`): System & user requirements
- HLD (`design/HLD.md`): High-level architecture
- LLD (`design/LLD.md`): Low-level design, classes, functions

## Optional Documents
- DB design (`optional/db_design.md`)
- Business workflow (`optional/business_flow.md`)
- API spec (`optional/api_spec.md`)
- Other supplements (`optional/calculations.md`)
- Only generate if explicitly requested.

## General Guidelines
- Maintain consistency with existing documents.
- Include links between related documents.
- Keep descriptions clear and concise.
- If unsure, provide suggestions rather than assumptions.
