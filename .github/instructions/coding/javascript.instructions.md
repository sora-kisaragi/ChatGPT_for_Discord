---
applyTo: "src/**/*.{js,ts}"
---

# Coding Standards for JavaScript / TypeScript

## General Rules
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) for JS.
- For TypeScript, follow [TypeScript Handbook Recommendations](https://www.typescriptlang.org/docs/handbook/intro.html).
- Use **Prettier** for formatting and **ESLint** for linting.
- Add `// Contains AI-generated edits.` at the end of AI-modified files.

## Naming Conventions
- Variables and functions: `camelCase`
- Classes and interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private/protected members: `_camelCase`

## Commenting
- Write all comments in **English** as the primary language.
- Optionally add explanations in secondary languages (e.g., Japanese, Korean, Chinese) when necessary.
- Keep comments concise and meaningful; avoid redundant statements.
- Use JSDoc/TSDoc for documenting functions, classes, and modules.
- Example:
  ```ts
  /**
   * Calculate the sum of an array of numbers
   * 配列内の数値の合計を計算する
   */
  function sum(values: number[]): number {
      return values.reduce((a, b) => a + b, 0);
  }
  ```

## Error Handling

* Use `throw` and `try/catch` for error handling.
* Prefer custom error classes for specific scenarios.
* Avoid silent failures.

## Testing

* Use **Jest**, **Mocha**, or **Vitest** for unit tests.
* Place test files under `tests/` with mirrored directory structure of `src/`.
