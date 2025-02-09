# py3-TTS-Wrapper

[![PyPI version](https://badge.fury.io/py/py3-tts-wrapper.svg)](https://badge.fury.io/py/py3-tts-wrapper)
[![codecov](https://codecov.io/gh/willwade/py3-tts-wrapper/branch/master/graph/badge.svg?token=79IG7GAK0B)](https://codecov.io/gh/willwade/py3-tts-wrapper)

> **Contributions are welcome! Check our [contribution guide](./CONTRIBUTING.md).**

_TTS-Wrapper_ simplifies using text-to-speech APIs by providing a unified interface across multiple services, allowing easy integration and manipulation of TTS capabilities.


## Supported Services

- AWS Polly
- Google TTS
- Microsoft Azure TTS
- IBM Watson
- ElevenLabs
- Wit.Ai 
- eSpeak-NG
- Play.HT


### Experimental (Not fully featured or in a state of WIP)

- PicoTTS
- UWP (WinRT) Speech system (win 10+)
- Sherpa-Onnx (focusing on MMS models for now)
- SAPI/NSSS (Microsoft Speech API)/NSSS


## Features
- **Text to Speech**: Convert text into spoken audio.
- **SSML Support**: Use Speech Synthesis Markup Language to enhance speech synthesis.
- **Voice and Language Selection**: Customize the voice and language for speech synthesis.
- **Streaming and Direct Play**: Stream audio or play it directly.
- **Pause, Resume, and Stop Controls**: Manage audio playback dynamically.
- **File Output**: Save spoken audio to files in various formats.
- **Unified Voice handling** Get Voices across all TTS engines with alike keys
- **Volume, Pitch, and Rate Controls** Control volume, pitch and rate with unified methods


## Feature set overview

| Engine     | OS                  | Online/Offline | SSML | Rate/Volume/Pitch | onWord events |
|------------|---------------------|----------------|------|-------------------|---------------|
| Polly      | Linux/MacOS/Windows | Online         | Yes  | Yes               | Yes           |
| Google     | Linux/MacOS/Windows | Online         | Yes  | Yes               | Yes           |
| Azure      | Linux/MacOS/Windows | Online         | Yes  | Yes               | Yes           |
| Watson     | Linux/MacOS/Windows | Online         | Yes  | No                | Yes           |
| ElevenLabs | Linux/MacOS/Windows | Online         | No   | Yes               | Yes           |
| Wit.AI     | Linux/MacOS/Windows | Online         | Yes  | No                | No            |
| Play.HT    | Linux/MacOS/Windows | Online         | No   | Yes               | No            |
| Sherpa-Onnx| Linux/MacOS/Windows | Offline        | No   | No                | No            |
| gTTS       | Linux/MacOS/Windows | Online         | No   | No                | No            |
| UWP        | Windows             | Offline        | No   | Yes               | No            |
| SAPI       | Windows             | Offline        | Yes  | Yes               | Yes           |
| NSS        | MacOS               | Offline        | Yes  | Yes               | Yes           |
| eSpeak     | Linux/MacOS/Windows | Offline        | Yes  | Yes               | Yes           |


### Methods for each engine

| Method                    | Description                                  | Available Engines       |
|---------------------------|----------------------------------------------|-------------------------|
| `speak()`                 | Plays synthesized speech directly.           | All engines             |
| `synth_to_file()`         | Synthesizes speech and saves it to a file.   | All engines             |
| `speak_streamed()`        | Streams synthesized speech.                  | All engines             |
| `set_property()`          | Sets properties like rate, volume, pitch.    | All engines             |
| `get_voices()`            | Retrieves available voices.                  | All engines             |
| `connect()`               | Connects callback functions for events.      | Polly, Microsoft, Google, Watson, eSpeak |
| `pause_audio()`           | Pauses ongoing speech playback.              | All engines             |
| `resume_audio()`          | Resumes paused speech playback.              | All engines             |
| `stop_audio()`            | Stops ongoing speech playback.               | All engines             |
| `set_output_device('id')` | Stops ongoing speech playback.               | All engines             |
| `check_credentials()`     | True or False if Credentials are ok          | All engines             |

**Notes**:

* For SSML where it says  'no' you can send the engine SSML we will just strip it
* For onWord Events. For Engines where it is a no we have a very bad fallback mechanism which will emit word timings based on estimation. You cant rely on this for accurate use cases. 


## Install

### System Dependencies

This project requires the following system dependencies on Linux:

```sh
sudo apt-get insall portaudio19-dev
```

or MacOS, using [Homebrew](https://brew.sh)

```sh
brew install portaudio
```

For PicoTTS on Debian systems:

```sh
sudo apt-get install libttspico-utils
```

The `espeak` TTS functionality requires the `eSpeak` C library to be installed on your system.

- **Ubuntu/Debian**: `sudo apt install espeak-ng`
- **macOS**: `brew install espeak-ng`
- **Windows**: Download the binaries from https://espeak.sourceforge.net/

### Using pip

```sh
pip install py3-tts-wrapper[google,microsoft,sapi,sherpaonnx,googletrans]
```
or via git

```sh
pip install git+https://github.com/willwade/tts-wrapper#egg=tts-wrapper[google,microsoft,sapi,mms,sherpaonnx]
```

or (the newer way we should all use)

```sh
pip install tts-wrapper[google,microsoft,sapi,sherpaonnx,googletrans]@git+https://github.com/willwade/tts-wrapper
```


NB: On MacOS(/zsh) you may need to do use quotes

```sh
pip install py3-tts-wrapper"[google, watson, polly, elevenlabs, microsoft, mms, sherpaonnx]"
```



## Basic Usage

```python
from tts_wrapper import PollyClient
pollyClient = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))

from tts_wrapper import PollyTTS

tts = PollyTTS(pollyClient)
ssml_text = tts.ssml.add('Hello, <break time="500ms"/> world!')
tts.speak(ssml_text)
```

You can use SSML or plain text

```python
from tts_wrapper import PollyClient
pollyClient = PollyClient(credentials=('aws_key_id', 'aws_secret_access_key'))
from tts_wrapper import PollyTTS

tts = PollyTTS(pollyClient)
tts.speak('Hello world')
```

For a full demo see the examples folder. You'll need to fill out the credentials.json (or credentials-private.json). Use them from cd'ing into the examples folder. 
Tips on gaining keys are below.

## Authorization
Each service uses different methods for authentication:

### Polly

```python
from tts_wrapper import PollyTTS, PollyClient
client = PollyClient(credentials=('aws_region','aws_key_id', 'aws_secret_access_key'))

tts = PollyTTS(client)
```

### Google

```python
from tts_wrapper import GoogleTTS, GoogleClient
client = GoogleClient(credentials=('path/to/creds.json'))

tts = GoogleTTS(client)
```
or pass the auth file as dict - so in memory

```python
from tts_wrapper import GoogleTTS, GoogleClient

with open(os.getenv("GOOGLE_SA_PATH"), "r") as file:
    credentials_dict = json.load(file)

client = GoogleClient(credentials=os.getenv('GOOGLE_SA_PATH'))
client = GoogleClient(credentials=credentials_dict)]
```

### Microsoft

```python
from tts_wrapper import MicrosoftTTS, MicrosoftClient
client = MicrosoftClient(credentials=('subscription_key','subscription_region'))

tts = MicrosoftTTS(client)
```

### Watson

```python
from tts_wrapper import WatsonTTS, WatsonClient
client = WatsonClient(credentials=('api_key', 'region', 'instance_id'))

tts = WatsonTTS(client)
```

**Note** If you have issues with SSL certification try

```python
from tts_wrapper import WatsonTTS, WatsonClient
client = WatsonClient(credentials=('api_key', 'region', 'instance_id'),disableSSLVerification=True)

tts = WatsonTTS(client)
```

### ElevenLabs

```python
from tts_wrapper import ElevenLabsTTS, ElevenLabsClient
client = ElevenLabsClient(credentials=('api_key'))
tts = ElevenLabsTTS(client)
```

- **Note**: ElevenLabs does not support SSML.

### Wit.Ai

```python
from tts_wrapper import WitAiTTS, WitAiClient
client = WitAiClient(credentials=('token'))
tts = WitAiTTS(client)
```

### Play.HT

```python
from tts_wrapper import PlayHTClient, PlayHTTTS
client = PlayHTClient(credentials=('api_key', 'user_id'))
tts = PlayHTTTS(client)
```

- **Note**: Play.HT does not support SSML, but we automatically strip SSML tags if present.

### UWP

```python
from tts_wrapper import UWPTTS, UWPClient
client = UWPClient()
tts = UWPTTS(client)
```

### eSpeak

```python
from tts_wrapper import eSpeakClient, eSpeakTTS

client = eSpeakClient()
tts = eSpeakTTS(client)

```

Note: It relies on know extra libraries except you need to instal espeak-ng

### SAPI/eSpeak/NSSS

```python
from tts_wrapper import SystemTTSClient, SystemTTS
client = SystemTTSClient('espeak') # eSpeak
client = SystemTTSClient('sapi') #SAPI
client = SystemTTSClient('nsss') #NSSS MacOS
# Initialize the TTS engine
tts = SystemTTSClient(client)
```

**Just note: We cant do word timings in this.**


### GoogleTrans

Uses the gTTS library. 

```python
from tts_wrapper import GoogleTransClient, GoogleTransTTS
voice_id = "en-co.uk"  # Example voice ID for UK English
client = GoogleTransClient(voice_id)
# Initialize the TTS engine
tts = GoogleTransTTS(client)
```

### Sherpa-ONNX

You can provide blank model path and tokens path - and we will use a default location.. 
AS NOTED - WE HAVE DESIGNED THIS RIGHT NOW FOR MMS MODELS! We will add others like piper etc to this - Infact I'll drop regular piper support for sherpa-onnx. Its less of a headache..

```python
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
client = SherpaOnnxClient(model_path=None, tokens_path=None)
tts = SherpaOnnxTTS(client)
```

Set a voice like

```python
# Find voices/langs availables
voices = tts.get_voices()
print("Available voices:", voices)

# Set the voice using ISO code
iso_code = "eng"  # Example ISO code for the voice - also ID in voice details
tts.set_voice(iso_code)
```
and then use speak, speak_streamed etc.. 

You then can perform the following methods.

## Advanced Usage

### SSML

Even if you don't use SSML features that much its wise to use the same syntax - so pass SSML not text to all engines

```python
ssml_text = tts.ssml.add('Hello world!')
```

### Plain Text

If you want to keep things simple each engine will convert plain text to SSML if its not.

```python
tts.speak('Hello World!')
```

### Speak 

This will use the default audio output of your device to play the audio immediately

```python
tts.speak(ssml_text)
```

### Check Credentials

This will check if the credentials are valid. Its only on the client object. Eg

```python

    client = MicrosoftClient(
        credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION"))
    )
    if client.check_credentials():
        print("Credentials are valid.")
    else:
        print("Credentials are invalid."

```

NB: Each engine has a different way of checking credentials. If they dont have a supported the parent class will check get_voices. If you want to save calls just do a get_voices call.

### Streaming and Playback Control

### `pause_audio()`, `resume_audio()`, `stop_audio()`
These methods manage audio playback by pausing, resuming, or stopping it.
NB: Only to be used for speak_streamed

You need to make sure the optional dependency is included for this

```sh
pip install py3-tts-wrapper[controlaudio,google.. etc
```

then

```python

client = GoogleClient(..)
tts = GoogleTTS(client)
try:
    text = "This is a pause and resume test. The text will be longer, depending on where the pause and resume works"
    audio_bytes = tts.synth_to_bytes(text)
    tts.load_audio(audio_bytes)
    print("Play audio for 3 seconds")
    tts.play(1)
    tts.pause(8)
    tts.resume()
    time.sleep(6)
finally:
    tts.cleanup()

```

- the pause and resume are in seconds from the start of the audio
- Please use the cleanup method to ensure the audio is stopped and the audio device is released

NB: to do this we use pyaudio. If you have issues with this you may need to install portaudio19-dev - particularly on linux

```sh
sudo apt-get install portaudio19-dev
```


### File Output

```python
tts.synth_to_file(ssml_text, 'output.mp3', format='mp3')
```
there is also "synth" method which is legacy. Note we support saving as mp3, wav or flac. 

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
```
Note you can also stream - and save. Just note it saves at the end of streaming entirely..

```python
ssml_text = tts.ssml.add('Hello world!')

tts.speak_streamed(ssml_text,filepath,'wav')
```


### Fetch Available Voices

```python
voices = tts.get_voices()
print(voices)
```

NB: All voices will have a id, dict of language_codes, name and gender. Just note not all voice engines provide gender

### Voice Selection

```python
tts.set_voice(voice_id,lang_code=en-US)
```

e.g.

```python
tts.set_voice('en-US-JessaNeural','en-US')
```

Use the id - not a name

### SSML

```python
ssml_text = tts.ssml.add('Hello, <break time="500ms"/> world!')
tts.speak(ssml_text)
```

### Volume, Rate and Pitch Control

Set volume:
```python
tts.set_property("volume", "90")
text_read = f"The current volume is 90"
text_with_prosody = tts.construct_prosody_tag(text_read)
ssml_text = tts.ssml.add(text_with_prosody)
```
- Volume is set on a scale of 0 (silent) to 100 (maximum).
- The default volume is 100 if not explicitly specified.

Set rate:

```python
tts.set_property("rate", "slow")
text_read = f"The current rate is SLOW"
text_with_prosody = tts.construct_prosody_tag(text_read)
ssml_text = tts.ssml.add(text_with_prosody)
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
tts.set_property("pitch", "high")
text_read = f"The current pitch is SLOW"
text_with_prosody = tts.construct_prosody_tag(text_read)
ssml_text = tts.ssml.add(text_with_prosody)
```
Pitch Control:
- Pitch is adjusted using predefined options that affect the vocal tone:
    - x-low: Very deep pitch.
    - low: Low pitch.
    - medium (default): Normal pitch.
    - high: High pitch.
    - x-high: Very high pitch.
- If not explicitly set, the pitch defaults to medium.

Use the ```tts.ssml.clear_ssml()``` method to clear all entries from the ssml list

### `set_property()`
This method allows setting properties like `rate`, `volume`, and `pitch`.

```python
tts.set_property("rate", "fast")
tts.set_property("volume", "80")
tts.set_property("pitch", "high")
```

### `get_property()`
This method retrieves the value of properties such as `volume`, `rate`, or `pitch`.

```python
current_volume = tts.get_property("volume")
print(f"Current volume: {current_volume}")
```


### Using callbacks on word-level boundaries

Note only **Polly, Microsoft, Google, ElevenLabs, UWP, SAPI and Watson** can do this **correctly**. We can't do this in anything else but we do do a estimated tonings for all other engines (ie elevenlabs, witAi and Piper)

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
    ssml_text = tts.ssml.add(text)
    tts.connect('onStart', on_start)
    tts.connect('onEnd', on_end)
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
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

### `connect()`
This method allows registering callback functions for events like `onStart` or `onEnd`.

```python
def on_start():
    print("Speech started")

tts.connect('onStart', on_start)
```


## Supported File Formats

By default, all engines output audio in the WAV format, but can be configured to output MP3 or other formats where supported.

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
```

The `synth_to_bytestream` method is designed to synthesize text into an in-memory bytestream in the specified audio format (`wav`, `mp3`, `flac`, etc.). It is particularly useful when you want to handle the audio data in-memory for tasks like saving it to a file, streaming the audio, or passing it to another system for processing.

#### Method Signature:

```python
def synth_to_bytestream(self, text: Any, format: Optional[str] = "wav") -> BytesIO:
    """
    Synthesizes text to an in-memory bytestream in the specified audio format.

    :param text: The text to synthesize.
    :param format: The audio format (e.g., 'wav', 'mp3', 'flac'). Default: 'wav'.
    :return: A BytesIO object containing the audio data.
    """
```

#### Parameters:
- **text**: The text to be synthesized into audio.
- **format**: The audio format in which the synthesized audio should be returned. Default is `wav`. Supported formats include `wav`, `mp3`, and `flac`.

#### Returns:
- **BytesIO**: A `BytesIO` object containing the audio data in the requested format. This can be used directly to save to a file or for playback in real-time.

---

### Example Use Cases

#### 1. Saving Audio to a File

You can use the `synth_to_bytestream` method to synthesize audio in any supported format and save it directly to a file.

```python
# Synthesize text into a bytestream in MP3 format
bytestream = tts.synth_to_bytestream("Hello, this is a test", format="mp3")

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
bytestream = tts.synth_to_bytestream("Hello, this is a live playback test", format="wav")

# Convert the bytestream back to raw PCM audio data for playback
audio_data = np.frombuffer(bytestream.read(), dtype=np.int16)

# Play the audio using sounddevice
sd.play(audio_data, samplerate=tts.audio_rate)
sd.wait()

print("Live playback completed")
```

**Explanation**:
- The method synthesizes the text into a `wav` bytestream.
- The bytestream is converted to raw PCM data using `np.frombuffer()`, which is then fed into the `sounddevice` library for live playback.
- `sd.play()` plays the audio in real-time, and `sd.wait()` ensures that the program waits until playback finishes.



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
   uv sync
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
   - `client.py` - Handles all interactions with the TTS API.
   - `engine.py` - Contains the TTS class that integrates with your abstract TTS system.
   - `ssml.py` - Defines any SSML handling specific to this engine.

   Final directory setup:

   ```
   engines/
   └── witai/
       ├── __init__.py
       ├── client.py
       ├── engine.py
       └── ssml.py
   ```

#### Step 2: Implement Client Functionality in `client.py`

Implement authentication and necessary setup for API connection. This file should manage tasks such as sending synthesis requests and fetching available voices.

```python
class TTSClient:
    def __init__(self, api_key):
        self.api_key = api_key
        # Setup other necessary API connection details here

    def synth(self, text, options):
        # Code to send a synthesis request to the TTS API
        pass

    def get_voices(self):
        # Code to retrieve available voices from the TTS API
        pass
```

#### Step 3: Define the TTS Engine in `engine.py`

This class should inherit from the abstract TTS class and implement required methods such as `get_voices` and `synth_to_bytes`.

```python
from .client import TTSClient
from your_tts_module.abstract_tts import AbstractTTS

class WitTTS(AbstractTTS):
    def __init__(self, api_key):
        super().__init__()
        self.client = TTSClient(api_key)

    def get_voices(self):
        return self.client.get_voices()

    def synth_to_bytes(self, text, format='wav'):
        return self.client.synth(text, {'format': format})
```

#### Step 4: Implement SSML Handling in `ssml.py`

If the engine has specific SSML requirements or supports certain SSML tags differently, implement this logic here.

```python
from your_tts_module.abstract_ssml import BaseSSMLRoot, SSMLNode

class EngineSSML(BaseSSMLRoot):
    def add_break(self, time='500ms'):
        self.root.add(SSMLNode('break', attrs={'time': time}))
```

#### Step 5: Update `__init__.py`

Make sure the `__init__.py` file properly imports and exposes the TTS class and any other public classes or functions from your engine.

```python
from .engine import WitTTS
from .ssml import EngineSSML
```


## Tips

### Getting keys

#### Watson

This is not straightforward

#### Polly


#### Microsoft 

* You first need an Azure subscription - [Create one for free](https://azure.microsoft.com/free/cognitive-services).
* [Create a Speech resource](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices) in the Azure portal.
* Your Speech resource key and region. After your Speech resource is deployed, select Go to resource to view and manage keys. For more information about Azure AI services resources, see [Get the keys for your resource](https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource?pivots=azportal#get-the-keys-for-your-resource)


#### Google

Create a Service Account:

1. Go to the Google Cloud Console: Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a New Project: If you don't already have a project, create a new one in the developer console.
3. Enable APIs: Enable the APIs that your service account will be using. For example, if you're using Google Drive API, enable that API for your project.
4. Create a Service Account:

* In the Google Cloud Console, navigate to "IAM & Admin" > "Service accounts."
* Click on "Create Service Account."
* Enter a name for the service account and an optional description.
* Choose the role for the service account. This determines the permissions it will have.
* Click "Continue" to proceed.

5. Create and Download Credentials:

* On the next screen, you can grant the service account a role in your project. You can also skip this step and grant roles later.
* Click "Create Key" to create and download the JSON key file. This file contains the credentials for your service account.
* Keep this JSON file secure and do not expose it publicly.


#### Wit.Ai

1. https://wit.ai/apps
2. Look for `Bearer` token. Its in the Curl example

#### ElevenLabs

1. Login at https://elevenlabs.io/app/speech-synthesis
2. Go to your profile and click on "Profile + API Key"
3. Click on Popup and copy "API Key"

#### Play.HT

1. Sign up at https://play.ht/
2. Go to your dashboard and click on "API Access"
3. You'll need two pieces of information:
   * API Key: Found under "API Key" section
   * User ID: Found under "User ID" section
4. Keep both the API Key and User ID secure and do not expose them publicly

## License

This project is licensed under the [MIT License](./LICENSE).
