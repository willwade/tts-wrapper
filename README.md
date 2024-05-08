# TTS-Wrapper

[![PyPI version](https://badge.fury.io/py/tts-wrapper.svg)](https://badge.fury.io/py/tts-wrapper)
![build](https://github.com/mediatechlab/tts-wrapper/workflows/build/badge.svg)
[![codecov](https://codecov.io/gh/mediatechlab/tts-wrapper/branch/master/graph/badge.svg?token=79IG7GAK0B)](https://codecov.io/gh/mediatechlab/tts-wrapper)
[![Maintainability](https://api.codeclimate.com/v1/badges/b327dda20742c054bcf0/maintainability)](https://codeclimate.com/github/mediatechlab/tts-wrapper/maintainability)

> ## **Contributions are welcome! Check our [contribution guide](./CONTRIBUTING.md).**

_TTS-Wrapper_ makes it easier to use text-to-speech APIs by providing a unified and easy-to-use interface.

Currently the following services are supported:

- AWS Polly
- Google TTS
- Microsoft TTS
- IBM Watson
- ElevenLabs
- PicoTTS
- SAPI (Microsoft Speech API)

## Installation

Install using pip.

```sh
pip install TTS-Wrapper
```

**Note: for each service you want to use, you have to install the required packages.**

Example: to use `google` and `watson`:

```sh
pip install TTS-Wrapper[google, watson]
```

For PicoTTS you need to install the package on your machine. For Debian (Ubuntu and others) install the package `libttspico-utils` and for Arch (Manjaro and others) there is a package called `aur/pico-tts`.

**Note: If you get an error installing this like "bad pattern: TTS-Wrapper[..." then try using quotes e.g. `pip install "TTS-Wrapper[google, watson]"`**

## Usage

Simply instantiate an object from the desired service and call `synth()`.

```Python
from tts_wrapper import PollyTTS, PollyClient

tts = PollyTTS(client=PollyClient())
tts.synth('<speak>Hello, world!</speak>', 'hello.wav')
```

Notice that you must create a client object to work with your service. Each service uses different authorization techniques. Check out [the documentation](#authorization) to learn more.

### Selecting a Voice

You can change the default voice and lang like this:

```Python
PollyTTS(voice='Camila', lang='pt-BR')
```

Check out the list of available voices for [Polly](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html), [Google](https://cloud.google.com/text-to-speech/docs/voices), [Microsoft](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/rest-text-to-speech#get-a-list-of-voices), and [Watson](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-voices).

### SSML

You can also use [SSML](https://en.wikipedia.org/wiki/Speech_Synthesis_Markup_Language) markup to control the output of compatible engines.

```Python
tts.synth('<speak>Hello, <break time="3s"/> world!</speak>', 'hello.wav')
```

It is recommended to use the `ssml` attribute that will create the correct boilerplate tags for each engine:

```Python
tts.synth(tts.ssml.add('Hello, <break time="3s"/> world!'), 'hello.wav')
```

Learn which tags are available for each service: [Polly](https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html), [Google](https://cloud.google.com/text-to-speech/docs/ssml), [Microsoft](https://docs.microsoft.com/en-us/cortana/skills/speech-synthesis-markup-language), and [Watson](https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-ssml).

### Authorization

To setup credentials to access each engine, create the respective client.

#### Polly

If you don't explicitly define credentials, `boto3` will try to find them in your system's credentials file or your environment variables. However, you can specify them with a tuple:

```Python
from tts_wrapper import PollyClient
client = PollyClient(credentials=(region, aws_key_id, aws_access_key))
```

#### Google

Point to your [Oauth 2.0 credentials file](https://developers.google.com/identity/protocols/OAuth2) path:

```Python
from tts_wrapper import GoogleClient
client = GoogleClient(credentials='path/to/creds.json')
```

#### Microsoft

Just provide your [subscription key](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/rest-text-to-speech#authentication), like so:

```Python
from tts_wrapper import MicrosoftClient
client = MicrosoftClient(credentials='TOKEN')
```

If your region is not the default "useast", you can change it like so:

```Python
client = MicrosoftClient(credentials='TOKEN', region='brazilsouth')
```

#### Watson

Pass your [API key and URL](https://cloud.ibm.com/apidocs/text-to-speech/text-to-speech#authentication) to the initializer:

```Python
from tts_wrapper import WatsonClient
client = WatsonClient(credentials=('API_KEY', 'API_URL'))
```

#### PicoTTS & SAPI

These clients dont't require authorization since they run offline.

```Python
from tts_wrapper import PicoClient, SAPIClient
client = PicoClient()
# or
client = SAPIClient()
```

## File Format

By default, all audio will be a wave file but you can change it to a mp3 using the `format` option:

```Python
tts.synth('<speak>Hello, world!</speak>', 'hello.mp3', format='mp3)
```

## License

Licensed under the [MIT License](./LICENSE).
