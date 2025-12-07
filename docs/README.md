# Verse Documentation

Welcome to the Verse documentation. This guide will help you understand, use, and contribute to the Verse interactive Bible reader with AI-powered insights.

## Getting Started

New to Verse? Start here:

- **[Quick Start Guide](getting-started.md)** - Get Verse up and running in minutes
- **[FAQ](faq.md)** - Frequently asked questions
- **[Available Translations](available-english-translations.md)** - Supported Bible translations

## Features

Learn about Verse's capabilities:

- **[Passage Links](features/passage-links.md)** - Navigate using URL parameters
- **[Wake Lock](features/wake-lock.md)** - Keep your device awake while reading

## Development

Contributing to Verse or running it locally:

- **[Development Setup](guides/development.md)** - Set up your local development environment
- **[Claude Usage Guide](guides/claude-usage.md)** - Working with Claude AI in this project
- **[Pre-commit Hooks](guides/pre-commit.md)** - Code quality automation
- **[Troubleshooting](guides/troubleshooting.md)** - Common issues and solutions
- **[Contributing Guidelines](../CONTRIBUTING.md)** - How to contribute to the project

## Architecture

Understand how Verse is built:

- **[System Architecture](architecture/README.md)** - High-level system design
- **[Security](architecture/security.md)** - Security features and best practices
- **[RAG System](architecture/rag.md)** - Retrieval-Augmented Generation for conversation memory
- **[Prompt Philosophy](architecture/prompt-philosophy.md)** - AI prompt design principles

## Advanced Features

Deep dives into specific capabilities:

### RAG (Retrieval-Augmented Generation)

- **[RAG Quick Start](guides/rag-quick-start.md)** - Get started with RAG features
- **[RAG Reference](guides/rag-reference.md)** - Detailed RAG API reference
- **[RAG Integration](guides/rag-integration.md)** - Integrating RAG into your code

## Reference

Technical reference documentation:

- **[API Endpoints](reference/api.md)** - Complete API documentation
- **[Database Schema](reference/database.md)** - Database models and relationships
- **[Configuration](reference/configuration.md)** - Environment variables and settings
- **[Prompts Module](reference/prompts.md)** - AI prompt components and composition
- **[Changelog](../CHANGELOG.md)** - Version history and changes

## About

Verse is an interactive Bible reader that combines beautiful text presentation with AI-powered insights from Claude. Highlight any passage to explore its historical context, theological significance, and practical application.

**Technology Stack:**
- Frontend: React 18, TypeScript, Vite
- Backend: Python 3.11, FastAPI
- Database: PostgreSQL
- AI: Anthropic Claude
