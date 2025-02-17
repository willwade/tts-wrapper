---
sidebar_position: 3
---

# Audio Control

TTS Wrapper provides comprehensive audio playback control features, allowing you to manage speech synthesis playback in real-time.

## Basic Playback Controls

### Starting Playback

```python
# Basic playback
tts.speak("Hello, world!")

# Playback with streaming
tts.speak_streamed("Hello, world!")
```

### Pause and Resume

```python
# Start speaking
tts.speak("This is a long sentence that we will pause in the middle.")

# Pause after 1 second
time.sleep(1)
tts.pause()

# Resume after another second
time.sleep(1)
tts.resume()
```

### Stop Playback

```python
# Stop playback immediately
tts.stop()
```

## Audio Properties

### Volume Control

```python
# Set volume (0-100)
tts.set_property("volume", "75")

# Get current volume
current_volume = tts.get_property("volume")
```

### Speech Rate

```python
# Set speech rate
tts.set_property("rate", "fast")  # x-slow, slow, medium, fast, x-fast
tts.set_property("rate", "150")   # Percentage (100 is normal)
```

### Pitch Control

```python
# Set pitch
tts.set_property("pitch", "high")  # x-low, low, medium, high, x-high
```

## Audio Device Selection

```python
# List available audio devices
import sounddevice as sd
devices = sd.query_devices()
print(devices)

# Set output device by ID
tts.set_output_device(device_id=1)
```

## File Output

### Saving to File

```python
# Save as WAV file
tts.synth_to_file("Hello world", "output.wav")

# Save as MP3
tts.synth_to_file("Hello world", "output.mp3", "mp3")
```

### Streaming with File Output

```python
# Stream audio and save to file simultaneously
tts.speak_streamed("Hello world", save_to_file_path="output.wav")
```

## Advanced Audio Control

### Timed Playback

```python
# Play for specific duration
tts.play(duration=2.0)  # Play for 2 seconds

# Pause for specific duration
tts.pause(duration=1.0)  # Pause for 1 second
```

### Audio Buffer Management

```python
# Load audio into buffer without playing
audio_bytes = tts.synth_to_bytes("Hello world")
tts.load_audio(audio_bytes)

# Play when ready
tts.play()
```

### Stream Setup

```python
# Configure audio stream
tts.setup_stream(
    samplerate=44100,
    channels=1,
    dtype="int16"
)
```

## Event Handling

### Playback Events

```python
def on_start():
    print("Audio started playing")

def on_end():
    print("Audio finished playing")

# Connect event handlers
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)
```

### Cleanup

```python
# Clean up resources when done
tts.cleanup()
```

## Best Practices

1. **Resource Management**
   - Always call `cleanup()` when done
   - Use context managers where possible
   - Release audio resources explicitly

2. **Error Handling**
   ```python
   try:
       tts.speak("Hello world")
   except Exception as e:
       print(f"Playback error: {e}")
   finally:
       tts.cleanup()
   ```

3. **Performance**
   - Use streaming for long text
   - Pre-synthesize repeated phrases
   - Monitor memory usage with large audio files

4. **Device Compatibility**
   - Check device availability before setting
   - Handle device errors gracefully
   - Test across different platforms

## Example: Complete Audio Control

Here's a comprehensive example combining various audio control features:

```python
from tts_wrapper import PollyClient, PollyTTS
import time

# Initialize TTS
client = PollyClient(credentials=('region', 'key_id', 'access_key'))
tts = PollyTTS(client)

# Set up event handlers
def on_start():
    print("Started speaking")

def on_end():
    print("Finished speaking")

tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)

try:
    # Configure audio properties
    tts.set_property("volume", "80")
    tts.set_property("rate", "medium")
    tts.set_property("pitch", "high")

    # Start speaking
    text = "This is a demonstration of audio control features."
    tts.speak_streamed(text)

    # Wait a moment
    time.sleep(1)

    # Pause playback
    tts.pause()
    print("Paused for 2 seconds...")
    time.sleep(2)

    # Resume playback
    tts.resume()
    print("Resumed playback")

    # Wait for completion
    while tts.isplaying:
        time.sleep(0.1)

except Exception as e:
    print(f"Error during playback: {e}")
finally:
    tts.cleanup()
```

## Next Steps

- Learn about [streaming capabilities](streaming) for real-time synthesis
- Explore [SSML support](ssml) for fine-grained speech control
- Check out [callback functionality](callbacks) for speech events 