---
applyTo: "**/*.cs, **/*.shader"
---

# Unity / C# & Shader Coding Standards

## Comments
- Main comments in English
- Optional clarifications in Japanese, Chinese, or Korean

## C# Naming Conventions
- Classes: PascalCase
- Methods, variables: camelCase
- Constants: ALL_CAPS_WITH_UNDERSCORES
- Script filenames: match class name

## Shader Guidelines
- Use HLSL/ShaderLab conventions
- File names: PascalCase or match material names
- Comment shader functions and calculations clearly
- Organize properties, functions, and passes consistently

## Unity Guidelines
- Use MonoBehaviour or ScriptableObject appropriately
- Separate logic from UI
- Avoid heavy computations in `Update`
- Use Coroutines or async/await for async tasks
- Reusable components preferred

## Testing
- Unit tests using Unity Test Framework for C# scripts
- Integration/play tests for gameplay mechanics
- Shader testing by applying materials in scenes

## Formatter & Lint
- Visual Studio / Rider auto-format
- Follow C# and HLSL style conventions
