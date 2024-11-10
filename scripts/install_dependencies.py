import subprocess
import sys


def install_linux_dependencies() -> None:
    commands = [
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "portaudio19-dev"],
    ]
    for command in commands:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(command[1:], check=True)
            except subprocess.CalledProcessError:
                sys.exit(1)

def main() -> None:

    if sys.platform == "linux":
        install_linux_dependencies()

if __name__ == "__main__":
    main()
