# Contributing to Multi-Agent Research System

Thank you for your interest in contributing to Multi-Agent Research System!
This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project and everyone participating in it is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold this code. Please report unacceptable behavior to royxforge@gmail.com.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```
   git clone https://github.com/your-username/multi-agent-research-system.git
   cd multi-agent-research-system
   ```
3. Add the upstream repository:
   ```
   git remote add upstream https://github.com/royxforge/multi-agent-research-system.git
   ```

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- npm

### Backend Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Verify Installation

```bash
# Backend
python -c "from src.api import app; print('Backend OK')"

# Frontend
cd frontend && npm run lint
```

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide.
- Use type annotations for all function signatures.
- Use `from __future__ import annotations` for deferred evaluation.
- Maximum line length: 88 characters (Black-compatible).
- Use descriptive names for variables and functions.

### TypeScript/React

- Follow the project's existing ESLint configuration.
- Use TypeScript strict mode.
- Use React functional components with hooks.
- Prefer Tailwind CSS utility classes over custom CSS.
- Use Framer Motion for animations where appropriate.

### Imports

Organize imports in the following order:

1. Standard library / built-in imports
2. Third-party imports
3. Local application imports

## Testing

### Backend Tests

```bash
pytest tests/ -v
pytest tests/test_chat.py -v
pytest tests/test_doi.py -v
pytest tests/test_summarize.py -v
pytest tests/test_validation.py -v
```

### Benchmark Suite

Before submitting changes that affect performance, run the benchmark suite:

```bash
python -m benchmarks.run_benchmarks
```

Ensure no regressions in key metrics.

## Pull Request Process

1. Create a new branch from `main`:
   ```
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear, descriptive commit messages.

3. Run tests:
   ```bash
   pytest tests/ -v
   ```

4. Push your branch and open a Pull Request on GitHub.

5. In your PR description, include:
   - What the change does
   - Any relevant issue numbers
   - How you tested the change
   - Screenshots or benchmark results if applicable

6. Request review from a maintainer.

## Commit Message Conventions

We follow conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `benchmark`

Examples:
```
feat(agents): add Ollama provider support for local LLM inference
fix(frontend): correct knowledge graph node color for dark mode
benchmark(tools): add image search cache latency measurements
```

## Issue Reporting

### Bug Reports

When filing a bug report, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior and actual behavior
- Environment details (OS, Python version, browser, LLM provider)
- Relevant logs or error messages
- Whether the issue occurs in backend, frontend, or both

### Feature Requests

We welcome feature suggestions! Please include:

- A clear description of the proposed feature
- The motivation or use case
- Any relevant research or references
- Whether you are willing to implement it

Thank you for helping make Multi-Agent Research System better!
