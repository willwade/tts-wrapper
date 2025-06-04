"""
PyInstaller hook for sounddevice package.

This hook ensures that PortAudio DLLs are included in the frozen build.
This is a backup in case the standard sounddevice hook doesn't work.
"""

import os

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect sounddevice data files and binaries
datas = collect_data_files('sounddevice')
binaries = collect_dynamic_libs('sounddevice')

# Specifically handle PortAudio binaries
try:
    import sounddevice
    sounddevice_path = os.path.dirname(sounddevice.__file__)

    # Add PortAudio binaries from _sounddevice_data
    portaudio_data_path = os.path.join(sounddevice_path, '_sounddevice_data')
    if os.path.exists(portaudio_data_path):
        # Recursively add all files from _sounddevice_data
        for root, _dirs, files in os.walk(portaudio_data_path):
            for file in files:
                src_path = os.path.join(root, file)
                # Calculate relative path from sounddevice root
                rel_path = os.path.relpath(src_path, sounddevice_path)
                dest_dir = os.path.dirname(rel_path)

                if file.endswith('.dll'):
                    # Put DLLs in their original relative path
                    binaries.append((src_path, dest_dir))
                else:
                    # Put other files in their relative paths
                    datas.append((src_path, os.path.join('sounddevice', dest_dir)))

    # Also check for DLLs directly in sounddevice directory
    for file in os.listdir(sounddevice_path):
        if file.endswith('.dll'):
            dll_path = os.path.join(sounddevice_path, file)
            binaries.append((dll_path, '.'))

except ImportError:
    pass

# Hidden imports
hiddenimports = [
    'sounddevice._sounddevice',
    'cffi',
    'numpy',
]
