
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
- Wit.Ai 


### Experimental (Not fully featured or in a state of WIP)

- PicoTTS
- UWP (WinRT) Speech system (win 10+)
- Sherpa-Onnx (focusing on MMS models for now)
- gTTS (GoogleTranslation TTS.)
- eSpeak/SAPI (Microsoft Speech API)/NSSS


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
| Sherpa-Onnx| Linux/MacOS/Windows | Offline        | No   | No                | No            |
| gTTS       | Linux/MacOS/Windows | Online         | No   | No                | No            |
| UWP        | Windows             | Offline        | No   | Yes               | No            |
| SAPI       | Windows             | Offline        | Yes  | Yes               | Yes           |
| NSS        | MacOS               | Offline        | Yes  | Yes               | Yes           |
| eSpeak     | Linux/MacOS/Windows | Offline        | No   | Yes               | No            |

**Notes**:

* For methods like speak, speak_streamed etc, these are supported by all engines. The table above is really those features where it can't be matched across the board. 
* For SSML where it says  'no' you can send the engine SSML we will just strip it
* For onWord Events. For Engines where it is a no we have a very bad fallback mechanism which will emit word timings based on estimation. You cant rely on this for accurate use cases. 

## To-Do

- Add more tests and logging code for better debugging and exception handling. (see tests/ we do have examples/ where we are doing some quick real-world testing but the tests dir is where we should focus efforts)
- Verify the functionality of UWP (Universal Windows Platform). Not tested. 
- Investigate other audio engines. PyAudio is a pain to install on Linux 
- Piper needs a lot of work. Its playing at strange speeds. 

and an aside

- Explore the possibilities of using libraries like [OpenTTS](https://github.com/synesthesiam/opentts/) and [Orca](https://github.com/synesthesiam/orca).

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

### UWP

```python
from tts_wrapper import UWPTTS, UWPClient
client = UWPClient()
tts = UWPTTS(client)
```

### SAPI/eSpeak/NSSS

```python
from tts_wrapper import SAPIClient, SAPITTS
client = SAPIClient('espeak') # eSpeak
client = SAPIClient('sapi') #SAPI
client = SAPIClient('nsss') #NSSS MacOS
# Initialize the TTS engine
tts = SAPITTS(client)
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

### Streaming and Playback Control

```python
tts.speak_streamed(ssml_text)

tts.pause_audio()
tts.resume_audio()
tts.stop_audio()
```

here's an example of this in use

```python
ssml_text = tts.ssml.add('Hello world!')

tts.speak_streamed(ssml_text)
input("Press enter to pause...")
tts.pause_audio()
input("Press enter to resume...")
tts.resume_audio()
input("Press enter to stop...")
tts.stop_audio()
```

### File Output

```python
tts.synth_to_file(ssml_text, 'output.mp3', format='mp3')
```
there is also "synth" method which is legacy

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
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

## Supported File Formats

By default, all engines output audio in the WAV format, but can be configured to output MP3 or other formats where supported.

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
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

#### Using Poetry

1. Clone the repository:
   ```sh
   git clone https://github.com/willwade/tts-wrapper.git
   cd tts-wrapper
   ```

2. Install Python dependencies:
   ```sh
   poetry install
   ```

3. Install system dependencies (Linux only):
   ```sh
   poetry run postinstall
   ```


**NOTE**: to get a requirements.txt file for the project use `poetry export --without-hashes --format=requirements.txt > requirements.txt --all-extras` juat be warned that this will include all dependencies including dev ones.

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

## License

This project is licensed under the [MIT License](./LICENSE).
