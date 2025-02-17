---
sidebar_position: 10
---

# SAPI TTS

SAPI (Microsoft Speech API) provides native text-to-speech capabilities on Windows systems. It offers access to installed system voices with basic SSML support.

## Platform Support

SAPI is only available on Windows systems:

```python
from tts_wrapper import SAPIClient, SAPITTS

# Initialize client and TTS
client = SAPIClient()  # No credentials needed
tts = SAPITTS(client)
```

## Features

### Voice Selection
List and select from installed Windows voices:

```python
# Get list of available voices
voices = tts.get_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("Microsoft David Desktop")
```

### SSML Support
SAPI provides basic SSML support through Windows Speech API:

```python
ssml_text = """
<speak>
    Hello <break time="500ms"/> World!
    <prosody rate="slow" pitch="high">
        This is a test of SSML features.
    </prosody>
</speak>
"""
tts.speak(ssml_text)
```

### Voice Properties
Adjust synthesis properties:

```python
# Set speech rate (-10 to 10)
tts.set_property("rate", "0")  # Default is 0

# Set volume (0-100)
tts.set_property("volume", "100")

# Set pitch (-10 to 10)
tts.set_property("pitch", "0")
```

### Word Timing
Get timing information for each word:

```python
def word_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: {word}")
    print(f"Start Time: {start_time:.2f}s")
    print(f"Duration: {duration:.2f}s")

# Connect the callback
tts.connect("started-word", word_callback)

# Speak with word timing
tts.speak("This will trigger word timing callbacks")
```

### File Output
Save synthesized speech to file:

```python
# Save as WAV
tts.synth_to_file("Hello world", "output.wav")
```

## Best Practices

1. **Performance**
   - Reuse client instances
   - Use appropriate speech rate for your needs
   - Consider caching frequently used phrases

2. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "SAPI not available" in str(e):
           print("SAPI is not available on this system")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Windows only
- Basic SSML support
- Voice selection limited to installed Windows voices
- No custom voice support
- Performance may vary by system
- Some features require specific Windows versions

## Audio Settings

### Sample Rate
SAPI uses system-defined sample rates:

```python
# Check the current audio rate
print(f"Audio rate: {tts.audio_rate}")
```

### Audio Format
- Channels: Mono (1 channel)
- Sample Width: 16-bit
- Format: PCM

```python
print(f"Channels: {tts.channels}")        # 1
print(f"Sample width: {tts.sample_width}") # 2 (16-bit)
```

## Voice Types

### System Voices
Windows includes several built-in voices:
```python
# Common system voices
tts.set_voice("Microsoft David Desktop")  # Male voice
tts.set_voice("Microsoft Zira Desktop")   # Female voice
```

### Third-Party Voices
SAPI can use additional installed voices:
```python
# List all available voices including third-party
voices = tts.get_voices()
for voice in voices:
    print(f"Available voice: {voice['name']}")
```

## Language Support

SAPI supports multiple languages through installed Windows language packs:

```python
# List voices for a specific language
voices = tts.get_voices()
spanish_voices = [v for v in voices if "es" in v["language_codes"][0]]
for voice in spanish_voices:
    print(f"Spanish voice: {voice['name']}")
```

## Additional Resources

- [Microsoft SAPI Documentation](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723627(v=vs.85))
- [Windows TTS Voice Installation Guide](https://support.microsoft.com/en-us/windows/download-language-pack-for-speech-24d06ef3-ca09-ddcc-70a0-63606fd16394)
- [SAPI SSML Reference](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723628(v=vs.85))

## Next Steps

- Learn about [SSML support](../guides/ssml)
- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks) 