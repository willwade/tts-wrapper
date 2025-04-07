---
sidebar_position: 10
---

# OpenAI TTS

OpenAI provides high-quality neural text-to-speech through their GPT-4o mini TTS model and other TTS models. It offers natural-sounding voices with support for multiple languages and voice characteristics control through instructions.

## Authentication

OpenAI requires an API key:

```python
from tts_wrapper import OpenAIClient

# Create the client with your API key
tts = OpenAIClient(api_key='your_api_key')
```

:::tip
Use environment variables for secure credential management:
```python
import os

tts = OpenAIClient(api_key=os.getenv('OPENAI_API_KEY'))
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
    print(f"ID: {voice['id']}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("alloy")  # Other options: nova, echo, fable, onyx, shimmer, etc.
```

### Model Selection
Choose from different TTS models:

```python
# Create client with specific model
tts = OpenAIClient(
    api_key='your_api_key',
    model='gpt-4o-mini-tts'  # Default model
)

# Other models include:
# - tts-1 (lower latency)
# - tts-1-hd (higher quality)
```

### Streaming
Supports real-time audio streaming:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Voice Properties via Instructions
Control voice characteristics through properties:

```python
# Set rate (speed)
tts.set_property("rate", 0.7)  # Slow
tts.set_property("rate", 1.3)  # Fast

# Set volume
tts.set_property("volume", 0.6)  # Quiet
tts.set_property("volume", 1.4)  # Loud

# Set pitch
tts.set_property("pitch", 0.7)  # Low pitch
tts.set_property("pitch", 1.3)  # High pitch

# You can also use string values
tts.set_property("rate", "moderate")
tts.set_property("volume", "medium")
tts.set_property("pitch", "normal")
```

### Custom Instructions
Provide custom instructions for more control:

```python
# Create client with specific instructions
tts = OpenAIClient(
    api_key='your_api_key',
    instructions="Speak in a cheerful and positive tone with slight British accent."
)
```

### File Output
Save synthesized speech to file:

```python
# Save as MP3
tts.synth("Hello world", "output.mp3", "mp3")

# Save as WAV
tts.synth("Hello world", "output.wav", "wav")
```

## Best Practices

1. **Cost Management**
   - Monitor API usage
   - Cache frequently used phrases
   - Use appropriate models for your needs (tts-1 for lower latency, tts-1-hd for higher quality)

2. **Performance**
   - Use WAV or PCM format for streaming for lowest latency
   - For file output, MP3 provides good compression
   - Balance quality vs. performance with model selection

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Unauthorized" in str(e):
           print("Check your OpenAI API key")
       elif "Rate limit" in str(e):
           print("API rate limit exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- No SSML support (tags will be stripped)
- No word timing information (estimated timings only)
- No word event callbacks
- API rate limits apply
- Usage costs based on character count
- No custom voice creation
- Voices optimized for English, though multiple languages are supported

## Language Support

OpenAI TTS supports all languages that the Whisper model supports, including:

Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh.

## Voice Customization

While OpenAI doesn't support custom voice creation, you can customize the voice output using instructions:

```python
# Create client with specific instructions
tts = OpenAIClient(
    api_key='your_api_key',
    instructions="Speak with a deep, resonant voice. Use a slow, deliberate pace with slight pauses between sentences."
)
```

You can also combine properties with instructions:

```python
tts = OpenAIClient(
    api_key='your_api_key',
    instructions="Speak with a slight French accent."
)

# Add properties on top of instructions
tts.set_property("rate", 0.9)  # Slightly slow
tts.set_property("pitch", 1.1)  # Slightly high pitch
```

## Output Formats

OpenAI supports multiple output formats:

- MP3 (default): Good for general use
- WAV: Uncompressed, good for processing
- PCM: Raw samples, lowest latency
- OPUS: Good for streaming
- AAC: Good for mobile
- FLAC: Lossless compression

```python
# Save in different formats
tts.synth("Hello world", "output.mp3", "mp3")
tts.synth("Hello world", "output.wav", "wav")
tts.synth("Hello world", "output.flac", "flac")
```

## Additional Resources

- [OpenAI TTS Documentation](https://platform.openai.com/docs/guides/text-to-speech)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference/audio/createSpeech)
- [OpenAI Pricing](https://openai.com/pricing)
- [OpenAI.fm Demo](https://openai.fm) - Interactive demo for trying voices

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [audio control features](../guides/audio-control)
- Learn about [multilingual support](../guides/multilingual)
