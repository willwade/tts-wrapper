---
sidebar_position: 3
---

# Release Process

This guide explains how to create and manage releases for TTS Wrapper.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

## Creating a Release

1. **Update Version**
   - Update version in `pyproject.toml`
   - Update version in documentation if necessary
   - Update CHANGELOG.md

2. **Create Git Tag**
   ```sh
   git tag -a v0.1.0 -m "Release 0.1.0"
   git push origin v0.1.0
   ```

3. **GitHub Release**
   - The GitHub Action will automatically:
     - Build the package
     - Run tests
     - Deploy documentation
     - Publish to PyPI (if configured)

## Release Checklist

Before creating a release:

- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] All GitHub issues for this version are closed
- [ ] All pull requests for this version are merged
- [ ] Version numbers are updated
- [ ] Release notes are prepared

## Documentation Deployment

Documentation is automatically deployed when:
1. Changes are pushed to the main branch
2. A new release tag is created
3. The deploy-docs workflow is manually triggered

The deployment process:
1. Builds the Docusaurus site
2. Deploys to GitHub Pages
3. Updates the documentation version

## Hotfix Process

For urgent fixes:

1. Create a hotfix branch from the release tag:
   ```sh
   git checkout -b hotfix/v0.1.1 v0.1.0
   ```

2. Make necessary fixes

3. Update version and create new tag:
   ```sh
   git tag -a v0.1.1 -m "Hotfix 0.1.1"
   git push origin v0.1.1
   ```

## Release Notes

Good release notes should include:

- Summary of changes
- New features
- Bug fixes
- Breaking changes
- Migration instructions (if needed)
- Contributors
- Links to relevant issues/PRs

Example:
```markdown
## [0.1.0] - 2024-03-20

### Added
- New TTS engine: Sherpa-ONNX
- Streaming support for Play.HT
- Word timing callbacks for AVSynth

### Fixed
- Memory leak in audio playback
- SSML parsing for Microsoft Azure

### Changed
- Improved error handling
- Updated documentation structure

### Breaking Changes
- Renamed `speak_async` to `speak_streamed`
- Changed credential format for Watson TTS
``` 