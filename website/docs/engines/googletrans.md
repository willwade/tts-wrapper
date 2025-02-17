---
sidebar_position: 12
---

# GoogleTrans TTS

GoogleTrans provides free text-to-speech capabilities through Google Translate's speech synthesis. It's useful for basic TTS needs without requiring API keys or authentication.

## Platform Support

GoogleTrans works on all platforms with internet connectivity:

```python
from tts_wrapper import GoogleTransClient, GoogleTransTTS

# Initialize client and TTS (no credentials needed)
client = GoogleTransClient()
tts = GoogleTransTTS(client)
```

## Features

### Language Selection
Select from available languages:

```python
# Set language
tts.set_voice("en", "en")  # Language code for English

# Different languages
tts.set_voice("fr", "fr")  # French
tts.set_voice("es", "es")  # Spanish
tts.set_voice("de", "de")  # German
```

### Basic Synthesis
Simple text-to-speech conversion:

```python
# Basic speech synthesis
tts.speak("Hello, this is a test of Google Translate TTS")

# Different languages
tts.set_voice("fr", "fr")
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

1. **Usage Guidelines**
   - Respect Google's terms of service
   - Use for personal/testing purposes only
   - Consider commercial TTS services for production use
   - Keep requests reasonable in frequency

2. **Performance**
   - Reuse client instances
   - Consider caching frequently used phrases
   - Handle network connectivity issues

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Connection" in str(e):
           print("Check internet connection")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Requires internet connection
- No SSML support
- No voice selection (language-based only)
- No word timing support
- Limited control over voice properties
- Rate limits may apply
- Not recommended for commercial use
- Quality may vary by language

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

GoogleTrans supports multiple languages:

```python
# Common language codes
LANGUAGES = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Russian": "ru"
}

# Set language
for name, code in LANGUAGES.items():
    tts.set_voice(code, code)
    tts.speak(f"This is a test in {name}")
```

## Use Cases

### Language Learning
```python
# Practice pronunciation in different languages
phrases = {
    "fr": "Bonjour, comment allez-vous?",
    "es": "¡Hola! ¿Cómo estás?",
    "de": "Guten Tag, wie geht es Ihnen?"
}

for lang, phrase in phrases.items():
    tts.set_voice(lang, lang)
    tts.speak(phrase)
```

### Quick Testing
```python
# Quick TTS testing without API setup
tts.set_voice("en", "en")
tts.speak("This is a quick test of text-to-speech")
```

## Additional Resources

- [Google Cloud TTS](../google-cloud) (for production use)
- [Language Codes Reference](https://cloud.google.com/translate/docs/languages)

## Next Steps

- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks)
- Consider upgrading to [Google Cloud TTS](../google-cloud) for production use 