# Basic Usage

This guide covers the fundamental operations of TTS Wrapper.

## Initializing a TTS Engine

Each TTS engine requires a client instance with appropriate credentials:

```python
from tts_wrapper import PollyClient, PollyTTS

# Initialize client with credentials
client = PollyClient(credentials=('region', 'key_id', 'access_key'))
tts = PollyTTS(client)
```

## Basic Text-to-Speech

The simplest way to convert text to speech is using the `speak()` method:

```python
# Basic speech synthesis
tts.speak("Hello, world!")
```

## Saving to File

You can save the synthesized speech to a file:

```python
# Save as WAV file
tts.synth_to_file("Hello world", "output.wav")

# Save as MP3 file
tts.synth_to_file("Hello world", "output.mp3", format="mp3")
```

## Voice Selection

List available voices and select one:

```python
# Get available voices
voices = tts.get_voices()

# Print voice details
for voice in voices:
    print(f"ID: {voice['id']}")
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("voice_id", "en-US")
```

## Speech Properties

Adjust speech properties like rate, volume, and pitch:

```python
# Set speech rate
tts.set_property("rate", "fast")  # Options: x-slow, slow, medium, fast, x-fast

# Set volume
tts.set_property("volume", "80")  # Range: 0-100

# Set pitch
tts.set_property("pitch", "high")  # Options: x-low, low, medium, high, x-high
```

## Next Steps

- Learn about [SSML support](ssml)
- Explore [audio control features](audio-control)
- Check out [streaming capabilities](streaming)
- Understand [callback functionality](callbacks) 