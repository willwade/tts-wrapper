import os
import subprocess
import sys
import shutil


def install_linux_dependencies():
    print("Installing system dependencies on Linux...")
    commands = [
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "portaudio19-dev"],
    ]
    for command in commands:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing {command}: {e}", file=sys.stderr)
            print("Attempting to install dependencies without sudo...")
            try:
                subprocess.run(command[1:], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error installing {command[1:]} without sudo: {e}", file=sys.stderr)
                print("Please install dependencies manually.")
                sys.exit(1)
    print("Linux system dependencies installed successfully.")

def main():

    if sys.platform == 'linux':
        install_linux_dependencies()

if __name__ == "__main__":
    main()
