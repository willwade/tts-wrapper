---
sidebar_position: 4
---

# Contributing

We welcome contributions to TTS Wrapper! This guide will help you get started.

## Getting Started

1. **Fork the Repository**
   - Visit [TTS Wrapper on GitHub](https://github.com/willwade/tts-wrapper)
   - Click the "Fork" button
   - Clone your fork locally

2. **Set Up Development Environment**
   ```sh
   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/tts-wrapper.git
   cd tts-wrapper

   # Install dependencies with UV
   pip install uv
   uv sync
   ```

## Development Workflow

1. **Create a Branch**
   ```sh
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/issue-description
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests**
   ```sh
   pytest tests/
   ```

4. **Check Code Style**
   ```sh
   # Format code
   black .

   # Check types
   mypy .
   ```

5. **Commit Changes**
   ```sh
   git add .
   git commit -m "Description of changes"
   ```

6. **Push and Create Pull Request**
   ```sh
   git push origin feature/my-new-feature
   ```
   Then create a Pull Request on GitHub.

## Pull Request Guidelines

1. **Description**
   - Clear description of changes
   - Reference any related issues
   - List breaking changes
   - Include screenshots for UI changes

2. **Code Quality**
   - Follow PEP 8 style guide
   - Include type hints
   - Add docstrings
   - Write clear commit messages

3. **Testing**
   - Add tests for new features
   - Ensure all tests pass
   - Include both unit and integration tests

4. **Documentation**
   - Update relevant documentation
   - Add docstrings to new code
   - Include examples if applicable

## Documentation Contributions

1. **Website Updates**
   - Located in `website/` directory
   - Built with Docusaurus
   - Preview changes locally:
     ```sh
     cd website
     yarn install
     yarn start
     ```

2. **API Documentation**
   - Update docstrings in code
   - Follow Google style format
   - Include type hints
   - Add examples

## Issue Guidelines

When creating issues:

1. **Bug Reports**
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Code examples

2. **Feature Requests**
   - Clear use case
   - Expected behavior
   - Example implementation if possible
   - Related issues/PRs

## Code Review Process

1. **Initial Review**
   - Code style and quality
   - Test coverage
   - Documentation
   - Performance implications

2. **Secondary Review**
   - Architecture considerations
   - Security implications
   - Breaking changes
   - Backward compatibility

3. **Final Review**
   - Documentation completeness
   - Test coverage
   - Merge conflicts
   - Version numbers

## Community Guidelines

- Be respectful and inclusive
- Follow the code of conduct
- Help others learn and grow
- Provide constructive feedback
- Acknowledge contributions

## Getting Help

- Create an issue for questions
- Join discussions on GitHub
- Check existing documentation
- Review closed issues/PRs

## Next Steps

- Review [adding new engines](adding-engines)
- Learn about the [release process](releases)
- Check out the [developer overview](overview) 