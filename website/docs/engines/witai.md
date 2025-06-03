---
sidebar_position: 8
---

# Wit.ai TTS

Wit.ai provides text-to-speech capabilities as part of Facebook's AI services. It offers basic speech synthesis with support for multiple languages.

## Authentication

Wit.ai requires an API token for authentication:

```python
from tts_wrapper import WitAiClient

tts = WitAiClient(credentials='your_wit_ai_token')
```

:::tip
Use environment variables for secure credential management:
```python
import os

tts = WitAiClient(credentials=os.getenv('WITAI_TOKEN'))
```
:::

:::note
`WitAiClient` can be used directly as it implements the TTS interface. The legacy pattern with separate `WitAiTTS` class is still supported for backward compatibility.
:::

## Features

### Voice Selection
Set language for synthesis:

```python
# Set language
tts.set_voice("en", "en-US")  # Language code and optional dialect

# Different languages
tts.set_voice("fr", "fr-FR")  # French
tts.set_voice("es", "es-ES")  # Spanish
```

### Basic Synthesis
Simple text-to-speech conversion:

```python
# Basic speech synthesis
tts.speak("Hello, this is a test of Wit.ai TTS")

# Different languages
tts.set_voice("fr", "fr-FR")
tts.speak("Bonjour, ceci est un test")
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

1. **API Usage**
   - Monitor API usage limits
   - Cache frequently used phrases
   - Handle rate limiting gracefully
   - Keep requests reasonable in frequency

2. **Performance**
   - Reuse client instances
   - Handle network connectivity issues
   - Consider response times in your application

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Unauthorized" in str(e):
           print("Check your Wit.ai token")
       elif "Connection" in str(e):
           print("Check internet connection")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Requires internet connection
- No SSML support
- Limited voice selection
- No word timing support
- Basic prosody control
- API rate limits apply
- Quality may vary by language
- Limited control over voice properties

## Audio Settings

### Audio Format
- Format: MP3 (converted to WAV for playback)
- Sample Rate: 22050 Hz
- Channels: Mono (1 channel)
- Sample Width: 16-bit

```python
print(f"Audio rate: {tts.audio_rate}")    # 22050
print(f"Channels: {tts.channels}")        # 1
print(f"Sample width: {tts.sample_width}") # 2 (16-bit)
```

## Language Support

Wit.ai supports multiple languages:

```python
# Common language codes
languages = {
    "English": ("en", "en-US"),
    "French": ("fr", "fr-FR"),
    "Spanish": ("es", "es-ES"),
    "German": ("de", "de-DE"),
    "Italian": ("it", "it-IT")
}

# Test different languages
for name, (lang, dialect) in languages.items():
    tts.set_voice(lang, dialect)
    tts.speak(f"This is a test in {name}")
```

## Use Cases

### Basic TTS Applications
```python
# Simple announcements
tts.speak("Your download is complete")

# Multi-language messages
messages = {
    ("en", "en-US"): "Welcome to our service",
    ("fr", "fr-FR"): "Bienvenue à notre service",
    ("es", "es-ES"): "Bienvenido a nuestro servicio"
}

for (lang, dialect), message in messages.items():
    tts.set_voice(lang, dialect)
    tts.speak(message)
```

### Integration with Wit.ai NLP
While the TTS wrapper focuses on speech synthesis, Wit.ai also offers natural language processing capabilities that can be integrated:

```python
# Example of combining NLP and TTS (requires separate Wit.ai NLP setup)
response = "Response from Wit.ai NLP"  # Your NLP logic here
tts.speak(response)
```

## Additional Resources

- [Wit.ai Documentation](https://wit.ai/docs)
- [API Reference](https://wit.ai/docs/http/20200513)
- [Language Support](https://wit.ai/docs/http#language-support)

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Learn about [audio control features](../guides/audio-control) 