# Instructions for Contributors

- Use [`uv`](https://github.com/astral-sh/uv) for dependency management.
  Install all extras with:
  
  ```bash
  uv sync --all-extras
  ```

- Run tests with:
  
  ```bash
  uv run pytest -m "not synthetic and not sapi and not watson"
  ```

- The test suite requires credentials for several TTS engines. Provide
  the necessary environment variables or a `credentials.json` file as
  described in `tests/load_credentials.py`.

- When new engines require credentials, ensure corresponding secrets are
  added to the GitHub Actions workflow environment variables.
