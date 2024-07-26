import os
import subprocess
import sys
import shutil

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("ffmpeg is installed, but there was an error checking the version.")
        sys.exit(1)
    except FileNotFoundError:
        print("ffmpeg is not installed. Attempting to install ffmpeg...")
        install_ffmpeg()

def install_ffmpeg():
    if sys.platform == "win32":
        install_ffmpeg_windows()
    elif sys.platform == "darwin":
        install_ffmpeg_macos()
    elif sys.platform == "linux":
        install_ffmpeg_linux()
    else:
        print("Unsupported platform. Please install ffmpeg manually.")
        sys.exit(1)
    print("ffmpeg installed successfully.")

def install_ffmpeg_windows():
    try:
        print("Downloading and installing ffmpeg for Windows...")
        subprocess.run([
            "powershell", "-Command",
            "Invoke-WebRequest -Uri https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.zip -OutFile ffmpeg.zip; "
            "Expand-Archive -Force ffmpeg.zip -DestinationPath .; "
            "Remove-Item -Force ffmpeg.zip; "
            "Move-Item -Path ./ffmpeg-*/* -Destination ./ffmpeg; "
            "Remove-Item -Force ./ffmpeg-* -Recurse; "
            "[System.Environment]::SetEnvironmentVariable('Path', [System.Environment]::GetEnvironmentVariable('Path', [System.EnvironmentVariableTarget]::Machine) + ';' + (Get-Location).Path + '\\ffmpeg\\bin', [System.EnvironmentVariableTarget]::Machine)"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffmpeg on Windows: {e}")
        print("Please install ffmpeg manually from https://ffmpeg.org/download.html")
        sys.exit(1)

def install_ffmpeg_macos():
    try:
        if shutil.which("brew") is None:
            print("Homebrew is not installed. Attempting to install Homebrew...")
            subprocess.run([
                "/bin/bash", "-c", "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            ], check=True)
        print("Installing ffmpeg using Homebrew...")
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffmpeg on macOS: {e}")
        print("Please install Homebrew and ffmpeg manually. Visit https://brew.sh/ for Homebrew installation and run 'brew install ffmpeg'")
        sys.exit(1)

def install_ffmpeg_linux():
    try:
        print("Installing ffmpeg using apt for Linux...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing ffmpeg on Linux: {e}")
        print("Attempting to install ffmpeg without sudo...")
        try:
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing ffmpeg without sudo on Linux: {e}")
            print("Please install ffmpeg manually using your package manager. For example, run 'sudo apt-get install ffmpeg'")
            sys.exit(1)

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
    try:
        import ffmpeg
        print("ffmpeg-python is installed, proceeding with ffmpeg check...")
        check_ffmpeg()
    except ImportError:
        print("ffmpeg-python is not installed, skipping ffmpeg check.")

    if sys.platform == 'linux':
        install_linux_dependencies()

if __name__ == "__main__":
    main()
