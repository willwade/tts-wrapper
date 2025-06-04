"""
PyInstaller hook for tts-wrapper package.

This hook automatically detects and includes all necessary dependencies
for tts-wrapper based on what optional extras are installed.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect basic tts_wrapper data and binaries
datas = collect_data_files('tts_wrapper')
binaries = collect_dynamic_libs('tts_wrapper')

# Basic hidden imports that are always needed
hiddenimports = [
    'sounddevice',
    'soundfile',
    'numpy',
    'langcodes',
    'language_data',
    'marisa_trie',
]

# Use our pyinstaller_utils to get all binaries
try:
    from tts_wrapper.pyinstaller_utils import get_all_audio_binaries
    audio_binaries = get_all_audio_binaries(include_system_dlls=False)
    binaries.extend(audio_binaries)
except ImportError:
    # Fallback if pyinstaller_utils isn't available
    pass

# Conditionally add PyAudio support (controlaudio extra)
try:
    import pyaudio
    hiddenimports.append('pyaudio')

    # Add PyAudio binaries
    pyaudio_path = os.path.dirname(pyaudio.__file__)
    for file in os.listdir(pyaudio_path):
        if file.endswith(('.dll', '.pyd')):
            dll_path = os.path.join(pyaudio_path, file)
            binaries.append((dll_path, '.'))

except ImportError:
    pass

# Conditionally add Azure Speech SDK support (microsoft extra)
try:
    import azure.cognitiveservices.speech
    hiddenimports.extend([
        'azure.cognitiveservices.speech',
        'azure.cognitiveservices.speech.audio',
        'azure.core',
        'azure.common',
    ])

    # Add Azure Speech SDK binaries
    azure_path = os.path.dirname(azure.cognitiveservices.speech.__file__)
    for root, _dirs, files in os.walk(azure_path):
        for file in files:
            if file.endswith('.dll'):
                dll_path = os.path.join(root, file)
                binaries.append((dll_path, '.'))

except ImportError:
    pass

# Conditionally add Google Cloud TTS support (google extra)
try:
    import google.cloud.texttospeech
    hiddenimports.extend([
        'google.cloud.texttospeech',
        'google.auth',
        'google.api_core',
        'grpc',
    ])
except ImportError:
    pass

# Conditionally add AWS Polly support (aws extra)
try:
    import boto3
    hiddenimports.extend([
        'boto3',
        'botocore',
    ])
except ImportError:
    pass

# Conditionally add OpenAI support (openai extra)
try:
    import openai
    hiddenimports.extend([
        'openai',
        'httpx',
    ])
except ImportError:
    pass

# Conditionally add ElevenLabs support (elevenlabs extra)
try:
    import elevenlabs
    hiddenimports.append('elevenlabs')
except ImportError:
    pass

# Conditionally add gTTS support (gtts extra)
try:
    import gtts
    hiddenimports.append('gtts')
except ImportError:
    pass

# Conditionally add IBM Watson support (watson extra)
try:
    import ibm_watson
    hiddenimports.extend([
        'ibm_watson',
        'websocket',
    ])
except ImportError:
    pass

# Conditionally add Sherpa ONNX support (sherpa extra)
try:
    import sherpa_onnx
    hiddenimports.append('sherpa_onnx')
except ImportError:
    pass

# Windows-specific TTS engines
if sys.platform == "win32":
    try:
        import comtypes
        hiddenimports.extend([
            'comtypes',
            'comtypes.client',
        ])
    except ImportError:
        pass

    # UWP/WinRT support
    try:
        import winrt
        hiddenimports.append('winrt')
    except ImportError:
        pass

# macOS-specific TTS engines
if sys.platform == "darwin":
    # AVSpeechSynthesizer support is built-in, no extra imports needed
    pass

# Linux-specific TTS engines
if sys.platform.startswith("linux"):
    # eSpeak support is system-level, no extra imports needed
    pass

# Filter out any imports that aren't actually available
available_hiddenimports = []
for module in hiddenimports:
    try:
        __import__(module)
        available_hiddenimports.append(module)
    except ImportError:
        pass

hiddenimports = available_hiddenimports
