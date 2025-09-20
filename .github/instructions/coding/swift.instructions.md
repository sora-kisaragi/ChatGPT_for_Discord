---
applyTo: "**/*.swift"
---

# Swift / iOS Framework Guidelines

Follow the [Swift API Design Guidelines](https://swift.org/documentation/api-design-guidelines/) and [Apple Swift Style Guide](https://swift.org/documentation/api-design-guidelines/) for consistent and readable code.

## Directory and File Structure
- Use `Sources/`, `Tests/`, `Resources/` directories.
- One class, struct, enum, or protocol per file.
- File names: PascalCase matching the type name.

## Class, Struct, Enum, and Protocol Naming
- Type names: PascalCase (e.g., `MyViewController`, `UserModel`).
- Function names: camelCase.
- Variable names: camelCase.
- Constants: UPPER_SNAKE_CASE or camelCase for static constants.
- Enum cases: camelCase.

## Coding Style
- Use `let` for immutable variables and `var` only when necessary.
- Keep functions concise and single-responsibility.
- Favor Swift idioms (`guard`, `defer`, `optional binding`).
- Add documentation comments in English (main), 日本語 / 中文 / 한국어 (supplement).

## iOS Guidelines
- Follow MVC or MVVM patterns consistently.
- Use UIKit, SwiftUI, or Combine/Async appropriately.
- Use Storyboards/XIBs sparingly; prefer programmatic UI when possible.
- Localize strings using `NSLocalizedString` instead of hard-coded values.

## Testing
- Use XCTest for unit and UI tests.
- Name test files as `*Tests.swift`.
- Test ViewControllers, ViewModels, Models, and key business logic.

## AI Assistance
- Copilot can scaffold classes, Views, and boilerplate code.
- Encourage human review for logic correctness, UI conventions, and naming.

## Comments
- Main language: English
- Supplement: 日本語 / 中文 / 한국어
