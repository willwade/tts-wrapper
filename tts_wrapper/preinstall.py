import os
import platform
import subprocess
import sys

def is_espeak_installed():
    try:
        subprocess.run(["espeak-ng", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def install_espeak():
    system = platform.system().lower()
    try:
        if system == "linux":
            print("Installing espeak-ng on Linux...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "espeak-ng"], check=True)
        elif system == "darwin":
            print("Installing espeak-ng on macOS...")
            subprocess.run(["brew", "install", "espeak-ng"], check=True)
        elif system == "windows":
            print("Please download and install espeak-ng manually from: https://github.com/espeak-ng/espeak-ng/releases")
            sys.exit(1)
        else:
            print(f"Unsupported platform: {system}")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        sys.exit(1)

def main():
    # Check if espeak-ng is needed and install it if necessary
    if "espeak" in sys.argv:
        print("Checking for espeak-ng...")
        if not is_espeak_installed():
            print("espeak-ng is not installed. Attempting to install...")
            install_espeak()
        else:
            print("espeak-ng is already installed.")
    else:
        print("No additional system dependencies to install.")

if __name__ == "__main__":
    main()