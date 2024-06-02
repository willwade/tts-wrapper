import os
import subprocess
import sys

def main():
    # Check if the operating system is Linux
    if os.name != 'posix' or sys.platform != 'linux':
        print("This script is intended to run on Linux systems only.", file=sys.stderr)
        sys.exit(1)
    
    print("Installing system dependencies...")

    # List of commands to install dependencies
    commands = [
        ["apt-get", "update"],
        ["apt-get", "install", "-y", "portaudio19-dev"],
        # Add other system dependencies here
    ]

    # Execute each command
    for command in commands:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing {command}: {e}", file=sys.stderr)
            sys.exit(1)

    print("System dependencies installed successfully.")

if __name__ == "__main__":
    main()
