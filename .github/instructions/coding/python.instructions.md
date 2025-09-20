---
applyTo: "**/*.py"
---

# Python Framework Guidelines (Django / Flask / FastAPI)

Follow the [PEP 8](https://peps.python.org/pep-0008/) style guide and framework-specific best practices for consistency, readability, and maintainability.

## Directory and File Structure
- Use `src/` or `project_name/` for main code, `tests/` for test code.
- One class per file where appropriate.
- File names: snake_case.
- Framework-specific guidance:
  - **Django:** apps/, models.py, views.py, serializers.py, forms.py
  - **Flask:** blueprints/, app factory pattern
  - **FastAPI:** routers/, Pydantic models, main.py for app setup

## Class, Function, and Variable Naming
- Class names: PascalCase (e.g., `UserModel`)  
  クラス名は PascalCase を使用（例: `UserModel`）  
  类名使用 PascalCase（例: `UserModel`）  
  클래스명은 PascalCase 사용 (예: `UserModel`)
- Function and method names: snake_case  
  関数・メソッド名は snake_case  
  函数与方法名使用 snake_case  
  함수 및 메서드 이름은 snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE

## Coding Style
- Prefer immutable variables where possible.
- Keep functions small and focused.
- Use type hints for functions and variables.
- Add docstrings in English (main), 日本語 / 中文 / 한국어 (supplement).
- Framework-specific idioms:
  - **Django:** models, views, serializers, forms
  - **Flask:** blueprints, app factory
  - **FastAPI:** Pydantic models, routers

## Testing
- Use `pytest` or `unittest`.
- Test views, endpoints, models, and core logic.
- Name test files as `test_*.py`.

## AI Assistance
- Copilot can scaffold views, routers, serializers, and boilerplate.
- Encourage human review for business logic, database migrations, and security practices.

## Comments
- Main language: English  
- Supplement: 日本語 / 中文 / 한국어
