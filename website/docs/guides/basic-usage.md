# Basic Usage

This guide covers the fundamental operations of TTS Wrapper.

## Initializing a TTS Engine

Each TTS engine is initialized with appropriate credentials:

```python
from tts_wrapper import PollyClient

# Initialize client with credentials
client = PollyClient(credentials=('region', 'key_id', 'access_key'))
```

## Basic Text-to-Speech

The simplest way to convert text to speech is using the `speak()` method:

```python
# Basic speech synthesis
client.speak("Hello, world!")
```

## Saving to File

You can save the synthesized speech to a file:

```python
# Save as WAV file
client.synth_to_file("Hello world", "output.wav")

# Save as MP3 file
client.synth_to_file("Hello world", "output.mp3", format="mp3")
```

## Silent Audio Synthesis

The `synthesize()` method provides silent audio synthesis without playback - perfect for applications that need audio data without immediate playback:

```python
# Get complete audio data (default)
audio_bytes = client.synthesize("Hello world")

# Get streaming audio data for real-time processing
audio_stream = client.synthesize("Hello world", streaming=True)
for chunk in audio_stream:
    # Process each audio chunk as it's generated
    process_audio_chunk(chunk)

# Use with specific voice
audio_bytes = client.synthesize("Hello world", voice_id="en-US-JennyNeural")
```

**Use cases for silent synthesis:**
- SAPI bridges and accessibility tools
- Audio processing pipelines
- Batch audio generation
- Real-time audio streaming applications
- Custom audio players

## Voice Selection

List available voices and select one:

```python
# Get available voices
voices = client.get_voices()

# Print voice details
for voice in voices:
    print(f"ID: {voice['id']}")
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
client.set_voice("voice_id", "en-US")
```

## Speech Properties

Adjust speech properties like rate, volume, and pitch:

```python
# Set speech rate
client.set_property("rate", "fast")  # Options: x-slow, slow, medium, fast, x-fast

# Set volume
client.set_property("volume", "80")  # Range: 0-100

# Set pitch
client.set_property("pitch", "high")  # Options: x-low, low, medium, high, x-high
```

## Getting Audio Bytes

Both `speak()` and `speak_streamed()` methods can return audio bytes for custom processing:

```python
# Get audio bytes from speak() method
audio_bytes = client.speak("Hello world", return_bytes=True, wait_for_completion=False)

# Get audio bytes from speak_streamed() method
audio_bytes = client.speak_streamed("Hello world", return_bytes=True, wait_for_completion=False)

# Process the audio bytes
if audio_bytes:
    print(f"Received {len(audio_bytes)} bytes of audio data")
    # Use bytes for custom processing, streaming, etc.
```

### Use Cases for Audio Bytes

- **No audio playback**: Perfect when you don't have audio hardware or the `controlaudio` extra
- **Custom audio processing**: Apply effects, change format, or integrate with other audio libraries
- **Streaming applications**: Send audio data over network or to custom playback systems
- **Memory-efficient processing**: Work with audio data without temporary files

### Combined Operations

You can also get bytes while saving to file:

```python
# Get bytes AND save to file simultaneously
audio_bytes = client.speak_streamed(
    "Hello world",
    return_bytes=True,
    save_to_file_path="output.wav"
)
```

## Next Steps

- Learn about [SSML support](ssml)
- Explore [audio control features](audio-control)
- Check out [streaming capabilities](streaming)
- Understand [callback functionality](callbacks)