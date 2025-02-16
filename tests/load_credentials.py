"""Load credentials from a JSON file if not already set in environment variables."""

import base64
import json
import os
from pathlib import Path

REQUIRED_ENV_VARS = {
    "polly": ["POLLY_REGION", "POLLY_AWS_KEY_ID", "POLLY_AWS_ACCESS_KEY"],
    "google": ["GOOGLE_SA_PATH", "GOOGLE_SA_FILE_B64"],
    "microsoft": ["MICROSOFT_TOKEN", "MICROSOFT_REGION"],
    "watson": ["WATSON_API_KEY", "WATSON_REGION", "WATSON_INSTANCE_ID"],
    "elevenlabs": ["ELEVENLABS_API_KEY"],
    "witai": ["WITAI_TOKEN"],
    "playht": ["PLAYHT_API_KEY", "PLAYHT_USER_ID"],
}

def check_required_env_vars() -> None:
    """Check that all required environment variables are set."""
    missing_vars = []
    for vars in REQUIRED_ENV_VARS.values():
        for var in vars:
            if not os.getenv(var):
                missing_vars.append(var)
    if missing_vars:
        msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        raise RuntimeError(msg)


def load_credentials(public_json_file: str = "credentials.json") -> None:
    """Load credentials from a JSON file if not already set in environment variables.

    Parameters
    ----------
    public_json_file : str
        The path to the public JSON file with credentials.

    """
    # Decode Google credentials if set
    decode_google_creds()

    # Construct the path to the private JSON file
    private_json_file = public_json_file.replace(".json", "-private.json")
    private_path = Path(private_json_file)

    # Decide which JSON file to use (private if available, otherwise public)
    if private_path.exists():
        json_file = private_path
    elif Path(public_json_file).exists():
        json_file = public_json_file
    else:
        # If neither JSON file exists, rely solely on environment variables
        # Check that all required environment variables are set
        check_required_env_vars()
        return  # Exit early if no files are found

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
    Also needs GOOGLE_SA_PATH
    """
    google_b64_creds = os.getenv("GOOGLE_SA_FILE_B64")
    google_sa_path = os.getenv("GOOGLE_SA_PATH", "google_creds.json")


    if google_b64_creds:
        try:
            # Ensure the directory exists
            creds_path = Path(google_sa_path)
            creds_path.parent.mkdir(parents=True, exist_ok=True)

            # Decode and write the credentials
            decoded_creds = base64.b64decode(google_b64_creds).decode("utf-8")
            with creds_path.open("w") as f:
                f.write(decoded_creds)
            if creds_path.exists() and creds_path.stat().st_size > 0:
                print(f"Google Service Account JSON created successfully at: {google_sa_path}")
            else:
                raise ValueError("Failed to create the Google Service Account file.")
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
