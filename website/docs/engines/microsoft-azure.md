---
sidebar_position: 4
---

# Microsoft Azure TTS

Microsoft Azure Cognitive Services Text-to-Speech provides high-quality voice synthesis with support for neural voices, custom voice creation, and extensive SSML features.

## Authentication

Azure TTS requires a subscription key and region:

```python
from tts_wrapper import MicrosoftTTS, MicrosoftClient

client = MicrosoftClient(credentials=(
    'subscription_key',  # Your Azure subscription key
    'region'            # e.g., 'eastus', 'westeurope'
))

tts = MicrosoftTTS(client)
```

:::tip
Use environment variables for secure credential management:
```python
import os

client = MicrosoftClient(credentials=(
    os.getenv('MICROSOFT_TOKEN'),
    os.getenv('MICROSOFT_REGION')
))
```
:::

## Features

### SSML Support
Azure TTS provides extensive SSML support with unique features:

```python
ssml_text = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts">
    Hello <break time="300ms"/> World!
    <prosody rate="-20%" pitch="+20%">
        This is a test of SSML features.
    </prosody>
    <mstts:express-as style="cheerful">
        This text will be spoken in a cheerful way!
    </mstts:express-as>
</speak>
"""
tts.speak(ssml_text)
```

See [Microsoft TTS SSML Reference](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-synthesis-markup) for all supported tags.

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
    print(f"Locale: {voice['language_codes'][0]}")
    print(f"Gender: {voice['gender']}")
    print("---")

# Set a specific voice
tts.set_voice("en-US-JennyNeural", "en-US")
```

### Voice Styles and Roles
Azure offers unique voice styling capabilities:

```python
ssml_text = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts">
    <mstts:express-as style="excited" styledegree="2">
        This is very exciting news!
    </mstts:express-as>
</speak>
"""
tts.speak(ssml_text)
```

## Best Practices

1. **Cost Management**
   - Use streaming for long text
   - Monitor usage through Azure Portal
   - Cache frequently used phrases

2. **Performance**
   - Reuse client instances
   - Choose appropriate region
   - Use appropriate voice selection for your needs

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "AuthenticationFailed" in str(e):
           print("Check your Azure credentials")
       elif "QuotaExceeded" in str(e):
           print("Usage quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Maximum text length varies by endpoint
- API rate limits apply (check Azure quotas)
- Some voice styles only available with specific voices
- Neural voices may have higher latency
- Custom voice creation requires additional setup

## Additional Resources

- [Azure TTS Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/text-to-speech)
- [Pricing Information](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)
- [Voice List](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=tts)
- [SSML Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-synthesis-markup)

## Next Steps

- Learn about [SSML support](../guides/ssml)
- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks) 