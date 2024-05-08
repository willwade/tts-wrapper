
# TTS-Wrapper

[![PyPI version](https://badge.fury.io/py/tts-wrapper.svg)](https://badge.fury.io/py/tts-wrapper)
![build](https://github.com/mediatechlab/tts-wrapper/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/mediatechlab/tts-wrapper/branch/master/graph/badge.svg?token=79IG7GAK0B)](https://codecov.io/gh/mediatechlab/tts-wrapper)
[![Maintainability](https://api.codeclimate.com/v1/badges/b327dda20742c054bcf0/maintainability)](https://codeclimate.com/github/mediatechlab/tts-wrapper/maintainability)

> **Contributions are welcome! Check our [contribution guide](./CONTRIBUTING.md).**

_TTS-Wrapper_ simplifies using text-to-speech APIs by providing a unified interface across multiple services, allowing easy integration and manipulation of TTS capabilities.

## Supported Services
- AWS Polly
- Google TTS
- Microsoft Azure TTS
- IBM Watson
- ElevenLabs
- PicoTTS
- SAPI (Microsoft Speech API)

## Features
- **Text to Speech**: Convert text into spoken audio.
- **SSML Support**: Use Speech Synthesis Markup Language to enhance speech synthesis.
- **Voice and Language Selection**: Customize the voice and language for speech synthesis.
- **Streaming and Direct Play**: Stream audio or play it directly.
- **Pause, Resume, and Stop Controls**: Manage audio playback dynamically.
- **File Output**: Save spoken audio to files in various formats.
- **Unified Voice handling** Get Voices across all TTS engines with alike keys

## Installation

```sh
pip install TTS-Wrapper
```

### Dependencies
Install additional dependencies based on the services you want to use:

```sh
pip install "TTS-Wrapper[google, watson]"
```

For PicoTTS on Debian systems:

```sh
sudo apt-get install libttspico-utils
```

## Basic Usage

```python
from tts_wrapper import PollyClient
client = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))

from tts_wrapper import PollyTTS

tts = PollyTTS(client=PollyClient())
tts.speak('Hello, world!')
```

## Authorization
Each service uses different methods for authentication:

### Polly

```python
from tts_wrapper import PollyClient
client = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
```

### Google

```python
from tts_wrapper import GoogleClient
client = GoogleClient(credentials='path/to/creds.json')
```

### Microsoft

```python
from tts_wrapper import MicrosoftClient
client = MicrosoftClient(credentials='subscription_key')
```

### Watson

```python
from tts_wrapper import WatsonClient
client = WatsonClient(credentials=('api_key', 'api_url'))
```

### ElevenLabs

```python
from tts_wrapper import ElevenLabs
client = ElevenLabsClient(credentials=('api_key'))
```

and then for each engine then bring in the TTS class 

```python
from tts_wrapper import PollyTTS
tts = PollyTTS(client=client, voice='Joanna')
```

You then can peform the following methods.

## Advanced Usage

### Streaming and Playback Control

```python
tts.speak_streamed('Hello, world!')
tts.pause_audio()
tts.resume_audio()
tts.stop_audio()
```

### File Output

```python
tts.synth_to_file('Hello, world!', 'output.mp3', format='mp3')
```

### Fetch Available Voices

```python
voices = tts.get_voices()
print(voices)
```

### Voice Selection

```python
tts.set_voice('en-US-JessaNeural')
```

### SSML

```python
ssml_text = tts.ssml.add('Hello, <break time="500ms"/> world!')
tts.speak(ssml_text)
```


#### PicoTTS & SAPI

These clients dont't require authorization since they run offline.

```python
from tts_wrapper import PicoClient, SAPIClient
client = PicoClient()
# or
client = SAPIClient()
```

## Supported File Formats

By default, all engines output audio in the WAV format, but can be configured to output MP3 or other formats where supported.

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
```

## License

This project is licensed under the [MIT License](./LICENSE).
