---
sidebar_position: 2
---

# Adding New Engines

This guide explains how to add a new TTS engine to the wrapper system.

## Directory Structure

Create a new directory for your engine in `tts_wrapper/engines/`:

```
tts_wrapper/engines/myengine/
├── __init__.py
├── client.py
├── myengine.py
└── ssml.py
```

## Implementation Steps

### 1. Create Client Class

The client handles communication with the TTS service:

```python
from typing import Any, Optional, Tuple

class MyEngineClient:
    def __init__(self, credentials: Optional[Tuple[str, ...]] = None) -> None:
        """Initialize the client with credentials."""
        self._credentials = credentials
        # Setup client-specific configuration

    def synth(self, text: str, options: dict) -> bytes:
        """Convert text to speech."""
        # Implement synthesis logic
        return audio_data

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices in standardized format."""
        return [{
            "id": "voice_id",
            "name": "Voice Name",
            "language_codes": ["en-US"],
            "gender": "female"
        }]

    def check_credentials(self) -> bool:
        """Verify credentials are valid."""
        try:
            self.get_voices()
            return True
        except Exception:
            return False
```

### 2. Create TTS Class

The TTS class implements the abstract interface:

```python
from typing import Any, Optional
from tts_wrapper.tts import AbstractTTS

class MyEngineTTS(AbstractTTS):
    def __init__(
        self,
        client: MyEngineClient,
        voice: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> None:
        """Initialize the TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self._lang = lang
        self.audio_rate = 22050  # Set appropriate sample rate
        self.channels = 1
        self.sample_width = 2  # 16-bit audio

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to speech."""
        text = str(text)
        options = {}

        if self._voice:
            options["voice"] = self._voice

        # Add any set properties
        for prop in ["rate", "volume", "pitch"]:
            value = self.get_property(prop)
            if value is not None:
                options[prop] = str(value)

        # Get audio data from client
        return self._client.synth(text, options)

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Set the voice for synthesis."""
        super().set_voice(voice_id, lang_id)
        self._voice = voice_id
        if lang_id:
            self._lang = lang_id
```

### 3. Implement SSML Support (Optional)

If your engine supports SSML:

```python
from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode

class MyEngineSSMLNode(SSMLNode):
    """SSML node implementation."""
    def __str__(self) -> str:
        """Convert SSML to engine-specific format."""
        # Implement SSML conversion
        return converted_ssml

class MyEngineSSML(BaseSSMLRoot):
    """SSML root implementation."""
    def __init__(self) -> None:
        super().__init__()
        self._inner = MyEngineSSMLNode("speak")
```

### 4. Update Package Exports

In `__init__.py`:

```python
from .client import MyEngineClient
from .myengine import MyEngineTTS
from .ssml import MyEngineSSML

__all__ = ["MyEngineClient", "MyEngineTTS", "MyEngineSSML"]
```

## Testing

Create tests in `tests/test_myengine.py`:

```python
import unittest
from tts_wrapper.engines.myengine import MyEngineClient, MyEngineTTS

class TestMyEngine(unittest.TestCase):
    def setUp(self):
        self.client = MyEngineClient(credentials=("test_cred",))
        self.tts = MyEngineTTS(self.client)

    def test_basic_synthesis(self):
        """Test basic text-to-speech synthesis."""
        audio = self.tts.synth_to_bytes("Hello, world!")
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0)

    def test_voice_selection(self):
        """Test voice selection."""
        voices = self.tts.get_voices()
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
```

## Documentation

1. Add engine documentation in `website/docs/engines/`
2. Update engine comparison in overview
3. Add examples in `examples/`
4. Update README.md with new engine

## Best Practices

1. **Error Handling**
   - Use custom exceptions where appropriate
   - Provide clear error messages
   - Handle network errors gracefully

2. **Performance**
   - Implement streaming where possible
   - Reuse client instances
   - Cache frequently used data

3. **Compatibility**
   - Follow the standard voice format
   - Implement all abstract methods
   - Support common properties

4. **Documentation**
   - Document all public methods
   - Include usage examples
   - List limitations and requirements

## Next Steps

- Review the [release process](releases)
- Learn how to [contribute](contributing)
- Check existing engine implementations for examples 