import json
import os
import platform


def load_credentials(public_json_file="credentials.json") -> None:
    """Load credentials from a public JSON file and optionally from a private JSON file,

    and set them as environment variables.

    :param public_json_file: Path to the public JSON file containing the credentials.
    """

    # Construct the path to the private JSON file
    private_json_file = public_json_file.replace(".json", "-private.json")

    def set_env_vars_from_json(json_file) -> None:
        with open(json_file) as file:
            data = json.load(file)
            for service, creds in data.items():
                for key, value in creds.items():
                    env_var = f"{service.upper()}_{key.upper()}"
                    os.environ[env_var] = value
#                     print(f"Set {env_var} to {value}")

    # Check if private credentials file exists
    if os.path.exists(private_json_file):
#         print(f"Loading private credentials from {private_json_file}")
        set_env_vars_from_json(private_json_file)
    else:
#         print(f"Loading public credentials from {public_json_file}")
        set_env_vars_from_json(public_json_file)

def set_env_vars_from_json(json_file) -> None:
    with open(json_file) as file:
        data = json.load(file)

        env_vars = {}
        for service, creds in data.items():
            for key, value in creds.items():
                env_var = f"{service.upper()}_{key.upper()}"
                env_vars[env_var] = value
                os.environ[env_var] = value  # Set for the current session

        if platform.system() == "Windows":
            set_env_vars_windows(env_vars)
        else:
            set_env_vars_unix(env_vars)

def set_env_vars_windows(env_vars) -> None:
    for var, value in env_vars.items():
        command = f'setx {var} "{value}"'
        os.system(command)

def set_env_vars_unix(env_vars) -> None:
    shell = os.environ.get("SHELL", "/bin/bash")
    if "bash" in shell:
        profile_path = os.path.expanduser("~/.bashrc")
    elif "zsh" in shell:
        profile_path = os.path.expanduser("~/.zshrc")
    else:
        profile_path = os.path.expanduser("~/.profile")

    with open(profile_path, "a") as profile:
        profile.write("\n# Environment variables set by script\n")
        for var, value in env_vars.items():
            profile.write(f'export {var}="{value}"\n')


if __name__ == "__main__":
#     json_file = 'path/to/your/credentials.json'
#     load_credentials(json_file)

    json_file = "credentials.json"
    set_env_vars_from_json(json_file)
