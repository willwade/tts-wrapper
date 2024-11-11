import json
import os
import unittest

from tts_wrapper import (
    SAPITTS,
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
    GoogleTransClient,
    GoogleTransTTS,
    GoogleTTS,
    MicrosoftClient,
    MicrosoftTTS,
    PollyClient,
    PollyTTS,
    SAPIClient,
    SherpaOnnxClient,
    SherpaOnnxTTS,
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
)

#from load_credentials import load_credentials
# Load credentials
#load_credentials('credentials-private.json')
services = ["polly","google","microsoft", "watson", "elevenlabs", "witai", "googletrans", "sherpaonnx", "sapi"]

TTS_CLIENTS = {
    "polly": {
        "client": PollyClient,
        "class": PollyTTS,
        "credential_keys": ["POLLY_REGION", "POLLY_AWS_KEY_ID", "POLLY_AWS_ACCESS_KEY"],
    },
    "google": {
        "client": GoogleClient,
        "class": GoogleTTS,
        "credential_keys": ["GOOGLE_CREDS_PATH"],
    },
    "microsoft": {
        "client": MicrosoftClient,
        "credential_keys": ["MICROSOFT_TOKEN", "MICROSOFT_REGION"],
        "class": MicrosoftTTS,
    },
    "watson": {
        "client": WatsonClient,
        "credential_keys": ["WATSON_API_KEY","WATSON_REGION", "WATSON_INSTANCE_ID"],
        "class": WatsonTTS,
    },
    "elevenlabs": {
        "client": ElevenLabsClient,
        "credential_keys" : ["ELEVENLABS_API_KEY"],
        "class": ElevenLabsTTS,
    },
    "witai": {
        "client": WitAiClient,
        "credential_keys": ["WITAI_TOKEN"],
        "class": WitAiTTS,
    },
    "googletrans": {
        "client_lambda": lambda: GoogleTransClient("en-co.uk"),
        "class": GoogleTransTTS,
    },
    "sherpaonnx": {
        "client_lambda": lambda: SherpaOnnxClient(model_path=None, tokens_path=None),
        "class": SherpaOnnxTTS,
    },
        "sapi": {
        "client_lambda": lambda: SAPIClient(),
        "class": SAPITTS,
    },
}

class ClientManager:
    def __init__(self, credentials_file="credentials-private.json") -> None:
        self.credentials_file = credentials_file
        self.credentials = self.load_credentials()

    def load_credentials(self):
        json_vars = {}
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file) as file:
                data = json.load(file)
                for service, creds in data.items():
                    for key, value in creds.items():
                        env_var = f"{service.upper()}_{key.upper()}"
                        json_vars[env_var] = value
        return json_vars

    def get_credential(self, key):
        return self.credentials.get(key) or os.getenv(key)

    def create_dynamic_client(self, config):
        if "client_lambda" in config:
            # For clients with predefined lambda functions
            return config["client_lambda"]()
        if "client" in config:
            # For clients that need credentials
            client_class = config["client"]
            credential_keys = config.get("credential_keys", [])

            if isinstance(credential_keys, (list, tuple)):
                args = [self.get_credential(key) for key in credential_keys]
                if len(args) == 1:
                    args=str(args[0])
                return client_class(credentials=args)
            msg = "credential_keys must be a tuple"
            raise ValueError(msg)
        msg = "Config must contain either 'client' or 'client_lambda'"
        raise ValueError(msg)

    def create_tts_instances(self, client_configs):
        tts_instances = {}
        for name, config in client_configs.items():
            client = self.create_dynamic_client(config)
            tts_class = config["class"]
            tts_instances[name] = tts_class(client)
        return tts_instances

class TestFileCreation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.success_count = 0

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self) -> None:
        self.google_filename = "google-test.wav"
        self.googletrans_filename = "googletrans-test.wav"
        self.elevenlabs_filename = "elevenlabs-test.wav"
        self.microsoft_filename = "microsoft-test.wav"
        self.polly_filename = "polly-test.wav"
        self.sherpaonnx_filename = "sherpaonnx-test.wav"
        self.watson_filename = "watson-test.wav"
        self.wtai_filename = "wtai-test.wav"
        self.sapi_filename = "sapi-test.wav"


    def tearDown(self) -> None:
        if os.path.exists(self.google_filename):
            os.remove(self.google_filename)
        if os.path.exists(self.elevenlabs_filename):
            os.remove(self.elevenlabs_filename)
        if os.path.exists(self.googletrans_filename):
            os.remove(self.googletrans_filename)
        if os.path.exists(self.microsoft_filename):
            os.remove(self.microsoft_filename)
        if os.path.exists(self.polly_filename):
            os.remove(self.polly_filename)
        if os.path.exists(self.sherpaonnx_filename):
            os.remove(self.sherpaonnx_filename)
        if os.path.exists(self.watson_filename):
            os.remove(self.watson_filename)
        if os.path.exists(self.wtai_filename):
            os.remove(self.wtai_filename)
        if os.path.exists(self.sapi_filename):
            os.remove(self.sapi_filename)

    def test_google_audio_creation(self) -> None:
        googletts = tts_instances["google"]
        ssml_text = googletts.ssml.add("This is me speaking with speak_streamed function and google")
        googletts.speak_streamed(ssml_text,self.google_filename,"wav")
        assert os.path.exists(self.google_filename)
        self.__class__.success_count += 1

    """def test_elevenlabs_audio_creation(self):
        elevenlabstts = tts_instances["elevenlabs"]
        ssml_text = elevenlabstts.ssml.add(f"This is me speaking with speak_streamed function and elevenlabs")
        print(ssml_text)
        elevenlabstts.speak_streamed(ssml_text,self.elevenlabs_filename,"wav")
        self.assertTrue(os.path.exists(self.elevenlabs_filename))
        print(f"Test passed: File '{self.elevenlabs_filename}' was created successfully.")
        self.__class__.success_count += 1
    """
    def test_googletrans_audio_creation(self) -> None:
        ssml_text = "This is me speaking with speak_streamed function and googletrans"
        googletranstts = tts_instances["googletrans"]
        googletranstts.speak_streamed(ssml_text,self.googletrans_filename,"wav")
        assert os.path.exists(self.googletrans_filename)
        self.__class__.success_count += 1

    def test_microsoft_audio_creation(self) -> None:
        microsofttts = tts_instances["microsoft"]
        ssml_text = "This is me speaking with speak_streamed function and microsoft"
        microsofttts.speak_streamed(ssml_text,self.microsoft_filename,"wav")
        assert os.path.exists(self.microsoft_filename)
        self.__class__.success_count += 1

    def test_polly_audio_creation(self) -> None:
        pollytts = tts_instances["polly"]
        ssml_text = "This is me speaking with speak_streamed function and polly"
        pollytts.speak_streamed(ssml_text,self.polly_filename,"wav")
        assert os.path.exists(self.polly_filename)
        self.__class__.success_count += 1

    def test_sherpaonnx_audio_creation(self) -> None:
        ssml_text = "This is me speaking with speak_streamed function and sherpaonnx"
        sherpaonnxtts =  tts_instances["sherpaonnx"]
        sherpaonnxtts.set_voice(voice_id="eng")
        sherpaonnxtts.speak_streamed(ssml_text,self.sherpaonnx_filename,"wav")
        assert os.path.exists(self.sherpaonnx_filename)
        self.__class__.success_count += 1

    def test_watson_audio_creation(self) -> None:
        ssml_text = "This is me speaking with speak_streamed function and watson"
        watsontts =  tts_instances["watson"]
        watsontts.speak_streamed(ssml_text,self.watson_filename,"wav")
        assert os.path.exists(self.watson_filename)
        self.__class__.success_count += 1

    def test_wtai_audio_creation(self) -> None:
        ssml_text = "This is me speaking with speak_streamed function and WTAI"
        wtaitts =  tts_instances["witai"]
        wtaitts.speak_streamed(ssml_text,self.wtai_filename,"wav")
        assert os.path.exists(self.wtai_filename)
        self.__class__.success_count += 1

    def test_sapi_audio_creation(self) -> None:
        ssml_text = "This is me speaking with speak_streamed function and SAPI"
        sapitts =  tts_instances["sapi"]
        sapitts.speak_streamed(ssml_text,self.sapi_filename,"wav")
        assert os.path.exists(self.sapi_filename)
        self.__class__.success_count += 1

if __name__ == "__main__":
    manager = ClientManager()
    tts_instances = manager.create_tts_instances(TTS_CLIENTS)

    unittest.main(verbosity=1)
