---
sidebar_position: 11
---

# AVSynth TTS

AVSynth provides native text-to-speech capabilities on macOS using the AVSpeechSynthesizer framework. It offers high-quality system voices with real-time streaming and word timing support.

## Platform Support

AVSynth is only available on macOS systems. The engine will not be available on other platforms.

```python
from tts_wrapper import AVSynthClient, AVSynthTTS

# Initialize client and TTS
client = AVSynthClient()  # No credentials needed
tts = AVSynthTTS(client)
```

## Features

### Voice Selection
List and select from available system voices:

```python
# Get list of available voices
voices = tts.get_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("com.apple.voice.compact.en-US.Samantha")
```

### Streaming
Supports real-time audio streaming with low latency:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Voice Properties
Adjust synthesis properties:

```python
# Set speech rate (0-100, default is 50)
tts.set_property("rate", "50")

# Set volume (0-100)
tts.set_property("volume", "100")

# Set pitch (0.5-2.0)
tts.set_property("pitch", "1.0")
```

### Word Timing
Get precise timing information for each word:

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
   - Use streaming for real-time applications
   - Set appropriate audio rate for your needs

2. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "AVSpeechSynthesizer" in str(e):
           print("Speech synthesis error")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- macOS only
- Limited SSML support (tags converted to native commands)
- Voice selection limited to installed system voices
- No custom voice support
- Some features may require newer macOS versions

## Audio Settings

### Sample Rate
AVSynth uses a default sample rate of 22050 Hz for more natural speech:

```python
# The audio rate is set automatically but can be checked
print(f"Audio rate: {tts.audio_rate}")  # 22050
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

### Compact Voices
Standard system voices with good quality:
```python
tts.set_voice("com.apple.voice.compact.en-US.Samantha")
```

### Premium Voices
Higher quality voices (if installed):
```python
tts.set_voice("com.apple.voice.premium.en-US.Samantha")
```

## Language Support

AVSynth supports multiple languages based on installed system voices:

```python
# List voices for a specific language
voices = tts.get_voices()
french_voices = [v for v in voices if "fr" in v["language_codes"][0]]
for voice in french_voices:
    print(f"French voice: {voice['name']}")
```

## Additional Resources

- [AVSpeechSynthesizer Documentation](https://developer.apple.com/documentation/avfoundation/avspeechsynthesizer)
- [macOS Voice Guide](https://support.apple.com/guide/mac-help/change-the-voice-your-mac-uses-to-speak-text-mchlp2290/mac)

## Next Steps

- Learn about [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Explore [audio control features](../guides/audio-control) 