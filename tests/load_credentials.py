import json
import os
from pathlib import Path

def load_credentials(public_json_file="credentials.json") -> None:
    """Load credentials from a JSON file if not already set in environment variables."""
    # Construct the path to the private JSON file
    private_json_file = public_json_file.replace(".json", "-private.json")

    # Decide which JSON file to use (private, if available, or else public)
    json_file = private_json_file if os.path.exists(private_json_file) else public_json_file

    # Load from JSON only if the environment variables are not already set
    if not credentials_set_in_env(json_file):
        set_env_vars_from_json(json_file)
    else:
        pass


def credentials_set_in_env(json_file) -> bool:
    """Check if credentials from the JSON file are already set in environment variables."""
    with open(json_file) as file:
        data = json.load(file)
        # Check if each credential is already set in the environment
        for service, creds in data.items():
            for key in creds:
                env_var = f"{service.upper()}_{key.upper()}"
                if env_var not in os.environ:
                    return False  # If any variable is missing, credentials are not fully set
    return True  # All credentials are set in the environment


def set_env_vars_from_json(json_file) -> None:
    """Set environment variables from a JSON file."""
    with open(json_file) as file:
        data = json.load(file)
        for service, creds in data.items():
            for key, value in creds.items():
                env_var = f"{service.upper()}_{key.upper()}"
                os.environ[env_var] = value  # Set for the current session


if __name__ == "__main__":
    # Attempt to load credentials, falling back to JSON files if needed
    load_credentials("credentials.json")
