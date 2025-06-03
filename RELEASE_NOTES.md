# TTS Wrapper v1.0.0 Release Notes

## Major Architecture Changes

This release includes a significant refactoring of the TTS Wrapper library that simplifies the architecture and improves usability. The changes are breaking but will make the library more intuitive and easier to use.

### Client Class Simplification

**Before:**
```python
from tts_wrapper import PollyClient
from tts_wrapper import PollyTTS

client = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
tts = PollyTTS(client)
```

**Now:**
```python
from tts_wrapper import PollyClient

tts = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
```

All TTS engine clients now directly inherit from `AbstractTTS`, eliminating the need for separate client and TTS classes. This means:

- You only need to import and instantiate a single class
- All TTS functionality is available directly from the client instance
- The client classes now have all the methods previously available in the TTS classes

### SSML Improvements

- Each TTS engine now has proper SSML support with engine-specific implementations
- Added graceful fallback to plain text when SSML processing fails
- Improved error handling for SSML processing
- Added support for SSML pauses and other markup across all engines
- Fixed Microsoft TTS SSML formatting issues

### Language Code Standardization

- Unified language code handling across all TTS engines
- Added support for different language code formats (BCP-47, ISO 639-3, human-readable)
- The `get_voices` method now supports a parameter to specify language code format

### Callback Handling Improvements

- Fixed word timing callbacks in Microsoft TTS and other engines
- Improved error handling in callback processing
- Added more consistent callback behavior across all engines
- Fixed duplicate callback issues in some engines

### Default Voice Selection

- All TTS engines now default to a voice if not explicitly set during initialization
- Users can provide a voice during engine initialization without needing to call `set_voice` separately

## Migration Guide

### 1. Update Imports and Initialization

**Before:**
```python
from tts_wrapper import GoogleClient
from tts_wrapper import GoogleTTS

client = GoogleClient(credentials='path/to/credentials.json')
tts = GoogleTTS(client)
```

**Now:**
```python
from tts_wrapper import GoogleClient

tts = GoogleClient(credentials='path/to/credentials.json')
```

### 2. Voice Setting

**Before:**
```python
client = MicrosoftClient(credentials=(token, region))
tts = MicrosoftTTS(client)
tts.set_voice("en-US-JennyMultilingualNeural")
```

**Now:**
```python
# Recommended: Direct initialization
tts = MicrosoftTTS(credentials=(token, region))
tts.set_voice("en-US-JennyMultilingualNeural")

# Alternative: Still supported for backward compatibility
tts = MicrosoftClient(credentials=(token, region))
tts.set_voice("en-US-JennyMultilingualNeural")
```

### 3. SSML Usage

**Before:**
```python
from tts_wrapper import eSpeakClient, eSpeakTTS

client = eSpeakClient()
tts = eSpeakTTS(client)
ssml = tts.ssml.add("This is a test")
tts.speak(ssml)
```

**Now:**
```python
from tts_wrapper import eSpeakClient

tts = eSpeakClient()
ssml = tts.ssml.add("This is a test")
tts.speak(ssml)
```

### 4. Getting Voices with Language Code Format

**New Feature:**
```python
# Get voices with BCP-47 language codes
voices = tts.get_voices(language_format="bcp47")

# Get voices with ISO 639-3 language codes
voices = tts.get_voices(language_format="iso639-3")

# Get voices with human-readable language names
voices = tts.get_voices(language_format="human")

# Get voices with all language code formats
voices = tts.get_voices(language_format="all")
```

## Breaking Changes Summary

1. Removed all separate TTS classes (e.g., `PollyTTS`, `GoogleTTS`, etc.)
2. Client classes now inherit directly from `AbstractTTS`
3. Changed parameter order in some methods for consistency
4. Updated SSML handling across all engines
5. Changed the behavior of some callback methods

## Improvements Summary

1. Simplified architecture with fewer classes
2. More consistent behavior across all TTS engines
3. Better error handling and fallback mechanisms
4. Improved SSML support
5. Standardized language code handling
6. Fixed various bugs in word timing callbacks
