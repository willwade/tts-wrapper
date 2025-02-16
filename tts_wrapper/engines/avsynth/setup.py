import os
import platform
import subprocess
from pathlib import Path

def build_swift_bridge():
    """Build the Swift bridge during package installation."""
    # Only build on macOS
    if platform.system() != "Darwin":
        return
    
    try:
        # Check if Swift is available
        subprocess.run(["swift", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Swift is not installed. AVSynth will not be available.")
        return
    
    try:
        # Get the directory containing this script
        package_dir = Path(__file__).parent
        
        # Build the Swift package
        print("Building Swift bridge for AVSynth...")
        subprocess.run(
            ["swift", "build"],
            cwd=package_dir,
            check=True,
            capture_output=True
        )
        
        # Copy the built executable to the package directory
        build_dir = package_dir / ".build/debug"
        if (build_dir / "SpeechBridge").exists():
            # Copy to package directory for distribution
            (package_dir / "SpeechBridge").write_bytes(
                (build_dir / "SpeechBridge").read_bytes()
            )
            print("Swift bridge built successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build Swift bridge: {e.stderr}")
    except Exception as e:
        print(f"Error building Swift bridge: {e}")

if __name__ == "__main__":
    build_swift_bridge() 