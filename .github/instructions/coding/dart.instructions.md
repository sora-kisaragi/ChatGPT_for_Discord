---
applyTo: "**/*.dart"
---

# Flutter / Dart Coding Standards

## Comments
- Use English for main comments, Japanese for clarification if necessary.
- Document public methods and classes with DartDoc style.

## Naming Conventions
- Classes: PascalCase
- Variables, functions: camelCase
- Constants: ALL_CAPS_WITH_UNDERSCORES
- Widget filenames: snake_case

## Widget Structure
- Prefer small reusable widgets
- Keep build methods concise
- Use StatelessWidget when possible

## State Management
- Follow chosen state management (Provider, Riverpod, Bloc, etc.)
- Separate UI and business logic

## Testing
- Write unit tests for business logic
- Widget tests for UI components

## Formatter & Lint
- Use `flutter format` / `dart format`
- Enable recommended lints (e.g., `flutter_lints`)
