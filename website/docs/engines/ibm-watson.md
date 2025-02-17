---
sidebar_position: 4
---

# IBM Watson TTS

IBM Watson Text-to-Speech provides high-quality voice synthesis with support for neural voices, SSML, and real-time streaming capabilities.

## Authentication

IBM Watson TTS requires an API key, region, and instance ID:

```python
from tts_wrapper import WatsonClient, WatsonTTS

client = WatsonClient(credentials=(
    'api_key',      # Your IBM Watson API key
    'api_url',      # Service URL (e.g., 'https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/')
    'region',       # Region (e.g., 'eu-gb')
    'instance_id'   # Instance ID
))

tts = WatsonTTS(client)
```

:::tip
Use environment variables for secure credential management:
```python
import os

client = WatsonClient(credentials=(
    os.getenv('WATSON_API_KEY'),
    os.getenv('WATSON_API_URL'),
    os.getenv('WATSON_REGION'),
    os.getenv('WATSON_INSTANCE_ID')
))
```
:::

## Features

### SSML Support
IBM Watson provides comprehensive SSML support:

```python
ssml_text = """
<speak>
    Hello <break time="300ms"/> World!
    <prosody rate="slow" pitch="+20Hz">
        This is a test of SSML features.
    </prosody>
</speak>
"""
tts.speak(ssml_text)
```

See [IBM Watson SSML Reference](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-ssml) for all supported tags.

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

# Set a specific voice
tts.set_voice("en-US_AllisonV3Voice", "en-US")
```

### Voice Transformation
IBM Watson supports voice transformation features:

```python
# Adjust speaking rate
tts.set_property("rate", "slow")  # Options: x-slow, slow, medium, fast, x-fast

# Adjust pitch
tts.set_property("pitch", "high")  # Options: x-low, low, medium, high, x-high

# Adjust volume
tts.set_property("volume", "loud")  # Options: soft, medium, loud
```

## Best Practices

1. **Cost Management**
   - Use appropriate audio formats
   - Cache frequently used phrases
   - Monitor API usage
   - Consider using websocket connections for streaming

2. **Performance**
   - Reuse client instances
   - Choose appropriate audio formats
   - Use streaming for long text
   - Select closest region for lower latency

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "Unauthorized" in str(e):
           print("Check your IBM Watson credentials")
       elif "QuotaExceeded" in str(e):
           print("Usage quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Maximum text length per request (5000 characters)
- API rate limits apply
- Some SSML features are voice-specific
- Neural voices not available in all regions
- Custom voice creation requires enterprise plan

## Voice Types

### Neural Voices
Higher quality, more natural-sounding voices:
```python
# Use a neural voice
tts.set_voice("en-US_EmmaV3Voice")
```

### Standard Voices
Traditional voices with consistent quality:
```python
# Use a standard voice
tts.set_voice("en-US_MichaelVoice")
```

## Language Support

IBM Watson TTS supports multiple languages and dialects:

```python
# List voices for a specific language
voices = tts.get_voices()
spanish_voices = [v for v in voices if "es" in v["language_codes"][0]]
for voice in spanish_voices:
    print(f"Spanish voice: {voice['name']}")
```

## Additional Resources

- [IBM Watson TTS Documentation](https://cloud.ibm.com/docs/text-to-speech)
- [Pricing Information](https://www.ibm.com/cloud/watson-text-to-speech/pricing)
- [SSML Documentation](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-ssml)
- [Voice List](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-voices)

## Next Steps

- Learn about [SSML support](../guides/ssml)
- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks) 