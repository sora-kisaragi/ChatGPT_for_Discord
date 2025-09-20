---
applyTo: "**/*.cpp, **/*.h, **/*.hpp"
---

# C++ Framework Guidelines (Game Engines, Libraries)

Follow [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html) for readability, maintainability, and cross-platform compatibility.

## Directory and File Structure
- Use `src/` for source code, `include/` for headers, `tests/` for unit tests.
- One class per file where appropriate.
- File names: `snake_case.hpp` / `snake_case.cpp` (Google C++ Style Guide)
- Framework-specific guidance:
  - **Unreal Engine:** source code in `Source/ProjectName/`, modules, plugin organization.
  - **Unity (C++ native plugins):** organize in Plugins folder.
  - Other C++ frameworks: standard include/lib separation.

## Class, Function, and Variable Naming
- Classes: `PascalCase` (e.g., `PlayerController`)  
  クラス名は PascalCase （例: `PlayerController`）  
  类名使用 PascalCase（例: `PlayerController`）  
  클래스명은 PascalCase 사용 (예: `PlayerController`)
- Functions / Methods: `CamelCase` (e.g., `GetPlayerName()`)  
- Variables: `snake_case` (e.g., `player_score`)  
- Constants / Macros: `kUpperSnakeCase` for constants, `UPPER_SNAKE_CASE` for macros

## Coding Style
- Use RAII and smart pointers (`std::unique_ptr`, `std::shared_ptr`) where possible.
- Prefer `const` correctness and `noexcept` when applicable.
- Keep functions short and modular.
- Use header guards (`#pragma once` preferred).
- Use namespaces to avoid symbol collisions.
- Framework-specific patterns:
  - **Unreal Engine:** UCLASS, UPROPERTY, UObject lifecycle, macros.
  - **Unity native plugins:** extern "C" for bindings, minimal dependencies.
  - **Shader files (HLSL/GLSL):** use consistent formatting and naming conventions.

## Testing
- Use GoogleTest or Catch2.
- Test core logic, modules, and interfaces with engine or libraries.
- Organize test files mirroring the `src/include` structure.

## AI Assistance
- Copilot can generate boilerplate code, class skeletons, and shader scaffolds.
- Human review recommended for engine integration, memory management, and performance-critical code.

## Comments
- Main language: English  
- Supplement: 日本語 / 中文 / 한국語
