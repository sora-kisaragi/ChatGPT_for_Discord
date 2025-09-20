---
applyTo: "docs/**/*.md"
---

# Supplementary Documentation Guidelines

This instruction defines how to create **supplementary design and planning documents** when needed.

## General Rules
- Format all documents in **Markdown** unless explicitly requested otherwise.
- Use **Mermaid** diagrams for workflows, sequence diagrams, or architecture flows.
- Use **LaTeX syntax** for complex mathematical formulas inside Markdown.
- Keep documents concise and modular; prefer multiple small files over a single long one.
- Clearly state the purpose of the document at the beginning.

## Types of Supplementary Documents

### 1. Database Design (Optional)
- Only create if the feature requires schema changes.
- Use Markdown tables for schemas and include Mermaid ER diagrams if helpful.
- Document:
  - Entities, attributes, and types
  - Relationships between tables
  - Indexing or optimization strategies (if critical)

### 2. Business Process / Workflow (Optional)
- Use Mermaid `flowchart` or `sequenceDiagram` for business processes.
- Keep diagrams at a high level first, then break down into detailed views if necessary.
- Clarify actors, systems, and data flows.

### 3. API Specifications (Optional)
- Create if the change introduces or modifies endpoints.
- Include:
  - Endpoint: `GET /api/resource`
  - Parameters, request/response schemas
  - Example requests/responses
- Prefer **OpenAPI-style Markdown tables** for clarity.

### 4. High-Level Design (HLD) and Low-Level Design (LLD)
- Always create for significant features.
- **HLD**: Architecture overview, main components, interactions, and responsibilities.
- **LLD**: Detailed logic, data structures, pseudo-code, or class diagrams.
- Use Mermaid `classDiagram` for code-level designs when needed.

### 5. Task/Implementation Plan
- If an Issue or PR lacks enough detail, generate a Markdown checklist.
- Tasks should be atomic and ordered.
- Example:

```md
## Task Plan
- [ ] Define DB schema
- [ ] Implement API endpoints
- [ ] Write unit tests
- [ ] Update documentation

## Output
- Always output in Markdown.
- If a diagram is included, ensure it can render correctly in GitHub.
- Cross-link related documents (e.g., See also: docs/api_docs.md).
```
