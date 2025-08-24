# py3-TTS-Wrapper

[![PyPI version](https://badge.fury.io/py/py3-tts-wrapper.svg)](https://badge.fury.io/py/py3-tts-wrapper)
[![codecov](https://codecov.io/gh/willwade/py3-tts-wrapper/branch/master/graph/badge.svg?token=79IG7GAK0B)](https://codecov.io/gh/willwade/py3-tts-wrapper)

> **Contributions are welcome! Check our [contribution guide](./CONTRIBUTING.md).**

> **Want this for NodeJS/JS?** - see http://github.com/willwade/js-tts-wrapper


_TTS-Wrapper_ simplifies using text-to-speech APIs by providing a unified interface across multiple services, allowing easy integration and manipulation of TTS capabilities.

 > ℹ️ Full documentation is available at [https://willwade.github.io/tts-wrapper/](https://willwade.github.io/tts-wrapper/)

## Requirements

- Python 3.10 or higher
- System dependencies (see below)
- API credentials for online services

## Supported Services

- AWS Polly
- Google TTS
- Google Translate TTS (GoogleTrans)
- Microsoft Azure TTS
- IBM Watson
- ElevenLabs
- Wit.Ai
- eSpeak-NG
- Play.HT
- UpliftAI
- OpenAI
- AVSynth (macOS only)
- SAPI (Windows only)
- Sherpa-Onnx (NB: Means you can run any ONNX model you want - eg Piper or MMS models)

### Experimental (Not fully featured or in a state of WIP)

- PicoTTS
- UWP (WinRT) Speech system (win 10+)

## Features
- **Text to Speech**: Convert text into spoken audio.
- **SSML Support**: Use Speech Synthesis Markup Language to enhance speech synthesis.
- **Voice and Language Selection**: Customize the voice and language for speech synthesis.
- **Streaming and Direct Play**: Stream audio or play it directly.
- **Pause, Resume, and Stop Controls**: Manage audio playback dynamically.
- **File Output**: Save spoken audio to files in various formats.
- **Unified Voice handling** Get Voices across all TTS engines with alike keys
- **Volume, Pitch, and Rate Controls** Control volume, pitch and rate with unified methods


## Feature Matrix

| Engine     | Platform            | Online/Offline | SSML | Word Boundaries | Streaming | Playback Control | Callbacks |
|------------|--------------------|--------------------|------|-----------------|-----------|------------------|-----------|
| Polly      | Linux/MacOS/Windows| Online            | Yes  | Yes            | Yes       | Yes              | Full      |
| Google     | Linux/MacOS/Windows| Online            | Yes  | Yes            | Yes       | Yes              | Full      |
| GoogleTrans| Linux/MacOS/Windows| Online            | No*  | No**           | Yes       | Yes              | Basic     |
| Microsoft  | Linux/MacOS/Windows| Online            | Yes  | Yes            | Yes       | Yes              | Full      |
| Watson     | Linux/MacOS/Windows| Online            | Yes  | Yes            | Yes       | Yes              | Full      |
| ElevenLabs | Linux/MacOS/Windows| Online            | No*  | Yes            | Yes       | Yes              | Full      |
| Play.HT    | Linux/MacOS/Windows| Online            | No*  | No**           | Yes       | Yes              | Basic     |
| UpliftAI   | Linux/MacOS/Windows| Online            | No*  | No**           | Yes       | Yes              | Basic     |
| OpenAI   | Linux/MacOS/Windows| Online            | No | No           | Yes       | Yes              | Basic     |
| Wit.Ai     | Linux/MacOS/Windows| Online            | No*  | No**           | Yes       | Yes              | Basic     |
| eSpeak     | Linux/MacOS        | Offline           | Yes  | No**           | Yes       | Yes              | Basic     |
| AVSynth    | MacOS              | Offline           | No   | No**           | Yes       | Yes              | Basic     |
| SAPI       | Windows            | Offline           | Yes  | Yes            | Yes       | Yes              | Full      |
| UWP        | Windows            | Offline           | Yes  | Yes            | Yes       | Yes              | Full      |
| Sherpa-ONNX| Linux/MacOS/Windows| Offline           | No   | No**           | Yes       | Yes              | Basic     |

**Notes**:
- **SSML**: Entries marked with No* indicate that while the engine doesn't support SSML natively, the wrapper will automatically strip SSML tags and process the plain text.
- **Word Boundaries**: Entries marked with No** use an estimation-based timing system that may not be accurate for precise synchronization needs.
- **Callbacks**:
  - "Full" supports accurate word-level timing callbacks, onStart, and onEnd events
  - "Basic" supports onStart and onEnd events, with estimated word timings
- **Playback Control**: All engines support pause, resume, and stop functionality through the wrapper's unified interface
- All engines support the following core features:
  - Voice selection (`set_voice`)
  - Property control (rate, volume, pitch)
  - File output (WAV, with automatic conversion to MP3/other formats)
  - Streaming playback
  - Audio device selection

### Core Methods Available

| Method                    | Description                                  | Availability |
|--------------------------|----------------------------------------------|--------------|
| `speak()`                | Direct speech playback                       | All engines  |
| `speak_streamed()`       | Streamed speech playback                    | All engines  |
| `synth_to_file()`        | Save speech to file                         | All engines  |
| `pause()`, `resume()`    | Playback control                            | All engines  |
| `stop()`                 | Stop playback                               | All engines  |
| `set_property()`         | Control rate/volume/pitch                   | All engines  |
| `get_voices()`           | List available voices                       | All engines  |
| `set_voice()`           | Select voice                                | All engines  |
| `connect()`             | Register event callbacks                    | All engines  |
| `check_credentials()`    | Verify API credentials                      | Online engines|
| `set_output_device()`    | Select audio output device                  | All engines  |

---

## Installation

### Package Name Note

This package is published on PyPI as `py3-tts-wrapper` but installs as `tts-wrapper`. This is because it's a fork of the original `tts-wrapper` project with Python 3 support and additional features.

### System Dependencies

This project requires the following system dependencies on Linux:

```sh
sudo apt-get install portaudio19-dev
```

or MacOS, using [Homebrew](https://brew.sh)

```sh
brew install portaudio
```

For PicoTTS on Debian systems:

```sh
sudo apt-get install libttspico-utils
```

The `espeak` TTS functionality requires the `espeak-ng` C library to be installed on your system:

- **Ubuntu/Debian**: `sudo apt install espeak-ng`
- **macOS**: `brew install espeak-ng`
- **Windows**: Download the binaries from https://espeak.sourceforge.net/

### Using pip

Install from PyPI with selected engines:
```sh
pip install "py3-tts-wrapper[google,microsoft,sapi,sherpaonnx,googletrans]"
```

Install from GitHub:
```sh
pip install "py3-tts-wrapper[google,microsoft,sapi,sherpaonnx,googletrans]@git+https://github.com/willwade/tts-wrapper"
```

Note: On macOS/zsh, you may need to use quotes:
```sh
pip install "py3-tts-wrapper[google,watson,polly,elevenlabs,microsoft,sherpaonnx]"
```



## Usage Guide

### Basic Usage

```python
from tts_wrapper import PollyClient

# Initialize the client - it's also the TTS engine
client = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
ssml_text = client.ssml.add('Hello, <break time="500ms"/> world!')
client.speak(ssml_text)
```

You can use SSML or plain text

```python
from tts_wrapper import PollyClient

# Initialize the client - it's also the TTS engine
client = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
client.speak('Hello world')
```

For a full demo see the examples folder. You'll need to fill out the credentials.json (or credentials-private.json). Use them from cd'ing into the examples folder.
Tips on gaining keys are below.

### Authorization

Each service uses different methods for authentication:

#### Polly

```python
from tts_wrapper import PollyClient
client = PollyClient(credentials=('aws_region','aws_key_id', 'aws_secret_access_key'))
```

#### Google

```python
from tts_wrapper import GoogleClient
client = GoogleClient(credentials=('path/to/creds.json'))
```
or pass the auth file as dict - so in memory

```python
from tts_wrapper import GoogleClient
import json
import os

with open(os.getenv("GOOGLE_SA_PATH"), "r") as file:
    credentials_dict = json.load(file)

client = GoogleClient(credentials=os.getenv('GOOGLE_SA_PATH'))
# Or use the dictionary directly
client = GoogleClient(credentials=credentials_dict)
```

#### Microsoft

```python
from tts_wrapper import MicrosoftTTS
tts = MicrosoftTTS(credentials=('subscription_key', 'subscription_region'))
tts.set_voice('voice_id')
```

#### Watson

```python
from tts_wrapper import WatsonClient
client = WatsonClient(credentials=('api_key', 'region', 'instance_id'))
```

**Note** If you have issues with SSL certification try

```python
from tts_wrapper import WatsonClient
client = WatsonClient(credentials=('api_key', 'region', 'instance_id'),disableSSLVerification=True)
```

#### ElevenLabs

```python
from tts_wrapper import ElevenLabsClient
client = ElevenLabsClient(credentials=('api_key'))
```

- **Note**: ElevenLabs does not support SSML.

#### Wit.Ai

```python
from tts_wrapper import WitAiClient
client = WitAiClient(credentials=('token'))
```

#### Play.HT

```python
from tts_wrapper import PlayHTClient
client = PlayHTClient(credentials=('api_key', 'user_id'))
```

- **Note**: Play.HT does not support SSML, but we automatically strip SSML tags if present.

#### UpliftAI

```python
from tts_wrapper import UpliftAIClient
client = UpliftAIClient(api_key="api_key")
```

#### UWP

```python
from tts_wrapper import UWPClient
client = UWPClient()
```

#### eSpeak

```python
from tts_wrapper import eSpeakClient
client = eSpeakClient()
```

Note: Requires espeak-ng to be installed on your system.

#### SAPI (Windows)

```python
from tts_wrapper import SAPIClient
client = SAPIClient()
```

Note: Only available on Windows systems.

#### AVSynth (macOS)

```python
from tts_wrapper import AVSynthClient
client = AVSynthClient()
```

Note: Only available on macOS. Provides high-quality speech synthesis with word timing support and voice property control.

#### GoogleTrans

Uses the gTTS library for free text-to-speech via Google Translate.

```python
from tts_wrapper import GoogleTransClient

# Initialize with default voice (UK English)
tts = GoogleTransClient()

# Or specify a voice/language
tts = GoogleTransClient(voice_id="en-co.uk")

# Set voice after initialization
tts.set_voice("fr-fr")  # French
```

#### Sherpa-ONNX

You can provide blank model path and tokens path - and we will use a default location..

```python
from tts_wrapper import SherpaOnnxClient
client = SherpaOnnxClient(model_path=None, tokens_path=None)
```

Set a voice like

```python
# Find voices/langs availables
voices = client.get_voices()
print("Available voices:", voices)

# Set the voice using ISO code
iso_code = "eng"  # Example ISO code for the voice - also ID in voice details
client.set_voice(iso_code)
```
and then use speak, speak_streamed etc..

You then can perform the following methods.

### Advanced Usage

#### SSML

Even if you don't use SSML features that much its wise to use the same syntax - so pass SSML not text to all engines

```python
ssml_text = client.ssml.add('Hello world!')
```

#### Plain Text

If you want to keep things simple each engine will convert plain text to SSML if its not.

```python
client.speak('Hello World!')
```

#### Speak

This will use the default audio output of your device to play the audio immediately

```python
client.speak(ssml_text)
```

#### Check Credentials

This will check if the credentials are valid:

```python
tts = MicrosoftTTS(
    credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION"))
)
if tts.check_credentials():
    print("Credentials are valid.")
else:
    print("Credentials are invalid.")
```

NB: Each engine has a different way of checking credentials. If they don't have a specific implementation, the parent class will check get_voices. If you want to save API calls, you can just do a get_voices call directly.

#### Streaming and Playback Control

#### `pause_audio()`, `resume_audio()`, `stop_audio()`
These methods manage audio playback by pausing, resuming, or stopping it.
NB: Only to be used for speak_streamed

You need to make sure the optional dependency is included for this

```sh
pip install py3-tts-wrapper[controlaudio,google.. etc
```

then

```python
client = GoogleClient(credentials="path/to/credentials.json")
try:
    text = "This is a pause and resume test. The text will be longer, depending on where the pause and resume works"
    audio_bytes = client.synth_to_bytes(text)
    client.load_audio(audio_bytes)
    print("Play audio for 3 seconds")
    client.play(1)
    client.pause(8)
    client.resume()
    time.sleep(6)
finally:
    client.cleanup()
```

- the pause and resume are in seconds from the start of the audio
- Please use the cleanup method to ensure the audio is stopped and the audio device is released

NB: to do this we use pyaudio. If you have issues with this you may need to install portaudio19-dev - particularly on linux

```sh
sudo apt-get install portaudio19-dev
```


#### File Output

```python
client.synth_to_file(ssml_text, 'output.mp3', format='mp3')
```
there is also "synth" method which is legacy. Note we support saving as mp3, wav or flac.

```python
client.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3')
```
Note you can also stream - and save. Just note it saves at the end of streaming entirely..

```python
ssml_text = client.ssml.add('Hello world!')

client.speak_streamed(ssml_text, filepath, 'wav')
```


#### Fetch Available Voices

```python
voices = client.get_voices()
print(voices)
```

NB: All voices will have a id, dict of language_codes, name and gender. Just note not all voice engines provide gender

#### Voice Selection

```python
client.set_voice(voice_id, lang_code="en-US")
```

e.g.

```python
client.set_voice('en-US-JessaNeural', 'en-US')
```

Use the id - not a name

#### SSML

```python
ssml_text = client.ssml.add('Hello, <break time="500ms"/> world!')
client.speak(ssml_text)
```

#### Volume, Rate and Pitch Control

Set volume:
```python
client.set_property("volume", "90")
text_read = f"The current volume is 90"
text_with_prosody = client.construct_prosody_tag(text_read)
ssml_text = client.ssml.add(text_with_prosody)
```
- Volume is set on a scale of 0 (silent) to 100 (maximum).
- The default volume is 100 if not explicitly specified.

Set rate:

```python
client.set_property("rate", "slow")
text_read = f"The current rate is SLOW"
text_with_prosody = client.construct_prosody_tag(text_read)
ssml_text = client.ssml.add(text_with_prosody)
```
Speech Rate:
- Rate is controlled using predefined options:
    - x-slow: Very slow speaking speed.
    - slow: Slow speaking speed.
    - medium (default): Normal speaking speed.
    - fast: Fast speaking speed.
    - x-fast: Very fast speaking speed.
- If not specified, the speaking rate defaults to medium.

Set pitch:
```python
client.set_property("pitch", "high")
text_read = f"The current pitch is HIGH"
text_with_prosody = client.construct_prosody_tag(text_read)
ssml_text = client.ssml.add(text_with_prosody)
```
Pitch Control:
- Pitch is adjusted using predefined options that affect the vocal tone:
    - x-low: Very deep pitch.
    - low: Low pitch.
    - medium (default): Normal pitch.
    - high: High pitch.
    - x-high: Very high pitch.
- If not explicitly set, the pitch defaults to medium.

Use the ```client.ssml.clear_ssml()``` method to clear all entries from the ssml list

#### `set_property()`
This method allows setting properties like `rate`, `volume`, and `pitch`.

```python
client.set_property("rate", "fast")
client.set_property("volume", "80")
client.set_property("pitch", "high")
```

#### `get_property()`
This method retrieves the value of properties such as `volume`, `rate`, or `pitch`.

```python
current_volume = client.get_property("volume")
print(f"Current volume: {current_volume}")
```


#### Using callbacks on word-level boundaries

Note only **Polly, Microsoft, Google, ElevenLabs, UWP, SAPI and Watson** can do this **correctly** with precise timing from the TTS engine. All other engines (GoogleTrans, Wit.Ai, Play.HT, OpenAI, eSpeak, AVSynth, Sherpa-ONNX) use **estimated timing** based on text length and average speaking rate.

```python
def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: {word}, Duration: {duration:.3f}s")

def on_start():
    print('Speech started')

def on_end():
    print('Speech ended')

try:
    text = "Hello, This is a word timing test"
    ssml_text = client.ssml.add(text)
    client.connect('onStart', on_start)
    client.connect('onEnd', on_end)
    client.start_playback_with_callbacks(ssml_text, callback=my_callback)
except Exception as e:
    print(f"Error: {e}")
```

and it will output

```bash
Speech started
Word: Hello, Duration: 0.612s
Word: , Duration: 0.212s
Word: This, Duration: 0.364s
Word: is, Duration: 0.310s
Word: a, Duration: 0.304s
Word: word, Duration: 0.412s
Word: timing, Duration: 0.396s
Word: test, Duration: 0.424s
Speech ended
```

#### `connect()`
This method allows registering callback functions for events like `onStart` or `onEnd`.

```python
def on_start():
    print("Speech started")

client.connect('onStart', on_start)
```


## Audio Output Methods

The wrapper provides several methods for audio output, each suited for different use cases:

### 1. Direct Playback

The simplest method - plays audio immediately:
```python
client.speak("Hello world")
```

### 2. Streaming Playback

Recommended for longer texts - streams audio as it's being synthesized:
```python
client.speak_streamed("This is a long text that will be streamed as it's synthesized")
```

### 3. File Output

Save synthesized speech to a file:
```python
client.synth_to_file("Hello world", "output.wav")
```

### 4. Raw Audio Data

For advanced use cases where you need the raw audio data:
```python
# Get raw PCM audio data as bytes
audio_bytes = client.synth_to_bytes("Hello world")
```

### 5. Silent Synthesis

The `synthesize()` method provides silent audio synthesis without playback - perfect for applications that need audio data without immediate playback:

```python
# Get complete audio data (default behavior)
audio_bytes = client.synthesize("Hello world")

# Get streaming audio data for real-time processing
audio_stream = client.synthesize("Hello world", streaming=True)
for chunk in audio_stream:
    # Process each audio chunk as it's generated
    process_audio_chunk(chunk)

# Use with specific voice
audio_bytes = client.synthesize("Hello world", voice_id="en-US-JennyNeural")
```

### Audio Format Notes

- All engines output WAV format by default
- For MP3 or other formats, use external conversion libraries like `pydub`:
  ```python
  from pydub import AudioSegment
  import io

  # Get WAV data
  audio_bytes = client.synth_to_bytes("Hello world")

  # Convert to MP3
  wav_audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
  wav_audio.export("output.mp3", format="mp3")
  ```

---

### Example Use Cases

#### 1. Saving Audio to a File

You can use the `synth_to_bytestream` method to synthesize audio in any supported format and save it directly to a file.

```python
# Synthesize text into a bytestream in MP3 format
bytestream = client.synth_to_bytestream("Hello, this is a test", format="mp3")

# Save the audio bytestream to a file
with open("output.mp3", "wb") as f:
    f.write(bytestream.read())

print("Audio saved to output.mp3")
```

**Explanation**:
- The method synthesizes the given text into audio in MP3 format.
- The `BytesIO` object is then written to a file using the `.read()` method of the `BytesIO` class.

#### 2. Real-Time Playback Using `sounddevice`

If you want to play the synthesized audio live without saving it to a file, you can use the `sounddevice` library to directly play the audio from the `BytesIO` bytestream.

```python
import sounddevice as sd
import numpy as np

# Synthesize text into a bytestream in WAV format
bytestream = client.synth_to_bytestream("Hello, this is a live playback test", format="wav")

# Convert the bytestream back to raw PCM audio data for playback
audio_data = np.frombuffer(bytestream.read(), dtype=np.int16)

# Play the audio using sounddevice
sd.play(audio_data, samplerate=client.audio_rate)
sd.wait()

print("Live playback completed")
```

**Explanation**:
- The method synthesizes the text into a `wav` bytestream.
- The bytestream is converted to raw PCM data using `np.frombuffer()`, which is then fed into the `sounddevice` library for live playback.
- `sd.play()` plays the audio in real-time, and `sd.wait()` ensures that the program waits until playback finishes.

### Manual Audio Control

For advanced use cases where you need direct control over audio playback, you can use the raw audio data methods:

```python
from tts_wrapper import AVSynthClient
import numpy as np
import sounddevice as sd

# Initialize TTS client
client = AVSynthClient()

# Method 1: Direct playback of entire audio
def play_audio_stream(client, text: str):
    """Play entire audio at once."""
    # Get raw audio data
    audio_data = client.synth_to_bytes(text)

    # Convert to numpy array for playback
    samples = np.frombuffer(audio_data, dtype=np.int16)

    # Play the audio
    sd.play(samples, samplerate=client.audio_rate)
    sd.wait()

# Method 2: Chunked playback for more control
def play_audio_chunked(client, text: str, chunk_size: int = 4096):
    """Process and play audio in chunks for more control."""
    # Get raw audio data
    audio_data = client.synth_to_bytes(text)

    # Create a continuous stream
    stream = sd.OutputStream(
        samplerate=client.audio_rate,
        channels=1,  # Mono audio
        dtype=np.int16
    )

    with stream:
        # Process in chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if len(chunk) % 2 != 0:  # Ensure even size for 16-bit audio
                chunk = chunk[:-1]
            samples = np.frombuffer(chunk, dtype=np.int16)
            stream.write(samples)
```

This manual control allows you to:
- Process audio data in chunks
- Implement custom audio processing
- Control playback timing
- Add effects or modifications to the audio
- Implement custom buffering strategies

The chunked playback method is particularly useful for:
- Real-time audio processing
- Custom pause/resume functionality
- Volume adjustment during playback
- Progress tracking
- Memory-efficient handling of long audio

**Note**: Manual audio control requires the `sounddevice` and `numpy` packages:
```sh
pip install sounddevice numpy
```


## Developer's Guide

### Setting up the Development Environment

#### Using Pipenv


1. Clone the repository:
   ```sh
   git clone https://github.com/willwade/tts-wrapper.git
   cd tts-wrapper
   ```

2. Install the package and system dependencies:
   ```sh
   pip install .
   ```

   To install optional dependencies, use:
   ```sh
   pip install .[google, watson, polly, elevenlabs, microsoft]
   ```

This will install Python dependencies and system dependencies required for this project. Note that system dependencies will only be installed automatically on Linux.

#### Using UV

1. [Install UV](https://docs.astral.sh/uv/#getting-started)
   ```sh
   pip install uv
   ```

2. Clone the repository:
   ```sh
   git clone https://github.com/willwade/tts-wrapper.git
   cd tts-wrapper
   ```

3. Install Python dependencies:
   ```sh
   uv sync --all-extras
   ```

4. Install system dependencies (Linux only):
   ```sh
   uv run postinstall
   ```


**NOTE**: to get a requirements.txt file for the project use `uv export --format  requirements-txt --all-extras --no-hashes` juat be warned that this will include all dependencies including dev ones.

## Release a new build

```sh
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

### Adding a New Engine to TTS Wrapper

This guide provides a step-by-step approach to adding a new engine to the existing Text-to-Speech (TTS) wrapper system.

#### Step 1: Create Engine Directory Structure

1. **Create a new folder** for your engine within the `engines` directory. Name this folder according to your engine, such as `witai` for Wit.ai.

   Directory structure:

   ```
   engines/witai/
   ```

2. **Create necessary files** within this new folder:

   - `__init__.py` - Makes the directory a Python package.
   - `client.py` - Handles all interactions with the TTS API and implements the AbstractTTS interface.
   - `ssml.py` - Defines any SSML handling specific to this engine (optional).

   Final directory setup:

   ```
   engines/
   └── witai/
       ├── __init__.py
       ├── client.py
       └── ssml.py
   ```

#### Step 2: Implement Client Functionality in `client.py`

Implement authentication and necessary setup for API connection. This file should manage tasks such as sending synthesis requests and fetching available voices. The client class should inherit from AbstractTTS.

```python
from tts_wrapper.tts import AbstractTTS

class WitAiClient(AbstractTTS):
    def __init__(self, credentials=None):
        super().__init__()
        self.token = credentials[0] if credentials else None
        self.audio_rate = 24000  # Default sample rate for this engine
        # Setup other necessary API connection details here

    def _get_voices(self):
        # Code to retrieve available voices from the TTS API
        # Return raw voice data that will be processed by the base class
        pass

    def synth_to_bytes(self, text, voice_id=None):
        # Code to send a synthesis request to the TTS API
        # Return raw audio bytes
        pass

    def synth(self, text, output_file, output_format="wav", voice_id=None):
        # Code to synthesize speech and save to a file
        pass
```

#### Step 3: Implement SSML Handling (if needed)

If the engine has specific SSML requirements or supports certain SSML tags differently, implement this logic in `ssml.py`.

```python
from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode

class WitAiSSML(BaseSSMLRoot):
    def add_break(self, time='500ms'):
        self.root.add(SSMLNode('break', attrs={'time': time}))
```

#### Step 4: Update `__init__.py`

Make sure the `__init__.py` file properly imports and exposes the client class.

```python
from .client import WitAiClient
```

#### NB: Credentials Files

You can store your credentials in either:
- `credentials.json` - For development
- `credentials-private.json` - For private credentials (should be git-ignored)

Example structure (do NOT commit actual credentials):
```json
{
    "Polly": {
        "region": "your-region",
        "aws_key_id": "your-key-id",
        "aws_access_key": "your-access-key"
    },
    "Microsoft": {
        "token": "your-subscription-key",
        "region": "your-region"
    }
}
```

### Service-Specific Setup

#### AWS Polly
- [Create an AWS account](https://aws.amazon.com/free)
- [Set up IAM credentials](https://docs.aws.amazon.com/polly/latest/dg/setting-up.html)
- [Polly API Documentation](https://docs.aws.amazon.com/polly/latest/dg/API_Operations.html)

#### Microsoft Azure
- [Create an Azure account](https://azure.microsoft.com/free)
- [Create a Speech Service resource](https://docs.microsoft.com/azure/cognitive-services/speech-service/get-started)
- [Azure Speech Service Documentation](https://docs.microsoft.com/azure/cognitive-services/speech-service/rest-text-to-speech)

#### Google Cloud
- [Create a Google Cloud account](https://cloud.google.com/free)
- [Set up a service account](https://cloud.google.com/text-to-speech/docs/quickstart-client-libraries)
- [Google TTS Documentation](https://cloud.google.com/text-to-speech/docs)

#### IBM Watson
- [Create an IBM Cloud account](https://cloud.ibm.com/registration)
- [Create a Text to Speech service instance](https://cloud.ibm.com/catalog/services/text-to-speech)
- [Watson TTS Documentation](https://cloud.ibm.com/apidocs/text-to-speech)

#### ElevenLabs
- [Create an ElevenLabs account](https://elevenlabs.io/)
- [Get your API key](https://docs.elevenlabs.io/authentication)
- [ElevenLabs Documentation](https://docs.elevenlabs.io/)

#### Play.HT
- [Create a Play.HT account](https://play.ht/)
- [Get your API credentials](https://docs.play.ht/reference/api-getting-started)
- [Play.HT Documentation](https://docs.play.ht/)

#### Wit.AI
- [Create a Wit.ai account](https://wit.ai/)
- [Create a new app and get token](https://wit.ai/docs/quickstart)
- [Wit.ai Documentation](https://wit.ai/docs)

## License

This project is licensed under the [MIT License](./LICENSE).
