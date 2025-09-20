---
applyTo: "**/*.cpp, **/*.h, **/*.cs, **/*.py, **/*.usf"
---

# Unreal Engine / C++ & Extensions & Shader Standards

## Comments
- Main comments in English
- Optional clarifications in Japanese, Chinese, or Korean

## C++ Naming Conventions
- Classes: PascalCase with `U`/`A`/`F` prefixes
- Variables: camelCase
- Constants: ALL_CAPS
- Functions: PascalCase

## C#/Python Extensions
- Use idiomatic C#/Python naming and conventions
- Separate engine extensions from gameplay logic
- Comment public APIs clearly

## Shader Guidelines (USF/HLSL)
- File names: PascalCase
- Use consistent indentation
- Comment all custom functions
- Organize properties and includes logically

## UE Guidelines
- Use UPROPERTY / UFUNCTION macros properly
- Follow memory management rules
- Prefer composition over inheritance
- Separate headers and source

## Testing
- Unit tests with UE automation framework
- Gameplay/Integration tests with Blueprints
- Shader tests in editor or sample scenes

## Formatter & Lint
- ClangFormat for C++
- Visual Studio / Rider formatting for C#
- PEP8 for Python
