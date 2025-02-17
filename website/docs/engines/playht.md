---
sidebar_position: 7
---

# Play.HT TTS

Play.HT provides high-quality neural text-to-speech with support for voice cloning, custom voice creation, and multiple voice engines including PlayHT 2.0 and Play3.0-mini.

## Authentication

Play.HT requires both an API key and user ID:

```python
from tts_wrapper import PlayHTClient, PlayHTTTS

client = PlayHTClient(credentials=(
    'api_key',  # Your Play.HT API key
    'user_id'   # Your Play.HT user ID
))

tts = PlayHTTTS(client)
```

:::tip
Use environment variables for secure credential management:
```python
import os

client = PlayHTClient(credentials=(
    os.getenv('PLAYHT_API_KEY'),
    os.getenv('PLAYHT_USER_ID')
))
```
:::

## Features

### Voice Selection
List and select from available voices, including both standard and cloned voices:

```python
# Get list of available voices
voices = tts.get_voices()
for voice in voices:
    print(f"Name: {voice['name']}")
    print(f"Languages: {voice['language_codes']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("voice_id", "en-US")
```

### Streaming
Supports real-time audio streaming:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Voice Properties
Adjust synthesis properties:

```python
# Set voice engine
tts.set_property("voice_engine", "PlayHT2.0")  # Options: PlayHT2.0, Play3.0-mini

# Set speed
tts.set_property("speed", "1.2")  # Range: 0.5-2.0

# Set quality
tts.set_property("quality", "high")  # Options: draft, low, medium, high, premium
```

### Advanced Features
Play.HT offers advanced voice control features:

```python
# Set emotion (PlayHT2.0)
tts.set_property("emotion", "happy")

# Set voice guidance
tts.set_property("voice_guidance", "relax more")

# Set style guidance
tts.set_property("style_guidance", "speak in a friendly tone")
```

### File Output
Save synthesized speech to file:

```python
# Save as WAV
tts.synth_to_file("Hello world", "output.wav", "wav")

# Save as MP3
tts.synth_to_file("Hello world", "output.mp3", "mp3")
```

## Best Practices

1. **Cost Management**
   - Use appropriate quality settings for your needs
   - Cache frequently used phrases
   - Monitor API usage

2. **Performance**
   - Reuse client instances
   - Choose appropriate voice engine
   - Use streaming for long text

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Unauthorized" in str(e):
           print("Check your Play.HT credentials")
       elif "QuotaExceeded" in str(e):
           print("Usage quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- No SSML support (tags will be stripped)
- No native word timing support
- API rate limits apply
- Quality settings affect synthesis time
- Some features limited to specific voice engines
- Voice cloning requires additional setup

## Voice Engine Selection

### PlayHT2.0
- Higher quality synthesis
- More natural prosody
- Supports emotions and style guidance
- Longer processing time

### Play3.0-mini
- Faster processing
- Good for real-time applications
- More consistent output
- Limited style options

```python
# For highest quality
tts.set_property("voice_engine", "PlayHT2.0")
tts.set_property("quality", "premium")

# For faster processing
tts.set_property("voice_engine", "Play3.0-mini")
tts.set_property("quality", "medium")
```

## Custom Voices

Play.HT supports voice cloning through their platform:

1. Create custom voice on Play.HT website
2. Get the voice ID (full S3 URL format)
3. Use it in your code:
```python
voice_id = "s3://voice-cloning-zero-shot/..."
tts.set_voice(voice_id)
```

## Additional Resources

- [Play.HT Documentation](https://docs.play.ht/)
- [Pricing Information](https://play.ht/pricing/)
- [Voice Library](https://play.ht/voice-library/)
- [API Reference](https://docs.play.ht/reference/api-getting-started)

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Learn about [audio control features](../guides/audio-control) 