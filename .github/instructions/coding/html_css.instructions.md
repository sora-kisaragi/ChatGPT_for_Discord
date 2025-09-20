---
applyTo: "**/*.html, **/*.css"
---

# HTML / CSS Coding Standards

Follow modern web standards and best practices for consistent, maintainable, and accessible code.

## File Structure and Organization
- Separate structure (HTML), presentation (CSS), and behavior (JavaScript)
- Use semantic HTML elements for better accessibility and SEO
- Organize CSS files by components or logical sections
- File names: kebab-case for both HTML and CSS files

## HTML Guidelines
- Use proper document structure with DOCTYPE, HTML, head, and body
- Indent with 2 spaces consistently
- Use semantic tags: `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, `<footer>`
- Include proper meta tags: charset, viewport, description
- Use meaningful `id` and `class` names in kebab-case
- Validate all HTML for syntax correctness
- Ensure accessibility: alt text, proper heading hierarchy, ARIA labels when needed

## CSS Guidelines
- Indent with 2 spaces consistently
- Use BEM (Block Element Modifier) or consistent naming convention
- Organize styles logically: normalize/reset → base → layout → components → utilities
- Prefer classes over IDs for styling
- Use CSS custom properties (variables) for consistent theming
- Write mobile-first responsive designs with media queries
- Separate layout, typography, and color styles for maintainability

## Comments and Documentation
- Main comments in English  
  主要なコメントは英語で記述  
  主要注释使用英语  
  주요 주석은 영어로 작성
- Use `<!-- -->` for HTML comments, `/* */` for CSS comments
- Document complex layouts or interactions
- Explain browser-specific workarounds when necessary

## Testing and Validation
- Validate HTML with W3C Markup Validator
- Validate CSS with W3C CSS Validator
- Test cross-browser compatibility
- Ensure responsive design works on multiple devices
- Check accessibility with tools like WAVE or axe
- Test performance and loading times

## Tools and Formatting
- Use Prettier for consistent formatting
- Use stylelint for CSS linting and style guide enforcement
- Consider PostCSS for preprocessing when needed
- Use browser developer tools for debugging and optimization
