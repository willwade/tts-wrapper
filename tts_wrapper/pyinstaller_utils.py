"""
PyInstaller utilities for tts-wrapper.

This module provides helper functions and information for creating
PyInstaller builds that include all necessary audio dependencies.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_sounddevice_binaries() -> list[tuple[str, str]]:
    """
    Get list of sounddevice binary files that need to be included in PyInstaller builds.

    Returns:
        List of (source_path, destination_path) tuples for PyInstaller --add-binary
    """
    binaries = []

    try:
        import sounddevice
        sounddevice_path = Path(sounddevice.__file__).parent

        # Look for PortAudio binaries
        portaudio_path = sounddevice_path / '_sounddevice_data' / 'portaudio-binaries'
        if portaudio_path.exists():
            for dll_file in portaudio_path.glob('*.dll'):
                binaries.append((str(dll_file), '.'))

        # Look for DLLs in main sounddevice directory
        for dll_file in sounddevice_path.glob('*.dll'):
            binaries.append((str(dll_file), '.'))

    except ImportError:
        pass

    return binaries


def get_pyaudio_binaries() -> list[tuple[str, str]]:
    """
    Get list of PyAudio binary files that need to be included in PyInstaller builds.

    Returns:
        List of (source_path, destination_path) tuples for PyInstaller --add-binary
    """
    binaries = []

    try:
        import pyaudio
        pyaudio_path = Path(pyaudio.__file__).parent

        # Look for DLLs and .pyd files in PyAudio directory
        for file_pattern in ['*.dll', '*.pyd']:
            for binary_file in pyaudio_path.glob(file_pattern):
                binaries.append((str(binary_file), '.'))

        # Specifically look for _portaudio.pyd
        portaudio_pyd = pyaudio_path / '_portaudio.pyd'
        if portaudio_pyd.exists():
            binaries.append((str(portaudio_pyd), '.'))

    except ImportError:
        pass

    return binaries


def get_azure_speech_binaries() -> list[tuple[str, str]]:
    """
    Get list of Azure Speech SDK binary files.

    Returns:
        List of (source_path, destination_path) tuples for PyInstaller --add-binary
    """
    binaries = []

    try:
        import azure.cognitiveservices.speech
        azure_path = Path(azure.cognitiveservices.speech.__file__).parent

        # Look for all DLLs in Azure Speech SDK directory
        for dll_file in azure_path.rglob('*.dll'):
            binaries.append((str(dll_file), '.'))

    except ImportError:
        pass

    return binaries


def get_windows_system_dlls() -> list[tuple[str, str]]:
    """
    Get list of Windows system DLLs commonly needed for audio applications.

    Returns:
        List of (source_path, destination_path) tuples for PyInstaller --add-binary
    """
    binaries = []

    if sys.platform != "win32":
        return binaries

    import os
    windows_system32 = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'System32'

    common_audio_dlls = [
        'winmm.dll',
        'dsound.dll',
        'AudioEng.dll',
        'AudioSes.dll',
        'AUDIOKSE.dll',
        'mf.dll',
        'mfplat.dll',
        'MMDevAPI.dll',
    ]

    for dll_name in common_audio_dlls:
        dll_path = windows_system32 / dll_name
        if dll_path.exists():
            binaries.append((str(dll_path), '.'))

    return binaries


def get_all_audio_binaries(include_system_dlls: bool = False) -> list[tuple[str, str]]:
    """
    Get all audio-related binaries needed for PyInstaller builds.

    Args:
        include_system_dlls: Whether to include Windows system DLLs (can be risky)

    Returns:
        List of (source_path, destination_path) tuples for PyInstaller --add-binary
    """
    binaries = []
    binaries.extend(get_sounddevice_binaries())
    binaries.extend(get_pyaudio_binaries())
    binaries.extend(get_azure_speech_binaries())

    if include_system_dlls:
        binaries.extend(get_windows_system_dlls())

    return binaries


def generate_pyinstaller_command(
    script_path: str,
    output_name: Optional[str] = None,
    additional_options: Optional[list[str]] = None,
    include_system_dlls: bool = False,
    comprehensive: bool = True
) -> str:
    """
    Generate a PyInstaller command with all necessary audio dependencies.

    Args:
        script_path: Path to the main Python script
        output_name: Name for the output executable (optional)
        additional_options: Additional PyInstaller options (optional)
        include_system_dlls: Whether to include Windows system DLLs (can be risky)
        comprehensive: Whether to include comprehensive collection options

    Returns:
        Complete PyInstaller command string
    """
    cmd_parts = ['pyinstaller']

    # Add output name if specified
    if output_name:
        cmd_parts.extend(['--name', output_name])

    # Add audio binaries
    for src, dst in get_all_audio_binaries(include_system_dlls):
        cmd_parts.extend(['--add-binary', f'"{src};{dst}"'])

    # Add hook directory
    hook_dir = Path(__file__).parent / '_pyinstaller'
    if hook_dir.exists():
        cmd_parts.extend(['--additional-hooks-dir', str(hook_dir)])

    # Add common options for TTS apps
    cmd_parts.extend([
        '--collect-binaries', 'sounddevice',
        '--collect-data', 'sounddevice',
        '--hidden-import', 'sounddevice',
        '--hidden-import', 'numpy',
        '--hidden-import', 'soundfile',
    ])

    # Add PyAudio if available
    try:
        import pyaudio
        cmd_parts.extend([
            '--collect-binaries', 'pyaudio',
            '--hidden-import', 'pyaudio',
        ])
    except ImportError:
        pass

    # Add Azure Speech SDK if available
    try:
        import azure.cognitiveservices.speech
        cmd_parts.extend([
            '--collect-binaries', 'azure.cognitiveservices.speech',
            '--hidden-import', 'azure.cognitiveservices.speech',
        ])
    except ImportError:
        pass

    # Add comprehensive collection if requested
    if comprehensive:
        cmd_parts.extend([
            '--collect-all', 'language_data',
            '--collect-all', 'language_tags',
            '--collect-all', 'comtypes',
        ])

    # Add additional options
    if additional_options:
        cmd_parts.extend(additional_options)

    # Add script path
    cmd_parts.append(script_path)

    return ' '.join(cmd_parts)


def get_hooks_dir() -> str:
    """Get the path to the TTS-wrapper PyInstaller hooks directory."""
    return str(Path(__file__).parent / '_pyinstaller')


def get_pyinstaller_command(script_name: str, app_name: Optional[str] = None) -> str:
    """
    Get a ready-to-use PyInstaller command for your script.

    Args:
        script_name: Name of your Python script (e.g., 'my_app.py')
        app_name: Name for the executable (optional, defaults to script name)

    Returns:
        Complete PyInstaller command string
    """
    if app_name is None:
        app_name = Path(script_name).stem

    # Check what's installed and choose the best approach
    has_optional_deps = False
    try:
        import azure.cognitiveservices.speech
        has_optional_deps = True
    except ImportError:
        pass

    try:
        import pyaudio
        has_optional_deps = True
    except ImportError:
        pass

    if has_optional_deps:
        # Use hooks for comprehensive support
        hook_dir = get_hooks_dir()
        return f'pyinstaller --additional-hooks-dir "{hook_dir}" --name "{app_name}" {script_name}'
    # Use simple approach for basic setup
    return f'pyinstaller --collect-binaries sounddevice --name "{app_name}" {script_name}'


def print_pyinstaller_help():
    """Print helpful information for PyInstaller builds."""
    print("=" * 70)
    print(" TTS-Wrapper PyInstaller Build Guide")
    print("=" * 70)

    print("\n📋 QUICK START - Copy and paste one of these commands:")
    print("=" * 50)

    # Check what's installed and recommend the best approach
    has_azure = False
    has_pyaudio = False

    try:
        import azure.cognitiveservices.speech
        has_azure = True
    except ImportError:
        pass

    try:
        import pyaudio
        has_pyaudio = True
    except ImportError:
        pass

    if has_azure or has_pyaudio:
        print("\n🎯 RECOMMENDED (you have optional dependencies):")
        hook_dir = get_hooks_dir()
        print(f'   pyinstaller --additional-hooks-dir "{hook_dir}" your_script.py')
        print("\n   OR generate a command for your specific script:")
        print('   python -c "from tts_wrapper.pyinstaller_utils import get_pyinstaller_command; print(get_pyinstaller_command(\'your_script.py\', \'YourApp\'))"')
    else:
        print("\n🎯 RECOMMENDED (basic setup):")
        print("   pyinstaller --collect-binaries sounddevice your_script.py")

    print("\n💡 ALTERNATIVE (always works):")
    print("   pyinstaller --collect-binaries sounddevice your_script.py")
    print("   (Use this if the hooks don't work or you only need basic audio)")

    print("\n" + "=" * 70)
    print(" DETAILED INFORMATION")
    print("=" * 70)

    print("\n1. Optional Dependencies Detected:")
    optional_deps = []
    try:
        import pyaudio
        optional_deps.append("✅ PyAudio (controlaudio extra)")
    except ImportError:
        optional_deps.append("❌ PyAudio (controlaudio extra) - not installed")

    try:
        import azure.cognitiveservices.speech
        optional_deps.append("✅ Azure Speech SDK (microsoft extra)")
    except ImportError:
        optional_deps.append("❌ Azure Speech SDK (microsoft extra) - not installed")

    try:
        import google.cloud.texttospeech
        optional_deps.append("✅ Google Cloud TTS (google extra)")
    except ImportError:
        optional_deps.append("❌ Google Cloud TTS (google extra) - not installed")

    try:
        import boto3
        optional_deps.append("✅ AWS Polly (aws extra)")
    except ImportError:
        optional_deps.append("❌ AWS Polly (aws extra) - not installed")

    for dep in optional_deps:
        print(f"   {dep}")

    print("\n2. Required Audio Binaries:")
    binaries = get_all_audio_binaries()
    if binaries:
        print(f"   Found {len(binaries)} binary files:")
        for src, _dst in binaries[:5]:  # Show first 5
            print(f"   • {os.path.basename(src)}")
        if len(binaries) > 5:
            print(f"   • ... and {len(binaries) - 5} more")
    else:
        print("   No audio binaries found")

    print("\n3. Hooks Directory Path:")
    hook_dir = get_hooks_dir()
    if Path(hook_dir).exists():
        print(f"   {hook_dir}")
        print("   (Use this path with --additional-hooks-dir)")
    else:
        print("   TTS-Wrapper hooks not found")

    print("\n4. Generated Commands:")

    print("\n   Basic command:")
    basic_cmd = generate_pyinstaller_command("your_script.py")
    # Truncate very long commands for readability
    if len(basic_cmd) > 100:
        print(f"   {basic_cmd[:97]}...")
        print("   (Run the utility command above to get the full command)")
    else:
        print(f"   {basic_cmd}")

    print("\n5. Troubleshooting:")
    print("   • Ensure sounddevice is installed (core dependency)")
    print("   • Install optional extras: pip install py3-tts-wrapper[controlaudio,microsoft]")
    print("   • Use --debug=all to see what PyInstaller is collecting")
    print("   • Test the frozen build on a clean machine")
    print("   • For Azure: ensure Visual C++ Redistributables are installed")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_pyinstaller_help()
