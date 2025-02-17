---
sidebar_position: 2
---

# AWS Polly

Amazon Polly is a cloud-based text-to-speech service that offers high-quality voice synthesis with support for multiple languages and voices.

## Authentication

To use AWS Polly, you'll need AWS credentials:

```python
from tts_wrapper import PollyTTS, PollyClient

client = PollyClient(credentials=(
    'aws_region',      # e.g., 'us-east-1'
    'aws_key_id',      # Your AWS Access Key ID
    'aws_secret_key'   # Your AWS Secret Access Key
))

tts = PollyTTS(client)
```

:::tip
Use environment variables or AWS credentials file for secure credential management:
```python
import os

client = PollyClient(credentials=(
    os.getenv('AWS_REGION'),
    os.getenv('AWS_ACCESS_KEY_ID'),
    os.getenv('AWS_SECRET_ACCESS_KEY')
))
```
:::

## Features

### SSML Support
AWS Polly provides comprehensive SSML support:

```python
ssml_text = """
<speak>
    Hello <break time="300ms"/> World!
    <prosody rate="slow" pitch="+20%">
        This is a test of SSML features.
    </prosody>
</speak>
"""
tts.speak(ssml_text)
```

See [Amazon Polly SSML Reference](https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html) for all supported tags.

### Streaming
Polly supports real-time audio streaming:

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
    print(f"ID: {voice['Id']}, Language: {voice['LanguageCode']}")

# Set a specific voice
tts.set_voice("Joanna", "en-US")
```

## Best Practices

1. **Cost Management**
   - Use streaming for long text to optimize bandwidth
   - Cache frequently used phrases
   - Monitor usage through AWS Console

2. **Performance**
   - Reuse client instances
   - Use appropriate sampling rates
   - Consider regional endpoints for lower latency

3. **Error Handling**
   ```python
   try:
       tts.speak("Hello, world!")
   except Exception as e:
       if "CredentialsError" in str(e):
           print("Check your AWS credentials")
       elif "QuotaExceeded" in str(e):
           print("AWS Polly quota exceeded")
       else:
           print(f"Error: {e}")
   ```

## Limitations

- Maximum text length of 3000 characters per request
- API rate limits apply (check AWS quotas)
- Certain SSML features limited to specific voices
- Neural voices not available in all regions

## Additional Resources

- [AWS Polly Documentation](https://docs.aws.amazon.com/polly/)
- [Pricing Information](https://aws.amazon.com/polly/pricing/)
- [Voice List](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html)

## Next Steps

- Learn about [SSML support](../guides/ssml)
- Explore [streaming capabilities](../guides/streaming)
- Check out [callback functionality](../guides/callbacks) 