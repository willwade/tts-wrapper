"""Load credentials from a JSON file if not already set in environment variables."""

import base64
import json
import os
from pathlib import Path


def load_credentials(public_json_file: str = "credentials.json") -> None:
    """Load credentials from a JSON file if not already set in environment variables.

    The JSON file should contain a dictionary with service names as keys and
    dictionaries of credentials as values. For example:

    {
        "google": {
            "api_key": "your_google_api_key"
        },
        "microsoft": {
            "api_key": "your_microsoft_api_key"
        }
    }

    Parameters
    ----------
    public_json_file : str
        The path to the public JSON file with credentials.

    """
    # Decode Google credentials if set
    decode_google_creds()

    # Construct the path to the private JSON file
    private_json_file = public_json_file.replace(".json", "-private.json")

    # Decide which JSON file to use (private, if available, or else public)
    private_path = Path(private_json_file)
    json_file = private_path if private_path.exists() else public_json_file

    # Load from JSON only if the environment variables are not already set
    if not credentials_set_in_env(json_file):
        set_env_vars_from_json(json_file)


def credentials_set_in_env(json_file: str) -> bool:
    """Check if credentials from the JSON file are already set in environment variables.

    Parameters
    ----------
    json_file : str
        The path to the JSON file containing credentials.

    Returns
    -------
    bool
        True if all credentials are set in environment variables; False otherwise.

    """
    with Path(json_file).open() as file:
        data = json.load(file)
        # Check if each credential is already set in the environment
        for service, creds in data.items():
            for key in creds:
                env_var = f"{service.upper()}_{key.upper()}"
                if env_var not in os.environ:
                    return False  # At least one credential is missing
    return True  # All credentials are set in the environment


def decode_google_creds() -> None:
    """Decode and save the Base64 Google credentials JSON file.

    Should only work if `GOOGLE_SA_FILE_B64` is set.
    Also needs GOOGLE_CREDS_PATH
    """
    google_b64_creds = os.getenv("GOOGLE_SA_FILE_B64")
    google_creds_path = os.getenv("GOOGLE_CREDS_PATH", "google_creds.json")

    if google_b64_creds:
        try:
            decoded_creds = base64.b64decode(google_b64_creds).decode("utf-8")
            with Path(google_creds_path).open("w") as f:
                f.write(decoded_creds)
        except (OSError, ValueError) as e:
            msg = "Failed to decode or save GOOGLE_SA_FILE_B64"
            raise ValueError(msg) from e


def set_env_vars_from_json(json_file: str) -> None:
    """Set environment variables from a JSON file.

    Parameters
    ----------
    json_file : str
        The path to the JSON file containing credentials.

    """
    with Path(json_file).open() as file:
        data = json.load(file)
        for service, creds in data.items():
            for key, value in creds.items():
                env_var = f"{service.upper()}_{key.upper()}"
                os.environ[env_var] = value  # Set for the current session


if __name__ == "__main__":
    # Attempt to load credentials, falling back to JSON files if needed
    load_credentials("credentials.json")
