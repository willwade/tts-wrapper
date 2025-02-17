---
sidebar_position: 6
---

# ElevenLabs TTS

ElevenLabs provides high-quality neural text-to-speech with support for voice cloning and customization. It offers some of the most natural-sounding voices available.

## Authentication

ElevenLabs requires an API key:

```python
from tts_wrapper import ElevenLabsTTS, ElevenLabsClient

client = ElevenLabsClient(credentials='your_api_key')
tts = ElevenLabsTTS(client)
```

:::tip
Use environment variables for secure credential management:
```python
import os

client = ElevenLabsClient(credentials=os.getenv('ELEVENLABS_API_KEY'))
```
:::

## Features

### Voice Selection
List and select from available voices:

```python
# Get list of available voices
voices = tts.get_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("voice_id")
```

### Streaming
Supports real-time audio streaming:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Voice Properties
Adjust voice properties:

```python
# Set stability and similarity boost
tts.set_property("stability", 0.5)  # Range: 0-1
tts.set_property("similarity_boost", 0.75)  # Range: 0-1
```

### File Output
Save synthesized speech to file:

```python
# Save as MP3
tts.synth_to_file("Hello world", "output.mp3", "mp3")

# Save as WAV
tts.synth_to_file("Hello world", "output.wav", "wav")
```

## Best Practices

1. **Cost Management**
   - Monitor character usage
   - Cache frequently used phrases
   - Use appropriate stability settings

2. **Performance**
   - Reuse client instances
   - Consider chunking long text
   - Balance stability vs. performance

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Unauthorized" in str(e):
           print("Check your ElevenLabs API key")
       elif "QuotaExceeded" in str(e):
           print("Character quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- No SSML support (tags will be stripped)
- No native word timing support
- API rate limits apply
- Character quota based on subscription
- Voice cloning requires additional setup
- Limited to English and a few other languages

## Voice Optimization

### Stability vs. Similarity
- **Stability** (0-1): Higher values produce more consistent, stable speech
- **Similarity Boost** (0-1): Higher values make the voice more expressive but may introduce artifacts

```python
# For consistent, stable output
tts.set_property("stability", 0.8)
tts.set_property("similarity_boost", 0.3)

# For more expressive, varied output
tts.set_property("stability", 0.3)
tts.set_property("similarity_boost", 0.8)
```

## Custom Voices

ElevenLabs supports voice cloning, but this must be set up through their platform:

1. Create custom voice on ElevenLabs website
2. Get the voice ID
3. Use it in your code:
```python
tts.set_voice("custom_voice_id")
```

## Additional Resources

- [ElevenLabs Documentation](https://docs.elevenlabs.io/)
- [Pricing Information](https://elevenlabs.io/pricing)
- [Voice Lab](https://elevenlabs.io/voice-lab)
- [API Reference](https://docs.elevenlabs.io/api-reference)

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Learn about [audio control features](../guides/audio-control) 