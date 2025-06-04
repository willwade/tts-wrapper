# PyInstaller Guide for TTS-Wrapper

Creating executable files from your TTS-wrapper applications is easy with PyInstaller.

## Quick Start

### 🎯 Get Your Command (Recommended)

Run this command to get a PyInstaller command tailored to your setup:

```bash
python -c "from tts_wrapper.pyinstaller_utils import print_pyinstaller_help; print_pyinstaller_help()"
```

This will show you exactly what to run based on what TTS engines you have installed.

### 🚀 Simple Universal Command

If you just want something that works:

```bash
pyinstaller --collect-binaries sounddevice your_script.py
```

This works for basic TTS functionality but may miss some optional dependencies like Azure Speech SDK.

## Examples

### Basic TTS App
```python
# my_tts_app.py
from tts_wrapper import eSpeakTTS

def main():
    tts = eSpeakTTS()
    tts.speak("Hello from PyInstaller!")

if __name__ == "__main__":
    main()
```

**Build command:**
```bash
pyinstaller --collect-binaries sounddevice my_tts_app.py
```

### Azure TTS App
```python
# azure_tts_app.py
from tts_wrapper import MicrosoftTTS

def main():
    tts = MicrosoftTTS(credentials=('your_key', 'your_region'))
    tts.speak("Hello from Azure TTS!")

if __name__ == "__main__":
    main()
```

**Build command (get the exact command):**
```bash
python -c "from tts_wrapper.pyinstaller_utils import get_pyinstaller_command; print(get_pyinstaller_command('azure_tts_app.py', 'AzureTTSApp'))"
```

## Troubleshooting

### "Device unavailable" Error
If your built executable shows audio device errors, this is usually because:
- The target machine has no audio drivers
- Running in a headless/remote environment
- Audio services are disabled

**Solution:** The TTS-wrapper automatically falls back to silent operation and file saving still works.

### Missing DLLs
If you get DLL missing errors:
1. Use the utility command to get the full command with all binaries
2. Make sure you have the optional extras installed: `pip install py3-tts-wrapper[microsoft,controlaudio]`
3. Test on a clean machine without Python installed

### Large Executable Size
To reduce size:
- Use `--onedir` instead of `--onefile`
- Only install the TTS engines you actually use
- Consider using `--exclude-module` for unused engines

## Advanced Usage

### Custom Build Options
```bash
# Get a command with custom options
python -c "
from tts_wrapper.pyinstaller_utils import generate_pyinstaller_command
cmd = generate_pyinstaller_command(
    'my_app.py', 
    'MyApp',
    ['--onedir', '--noconsole', '--clean'],
    include_system_dlls=False
)
print(cmd)
"
```

### Manual Binary Addition
If automatic detection fails, you can manually add binaries:
```bash
python -c "
from tts_wrapper.pyinstaller_utils import get_all_audio_binaries
for src, dst in get_all_audio_binaries():
    print(f'--add-binary \"{src};{dst}\"')
"
```

## Platform Notes

### Windows
- Ensure Visual C++ Redistributables are installed on target machines
- Test both with and without audio devices
- Consider including system audio DLLs for maximum compatibility

### Linux
- Install system audio libraries: `sudo apt-get install portaudio19-dev`
- May need additional ALSA/PulseAudio libraries

### macOS
- PortAudio should be included automatically
- Test on different macOS versions

## Getting Help

If you're still having issues:

1. **Run the diagnostic:**
   ```bash
   python -c "from tts_wrapper.pyinstaller_utils import print_pyinstaller_help; print_pyinstaller_help()"
   ```

2. **Check PyInstaller logs:**
   ```bash
   pyinstaller --debug=all your_script.py
   ```

3. **Test on a clean machine** without Python/development tools installed

4. **Open an issue** on the [tts-wrapper GitHub repository](https://github.com/willwade/tts-wrapper) with:
   - Your PyInstaller command
   - The error message
   - Output from the diagnostic command
