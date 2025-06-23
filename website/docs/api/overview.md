# API Overview

TTS Wrapper's API is designed to be intuitive and consistent across different TTS engines. This overview will help you understand the main components and their relationships.

## Core Components

### TTS Base Class

The `AbstractTTS` class is the foundation of all TTS engines. It defines the common interface that all engines must implement:

```python
class AbstractTTS:
    def speak(self, text: str, return_bytes: bool = False) -> bytes | None: ...
    def speak_streamed(self, text: str, callback=None, return_bytes: bool = False) -> bytes | None: ...
    def synth_to_file(self, text: str, filepath: str, format: str = 'wav') -> None: ...
    def synth_to_bytes(self, text: str) -> bytes: ...
    def get_voices(self) -> List[Voice]: ...
    def set_voice(self, voice_id: str, lang_code: str = None) -> None: ...
    def set_property(self, property_name: str, value: str) -> None: ...
    def get_property(self, property_name: str) -> str: ...
```

### Client Base Class

The `AbstractClient` class handles authentication and communication with TTS services:

```python
class AbstractClient:
    def __init__(self, credentials: Union[str, tuple, dict]): ...
    def check_credentials(self) -> bool: ...
    def synthesize(self, text: str, options: dict = None) -> bytes: ...
    def get_voices(self) -> List[dict]: ...
```

### SSML Support

The `SSMLBuilder` class helps construct valid SSML markup:

```python
class SSMLBuilder:
    def add(self, text: str) -> str: ...
    def add_break(self, time: str) -> None: ...
    def add_prosody(self, rate: str = None, pitch: str = None, volume: str = None, text: str = None) -> None: ...
    def get_text(self) -> str: ...
```

## Common Patterns

### 1. Engine Initialization

TTS engines can be initialized in two ways:

**Recommended Pattern (Direct TTS Initialization):**
```python
# Direct initialization - recommended for new code
tts = EngineTTS(credentials=(...))
```

**Legacy Pattern (Client + TTS):**
```python
# Create client with credentials
client = EngineClient(credentials=(...))

# Create TTS instance with client
tts = EngineTTS(client)
```

:::note
For most engines, `EngineTTS` is an alias for `EngineClient` that provides the same functionality. The direct initialization pattern is simpler and recommended for new code.
:::

### 2. Voice Management

```python
# List available voices
voices = tts.get_voices()

# Set voice by ID
tts.set_voice('voice_id', 'lang_code')
```

### 3. Speech Properties

```python
# Set speech properties
tts.set_property('rate', 'fast')
tts.set_property('volume', '80')
tts.set_property('pitch', 'high')
```

### 4. Audio Output

```python
# Direct playback
tts.speak("Hello world")

# Stream with callbacks
tts.speak_streamed("Hello world", callback=on_word)

# Save to file
tts.synth_to_file("Hello world", "output.wav")

# Get audio bytes (new in v1.x)
audio_bytes = tts.speak("Hello world", return_bytes=True)
audio_bytes = tts.speak_streamed("Hello world", return_bytes=True)

# Get bytes AND save to file
audio_bytes = tts.speak_streamed("Hello world", return_bytes=True, save_to_file_path="output.wav")
```

## Engine-Specific Features

While the base API is consistent, some engines offer additional features:

### AWS Polly
- Neural TTS support
- Speech Marks
- Lexicon management

### Google Cloud TTS
- WaveNet voices
- Audio device selection
- Custom voice selection

### Microsoft Azure
- Custom voice training
- Multiple voice styles
- Role-play voices

**Example:**
```python
from tts_wrapper import MicrosoftTTS

# Direct initialization (recommended)
tts = MicrosoftTTS(credentials=('subscription_key', 'region'))
tts.set_voice('en-US-JennyNeural')
tts.speak("Hello from Azure TTS!")

# Legacy pattern (still supported)
from tts_wrapper import MicrosoftClient
client = MicrosoftClient(credentials=('subscription_key', 'region'))
tts = MicrosoftTTS(client)
```

### IBM Watson
- Custom dictionary
- Voice transformation
- Background audio

## Property Values

### Rate
- `x-slow`
- `slow`
- `medium` (default)
- `fast`
- `x-fast`

### Volume
- `silent` (0)
- `x-soft` (25)
- `soft` (50)
- `medium` (75)
- `loud` (100)

### Pitch
- `x-low`
- `low`
- `medium` (default)
- `high`
- `x-high`

## Error Handling

TTS Wrapper defines several exception classes:

```python
class TTSError(Exception): pass
class AuthenticationError(TTSError): pass
class SynthesisError(TTSError): pass
class InvalidPropertyError(TTSError): pass
```

Example error handling:

```python
from tts_wrapper.exceptions import TTSError

try:
    tts.speak("Hello world")
except AuthenticationError:
    print("Authentication failed")
except SynthesisError:
    print("Speech synthesis failed")
except TTSError as e:
    print(f"General TTS error: {e}")
```

## Next Steps

- [Developer Overview](../developer/overview)
- [Adding New Engines](../developer/adding-engines)
- [Release Process](../developer/releases)
- [Contributing Guide](../developer/contributing) 