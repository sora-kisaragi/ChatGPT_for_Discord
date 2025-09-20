---
applyTo: "**/*.cs"
---

# C# Framework Guidelines (.NET Framework / .NET Core / .NET 6+)

Follow official Microsoft C# coding conventions and framework-specific best practices to ensure readability, maintainability, and consistent development workflows.

## Directory and Project Structure
- Use `src/` for main projects, `tests/` for unit tests.
- One class per file when possible.
- File names: PascalCase.cs
- Framework-specific guidance:
  - **.NET Framework / .NET Core / .NET 6+:** separate projects for API, UI, and libraries.
  - Keep solution files (`.sln`) at the root.

## Class, Method, and Variable Naming
- Class and interface names: PascalCase (e.g., `UserManager`)  
  クラス・インターフェイス名は PascalCase （例: `UserManager`）  
  类与接口名称使用 PascalCase（例: `UserManager`）  
  클래스 및 인터페이스 이름은 PascalCase 사용 (예: `UserManager`)
- Methods: PascalCase  
  メソッド名は PascalCase  
  方法名使用 PascalCase  
  메서드 이름은 PascalCase
- Variables and private fields: camelCase or _camelCase  
- Constants: UPPER_SNAKE_CASE or PascalCase
- Properties: PascalCase

## Coding Style
- Use explicit access modifiers (public/private/protected/internal).  
- Prefer `var` only when type is obvious.  
- Use `async/await` for asynchronous operations.  
- Keep methods small and focused.  
- Use XML documentation comments for public APIs.
- Framework-specific patterns:
  - **ASP.NET / ASP.NET Core:** MVC pattern, controllers, views, dependency injection.
  - **Entity Framework / EF Core:** DbContext, migrations, fluent API for model configuration.
  - **Unity (C# scripts):** MonoBehaviour lifecycle methods, SerializeField for editor fields.
  - **Unreal Engine (C# plugins, if applicable):** follow engine plugin conventions.
- Include shader-related conventions if using Unity or UE (HLSL/ShaderLab).

## Testing
- Use MSTest, NUnit, or xUnit.
- Test public APIs, business logic, and important workflows.
- Test projects should mirror the structure of main projects.

## AI Assistance
- Copilot can scaffold classes, controllers, models, and boilerplate code.
- Human review is recommended for critical business logic, database migrations, and platform-specific integration.

## Comments
- Main language: English  
- Supplement: 日本語 / 中文 / 한국어
