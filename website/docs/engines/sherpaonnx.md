---
sidebar_position: 13
---

# Sherpa-ONNX TTS

Sherpa-ONNX is an open-source speech toolkit that provides offline text-to-speech capabilities using ONNX models. It's designed for applications requiring local, privacy-focused speech synthesis.

## Platform Support

Sherpa-ONNX works on all major platforms (Linux, macOS, Windows) and requires no internet connection:

```python
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS

# Initialize client with optional model paths
client = SherpaOnnxClient(
    model_path=None,  # Uses default model if not specified
    tokens_path=None  # Uses default tokens if not specified
)
tts = SherpaOnnxTTS(client)
```

## Features

### Voice Selection
Select from available voices (based on installed models):

```python
# Get list of available voices
voices = tts.get_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print("---")

# Set a voice using ISO code
iso_code = "eng"  # Example ISO code
tts.set_voice(iso_code)
```

### Streaming
Supports real-time audio streaming:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Audio Playback
Direct audio playback with callback support:

```python
def play_audio_callback(outdata, frames, time, status):
    """Handle audio playback."""
    if status:
        print(f"Audio callback status: {status}")

# Set up audio stream with callback
tts.setup_stream(
    samplerate=22050,
    channels=1,
    dtype="float32"
)
```

### File Output
Save synthesized speech to file:

```python
# Save as WAV
tts.synth_to_file("Hello world", "output.wav")

# Save with specific format
tts.synth_to_file("Hello world", "output.wav", "wav")
```

## Best Practices

1. **Performance**
   - Reuse client instances
   - Use appropriate model size for your needs
   - Consider caching frequently used phrases
   - Monitor memory usage with large models

2. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Model not found" in str(e):
           print("Check model path configuration")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- No SSML support
- Limited voice selection (depends on available models)
- No custom voice support
- Performance depends on hardware
- Model size can be significant
- Basic prosody control

## Audio Settings

### Sample Rate
Sherpa-ONNX typically uses a 22050 Hz sample rate:

```python
# Check the current audio rate
print(f"Audio rate: {tts.audio_rate}")  # 22050
```

### Audio Format
- Channels: Mono (1 channel)
- Sample Width: 16-bit or 32-bit float
- Format: PCM or float

```python
# Configure audio settings
tts.setup_stream(
    samplerate=22050,
    channels=1,
    dtype="float32"  # or "int16" for PCM
)
```

## Model Management

### Default Models
The wrapper includes default models for basic usage:

```python
# Use default models
client = SherpaOnnxClient()
```

### Custom Models
Use your own ONNX models:

```python
# Use custom models
client = SherpaOnnxClient(
    model_path="path/to/model.onnx",
    tokens_path="path/to/tokens.txt"
)
```

## Language Support

Support depends on available models:

```python
# List available languages
voices = tts.get_voices()
languages = set(lang for voice in voices 
               for lang in voice["language_codes"])
print(f"Available languages: {languages}")
```

## Additional Resources

- [Sherpa-ONNX Repository](https://github.com/k2-fsa/sherpa-onnx)
- [Model Zoo](https://github.com/k2-fsa/sherpa-onnx/blob/master/docs/source/model-zoo/index.rst)
- [ONNX Runtime Documentation](https://onnxruntime.ai/)

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Learn about [audio control features](../guides/audio-control) 