---
applyTo: "**/*.kt"
---

# Kotlin / Android Framework Guidelines

Follow the [Kotlin Style Guide](https://developer.android.com/kotlin/style-guide) and Android best practices for consistent code and readability.

## Directory and File Structure
- Use `src/main/java/`, `src/main/kotlin/`, `src/main/res/`, `src/test/` directories.
- One class per file.
- File names: PascalCase for classes, snake_case for resources.

## Class and Object Naming
- Class names: PascalCase (e.g., `MyActivity`).
- Interface names: PascalCase, optionally prefix with `I`.
- Function names: camelCase.
- Variable names: camelCase.
- Constants: UPPER_SNAKE_CASE.

## Coding Style
- Prefer immutable variables (`val`) over mutable (`var`) where possible.
- Keep functions short, single responsibility.
- Use Kotlin idioms (e.g., `when`, `let`, `apply`, `also`).
- Add KDoc comments in English (main), 日本語 / 中文 / 한국어 (supplement).

## Android Guidelines
- Follow Android Jetpack recommendations.
- Use ViewModel, LiveData / StateFlow for state management.
- Use resource strings, dimensions, and colors instead of hard-coded values.
- Layouts: follow Material Design guidelines.

## Testing
- Use JUnit + AndroidX Test libraries.
- Name test files as `*Test.kt`.
- Write tests for Activities, Fragments, ViewModels, and major business logic.

## AI Assistance
- Copilot can scaffold Activities, Fragments, and layouts.
- Encourage human review for naming, UI conventions, and business logic separation.

## Comments
- Main language: English
- Supplement: 日本語 / 中文 / 한국어
