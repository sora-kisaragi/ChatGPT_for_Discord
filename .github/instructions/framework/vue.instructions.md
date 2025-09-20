---
applyTo: "**/*.vue"
---

# Vue.js Framework Guidelines

Follow the [Vue.js Style Guide](https://vuejs.org/style-guide/) for consistent code structure and readability.

## Directory and File Structure
- Use `components/`, `views/`, `store/` directories.
- One component per file.
- Name files using PascalCase for components (e.g., `MyComponent.vue`).

## Component Naming
- Component names: PascalCase in files, kebab-case in templates.
- Props: camelCase in JS, kebab-case in templates.

## Template
- Use self-closing tags where possible.
- Use `v-bind` and `v-on` shorthand consistently.

## Script
- Use `export default {}` pattern.
- Prefer composition API (`setup`) over options API for new components.
- Always define props with types.
- Add JSDoc comments in English (main), Japanese/Chinese/Korean (supplement).

## Style
- Use scoped CSS.
- Use BEM or another consistent class naming convention.

## Testing
- Use Jest + Vue Test Utils.
- Name test files as `*.spec.js`.
- Write tests for all critical components.

## AI Assistance
- Copilot can assist with component scaffolding and template generation.
- Encourage human review for logic and naming consistency.

## Comments
- Main language: English
- Supplement: 日本語 / 中文 / 한국어
