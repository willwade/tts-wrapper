---
sidebar_position: 2
---

# Installation

This guide will help you install TTS Wrapper and its dependencies. The library is published on PyPI as `py3-tts-wrapper` but installs as `tts_wrapper` in your Python environment.

### Basic Installation

Install the core package with pip:

```bash
pip install py3-tts-wrapper
```

### Installation with Specific Engines

You can install TTS Wrapper with support for specific engines:

```bash
# Install with all cloud service engines
pip install "py3-tts-wrapper[google,watson,polly,microsoft,elevenlabs,witai,playht]"

# Install with local engines
pip install "py3-tts-wrapper[espeak,sapi,sherpaonnx,avsynth]"

# Install with specific engines (example)
pip install "py3-tts-wrapper[google,microsoft,sapi,sherpaonnx]"
```

Note: On macOS/zsh, you need to use quotes around the package name and extras.

:::important
Note: If you want to control audio playback (e.g., pause and resume functionality), you need to install the `controllable` extra. Without this extra, playback control features will not work.
:::

### Available Extras

| Extra         | Description                           | Additional Dependencies |
|--------------|---------------------------------------|------------------------|
| google       | Google Cloud TTS support              | google-cloud-texttospeech |
| watson       | IBM Watson TTS support                | ibm-watson, websocket-client |
| polly        | AWS Polly support                     | boto3 |
| microsoft    | Microsoft Azure TTS support           | azure-cognitiveservices-speech |
| elevenlabs   | ElevenLabs TTS support               | - |
| witai        | Wit.ai TTS support                    | - |
| playht       | Play.HT TTS support                   | - |
| sapi         | Windows SAPI support                  | comtypes (Windows only) |
| sherpaonnx   | Sherpa-ONNX support                  | sherpa-onnx |
| googletrans  | Google Translate TTS support          | gTTS |
| controlaudio | Advanced audio control                | pyaudio |
| espeak       | eSpeak-NG support                    | - |
| avsynth      | macOS AVSpeechSynthesizer support    | - |
| uwp          | Windows UWP speech support           | winrt-runtime (Windows only) |

## System Requirements

- Python 3.10 or higher
- Operating system: Windows, macOS, or Linux
- System dependencies (varies by platform)

## System Dependencies

### Linux (Ubuntu/Debian)

```bash
# Core dependencies
sudo apt-get update
sudo apt-get install -y portaudio19-dev

# For eSpeak support
sudo apt-get install -y espeak-ng

# For PicoTTS support (optional)
sudo apt-get install -y libttspico-utils

# For audio playback
sudo apt-get install -y ffmpeg
```

### macOS

Using [Homebrew](https://brew.sh):

```bash
# Core dependencies
brew install portaudio

# For eSpeak support
brew install espeak-ng

# For audio playback
brew install ffmpeg
```

### Windows

- Download and install [eSpeak-NG](https://github.com/espeak-ng/espeak-ng/releases) if you plan to use eSpeak
- SAPI and UWP engines use built-in Windows components


## Troubleshooting

### Common Issues

1. **PortAudio errors**:
   - Ensure you've installed the PortAudio development libraries
   - On Linux: `sudo apt-get install portaudio19-dev`
   - On macOS: `brew install portaudio`

2. **eSpeak not found**:
   - Verify eSpeak-NG is installed and in your system PATH
   - On Linux: `sudo apt-get install espeak-ng`
   - On macOS: `brew install espeak-ng`
   - On Windows: Install from the official website

3. **SSL Certificate Verification**:
   - For Watson TTS, if you encounter SSL issues, you can disable verification:
     ```python
     client = WatsonClient(credentials=(...), disableSSLVerification=True)
     ```

4. **Windows SAPI Issues**:
   - Ensure you're running Python with appropriate permissions
   - Verify the `comtypes` package is installed

### Getting Help

If you encounter any issues:

1. Check the [GitHub Issues](https://github.com/willwade/tts-wrapper/issues) for similar problems
2. Ensure all system dependencies are correctly installed
3. Verify you're using a supported Python version (3.10 or higher)
4. Create a new issue with detailed information about your setup and the error

## Next Steps

Once you have TTS Wrapper installed, check out the [Basic Usage](guides/basic-usage) guide to learn how to use the library. 