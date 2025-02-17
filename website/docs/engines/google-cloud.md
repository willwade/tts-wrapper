---
sidebar_position: 3
---

# Google Cloud TTS

Google Cloud Text-to-Speech provides high-quality voice synthesis with support for multiple languages, voices, and neural models.

## Authentication

Google Cloud TTS requires a service account JSON file. You can provide it in two ways:

```python
from tts_wrapper import GoogleTTS, GoogleClient

# Method 1: Path to service account JSON file
client = GoogleClient(credentials='path/to/creds.json')

# Method 2: Service account credentials as dictionary
import json
with open('path/to/creds.json', 'r') as file:
    credentials_dict = json.load(file)
client = GoogleClient(credentials=credentials_dict)

tts = GoogleTTS(client)
```

:::tip
Use environment variables for secure credential management:
```python
import os
client = GoogleClient(credentials=os.getenv('GOOGLE_SA_PATH'))
```
:::

## Features

### SSML Support
Google Cloud TTS provides comprehensive SSML support:

```python
ssml_text = """
<speak>
    Hello <break time="300ms"/> World!
    <prosody rate="slow" pitch="+2st">
        This is a test of SSML features.
    </prosody>
</speak>
"""
tts.speak(ssml_text)
```

See [Google Cloud TTS SSML Reference](https://cloud.google.com/text-to-speech/docs/ssml) for all supported tags.

### Streaming
Supports real-time audio streaming:

```python
# Stream synthesis for real-time playback
tts.speak_streamed("This text will be synthesized and played in real-time")
```

### Word Timing
Get precise timing information for each word:

```python
def on_word(word: str):
    print(f"Speaking: {word}")

tts.connect("started-word", on_word)
tts.speak("This text will trigger word timing callbacks")
```

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

# Set a specific voice and language
tts.set_voice("en-US-Standard-C", "en-US")
```

### Neural Voices
Google Cloud TTS offers high-quality neural voices:

```python
# Select a neural voice
tts.set_voice("en-US-Neural2-C", "en-US")
```

## Best Practices

1. **Cost Management**
   - Use caching for frequently used phrases
   - Monitor usage through Google Cloud Console
   - Consider using standard voices for development

2. **Performance**
   - Reuse client instances
   - Use appropriate audio profiles
   - Choose the closest region for lower latency

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "InvalidCredentials" in str(e):
           print("Check your Google Cloud credentials")
       elif "QuotaExceeded" in str(e):
           print("Usage quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Maximum text length of 5000 characters per request
- API rate limits apply (check Google Cloud quotas)
- Neural voices may have higher latency
- Some SSML features are voice-specific
- Pricing varies by voice type (standard vs. neural)

## Additional Resources

- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)
- [Pricing Information](https://cloud.google.com/text-to-speech/pricing)
- [Supported Voices](https://cloud.google.com/text-to-speech/docs/voices)
- [SSML Guide](https://cloud.google.com/text-to-speech/docs/ssml)

## Next Steps

- Learn about [SSML support](../guides/ssml)
- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks) 