---
sidebar_position: 1
---

# Developer Overview

This section provides information for developers who want to contribute to TTS Wrapper or integrate it into their projects.

## Development Environment

### Using UV (Recommended)

1. [Install UV](https://docs.astral.sh/uv/#getting-started)
   ```sh
   pip install uv
   ```

2. Clone the repository:
   ```sh
   git clone https://github.com/willwade/tts-wrapper.git
   cd tts-wrapper
   ```

3. Install Python dependencies:
   ```sh
   uv sync
   ```

4. Install system dependencies (Linux only):
   ```sh
   uv run postinstall
   ```

To generate a requirements.txt file:
```sh
uv export --format requirements-txt --all-extras --no-hashes
```
Note: This will include all dependencies including dev ones.

### Using Pip

1. Clone the repository:
   ```sh
   git clone https://github.com/willwade/tts-wrapper.git
   cd tts-wrapper
   ```

2. Install the package and dependencies:
   ```sh
   pip install .
   ```

   For optional dependencies:
   ```sh
   pip install .[google,watson,polly,elevenlabs,microsoft]
   ```

## Project Structure

```
tts_wrapper/
├── engines/           # TTS engine implementations
│   ├── avsynth/      # macOS AVSpeechSynthesizer
│   ├── espeak/       # eSpeak-NG
│   ├── google/       # Google Cloud TTS
│   └── ...
├── ssml/             # SSML handling
├── exceptions.py     # Custom exceptions
└── tts.py           # Base TTS interface

tests/               # Test suite
website/             # Documentation site
examples/            # Example scripts
```

## Development Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Include docstrings for all public methods
   - Keep methods focused and single-purpose

2. **Testing**
   - Write unit tests for new features
   - Include integration tests for engine implementations
   - Test with both online and offline scenarios

3. **Documentation**
   - Update relevant documentation files
   - Include code examples
   - Document any new features or changes

4. **Error Handling**
   - Use custom exceptions where appropriate
   - Provide meaningful error messages
   - Handle both expected and unexpected errors

## Tools and Dependencies

- **Development Dependencies**
  - pytest: Testing framework
  - black: Code formatting
  - mypy: Type checking
  - docusaurus: Documentation site

- **Runtime Dependencies**
  - sounddevice: Audio playback
  - numpy: Audio processing
  - requests: HTTP client

## Next Steps

- Learn about [adding new engines](adding-engines)
- Understand our [release process](releases)
- Check out how to [contribute](contributing) 