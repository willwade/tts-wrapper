---
sidebar_position: 2
---

# SSML Support

Speech Synthesis Markup Language (SSML) support in TTS Wrapper is engine-dependent. Each engine has its own SSML implementation that maps to what the underlying service supports.

## Using SSML

Each TTS engine provides an SSML handler through the `ssml` property:

```python
from tts_wrapper import PollyClient, PollyTTS

client = PollyClient(credentials=('region', 'key_id', 'access_key'))
tts = PollyTTS(client)

# Create SSML using the handler
ssml_text = tts.ssml.add('Hello <break time="500ms"/> world!')
tts.speak(ssml_text)
```

## Engine-Specific SSML

### AWS Polly
Supports the full range of SSML tags as documented in the [Amazon Polly SSML Reference](https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html).

### Google Cloud
Follows the [Google Cloud Text-to-Speech SSML Reference](https://cloud.google.com/text-to-speech/docs/ssml).

### Microsoft Azure
Implements SSML according to the [Microsoft Speech Service SSML Reference](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/speech-synthesis-markup).

### IBM Watson
Uses SSML as specified in the [IBM Watson SSML Reference](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-ssml).

### AVSynth (macOS)
Converts SSML to AVSpeechSynthesizer commands:
- `<break>` → `[[slnc ms]]`
- `<prosody>` → Rate/pitch/volume commands
- Other tags are stripped to plain text

### eSpeak
Supports basic SSML tags with its own extensions. See the [eSpeak Documentation](https://github.com/espeak-ng/espeak-ng/blob/master/docs/markup.md).

### SAPI (Windows)
Limited SSML support through the Windows Speech API.

### ElevenLabs, Play.HT, Wit.ai
These engines do not support SSML natively. SSML tags will be stripped and the plain text content will be used.

## SSML Helper Methods

Each engine's SSML handler provides helper methods for common operations:

```python
# Clear any existing SSML content
tts.ssml.clear_ssml()

# Add text (may be plain text or SSML depending on engine)
tts.ssml.add("Text to speak")

# Get plain text (strips SSML tags)
plain_text = tts.ssml.get_text()
```

## Best Practices

1. **Check Engine Support**: Always check the specific engine's documentation for supported SSML features
2. **Graceful Degradation**: Provide plain text alternatives for unsupported SSML features
3. **Engine-Specific Features**: Use engine-specific SSML features when needed for better control
4. **Test Thoroughly**: Test SSML across different engines if your application needs to support multiple engines

## Example: Engine-Specific SSML

Here's how to handle SSML across different engines:

```python
def speak_with_pause(tts, text: str, pause_ms: int = 500) -> None:
    """Demonstrate SSML handling across engines."""
    
    # Get the SSML handler for this engine
    ssml = tts.ssml
    ssml.clear_ssml()
    
    if isinstance(tts, PollyTTS):
        # Use Polly-specific SSML
        ssml_text = f'<speak>First part <break time="{pause_ms}ms"/> Second part</speak>'
    elif isinstance(tts, AVSynthTTS):
        # Use AVSynth command format
        ssml_text = f'First part [[slnc {pause_ms}]] Second part'
    else:
        # For engines without SSML support, just use plain text
        ssml_text = f'First part. Second part'
    
    tts.speak(ssml.add(ssml_text))
```

## Next Steps

- Learn about [audio control features](audio-control) for playback manipulation
- Explore [streaming capabilities](streaming) for real-time synthesis
- Check out [callback functionality](callbacks) for speech events 