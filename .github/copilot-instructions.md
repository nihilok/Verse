# GitHub Copilot Instructions for Verse

## Project Overview

Verse is an interactive Bible reader with AI-powered insights. Users can highlight any passage to explore its historical context, theological significance, and practical application.

## Project Goals

- Create an intuitive and accessible Bible reading experience
- Integrate AI capabilities to provide meaningful insights on biblical passages
- Focus on user experience and ease of use
- Maintain respectful and thoughtful handling of religious content

## Coding Standards

### General Guidelines
- Write clear, maintainable, and well-documented code
- Follow language-specific best practices and conventions
- Use descriptive variable and function names
- Keep functions focused and single-purpose
- Comment complex logic and algorithms

### Code Style
- Use consistent indentation (2 or 4 spaces depending on language convention)
- Follow the existing code style in the repository
- Use meaningful commit messages that explain the "why" behind changes

## Security Guidelines

- Never commit API keys, secrets, or credentials to the repository
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Follow security best practices for authentication and authorization
- Be mindful of rate limits when integrating with external APIs

## Testing Requirements

- Write tests for new features and bug fixes when test infrastructure exists
- Ensure changes don't break existing functionality
- Test edge cases and error handling
- Consider accessibility in all user-facing features

## Documentation

- Update documentation when adding or modifying features
- Document API endpoints and data structures
- Include usage examples for complex features
- Keep README.md up to date with setup and usage instructions

## AI Integration Guidelines

- Use AI responsibly and transparently
- Ensure AI-generated content is accurate and appropriate
- Consider context and cultural sensitivity when providing biblical insights
- Provide citations and sources for AI-generated information when possible

## Accessibility

- Follow WCAG guidelines for web accessibility
- Ensure the application is usable with keyboard navigation
- Use semantic HTML and ARIA attributes appropriately
- Support screen readers and assistive technologies
- Consider users with different reading abilities and preferences

## Best Practices

- Prioritize user privacy and data security
- Optimize for performance and loading times
- Support multiple devices and screen sizes
- Handle errors gracefully with helpful error messages
- Consider internationalization and localization needs

## Tooling

- Use `bun` for JavaScript/TypeScript package management and scripts in the frontend. Prefer `bun` over `npm` or `yarn` for all relevant commands.
- Use `uv` for Python environment management where possible.

