"""
This module contains unit tests for TTS audio file creation.
"""

import json
import os
import unittest
from pathlib import Path

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

services = ["polly", "google", "microsoft", "watson", "elevenlabs",
             "witai", "googletrans", "sherpaonnx", "sapi"]

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
        "credential_keys": ["WATSON_API_KEY", "WATSON_REGION", "WATSON_INSTANCE_ID"],
        "class": WatsonTTS,
    },
    "elevenlabs": {
        "client": ElevenLabsClient,
        "credential_keys": ["ELEVENLABS_API_KEY"],
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
    """
    Manage the creation and configuration of TTS clients.
    """
    def __init__(self, credentials_file: str = "credentials-private.json") -> None:
        """
        Initialize the ClientManager with the given credentials file.
        
        :param credentials_file: Path to the JSON file containing credentials.
        """
        self.credentials_file = credentials_file
        self.credentials = self.load_credentials()

    def load_credentials(self) -> dict:
        """
        Load credentials from the JSON file and environment variables.
        
        :return: A dictionary of credentials.
        """
        json_vars = {}
        if Path(self.credentials_file).exists():
            with Path(self.credentials_file).open() as file:
                data = json.load(file)
                for service, creds in data.items():
                    for key, value in creds.items():
                        env_var = f"{service.upper()}_{key.upper()}"
                        json_vars[env_var] = value
        return json_vars

    def get_credential(self, key: str) -> str:
        """
        Retrieve a credential value by key.
        
        :param key: The key of the credential.
        :return: The value of the credential.
        """
        return self.credentials.get(key) or os.getenv(key)

    def create_dynamic_client(self, config: dict) -> object:
        """
        Create a dynamic TTS client based on the provided configuration.
        
        :param config: The configuration dictionary for the TTS client.
        :return: An instance of the TTS client.
        """
        if "client_lambda" in config:
            # For clients with predefined lambda functions
            return config["client_lambda"]()
        if "client" in config:
            client_class = config["client"]
            credential_keys = config.get("credential_keys", [])

            if isinstance(credential_keys, (list, tuple)):
                args = [self.get_credential(key) for key in credential_keys]
                if len(args) == 1:
                    args = str(args[0])
                return client_class(credentials=args)
            msg = "credential_keys must be a tuple"
            raise ValueError(msg)
        msg = "Config must contain either 'client' or 'client_lambda'"
        raise ValueError(msg)

    def create_tts_instances(self, client_configs: dict) -> dict:
        """
        Create TTS instances for all configured clients.
        
        :param client_configs: A dictionary of client configurations.
        :return: A dictionary of TTS instances.
        """
        tts_instances = {}
        for name, config in client_configs.items():
            client = self.create_dynamic_client(config)
            tts_class = config["class"]
            tts_instance = tts_class(client)
            if tts_instance.check_credentials():
                tts_instances[name] = tts_instance
            else:
                pass
        return tts_instances


class TestFileCreation(unittest.TestCase):
    """
    Unit tests for TTS audio file creation.
    """
    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the test class by initializing the ClientManager and TTS instances.
        """
        cls.manager = ClientManager()
        cls.tts_instances = cls.manager.create_tts_instances(TTS_CLIENTS)
        cls.success_count = 0

    def setUp(self) -> None:
        """
        Set up the test case by defining the file names for each TTS engine.
        """
        self.file_names = {
            "google": "google-test.wav",
            "googletrans": "googletrans-test.wav",
            "elevenlabs": "elevenlabs-test.wav",
            "microsoft": "microsoft-test.wav",
            "polly": "polly-test.wav",
            "sherpaonnx": "sherpaonnx-test.wav",
            "watson": "watson-test.wav",
            "witai": "witai-test.wav",
            "sapi": "sapi-test.wav",
        }

    def tearDown(self) -> None:
        """
        Clean up after each test case by removing the created audio files.
        """
        for filename in self.file_names.values():
            if Path(filename).exists():
                Path(filename).unlink()

    def _test_audio_creation(self, engine_name: str, ssml_text: str) -> None:
        """
        Test the audio file creation for a given TTS engine.
        
        :param engine_name: The name of the TTS engine.
        :param ssml_text: The SSML text to be synthesized.
        """
        tts_instance = self.__class__.tts_instances.get(engine_name) 
        if tts_instance:
            tts_instance.speak_streamed(ssml_text, self.file_names[engine_name], "wav")
            self.assertTrue(Path(self.file_names[engine_name]).exists())
            self.__class__.success_count += 1
        else:
            self.skipTest(f"{engine_name} is not available due to missing credentials.")

    def test_google_audio_creation(self) -> None:
        """
        Test audio file creation using Google TTS.
        """
        self._test_audio_creation("google", "This is a test using Google TTS.")

    def test_googletrans_audio_creation(self) -> None:
        """
        Test audio file creation using Google Translate TTS.
        """
        self._test_audio_creation("googletrans", 
                                  "This is a test using Google Translate TTS.")

    def test_microsoft_audio_creation(self) -> None:
        """
        Test audio file creation using Microsoft TTS.
        """
        self._test_audio_creation("microsoft", "This is a test using Microsoft TTS.")

    def test_polly_audio_creation(self) -> None:
        """
        Test audio file creation using Amazon Polly TTS.
        """
        self._test_audio_creation("polly", "This is a test using Amazon Polly TTS.")

    def test_sherpaonnx_audio_creation(self) -> None:
        """
        Test audio file creation using SherpaONNX TTS.
        """
        self._test_audio_creation("sherpaonnx", "This is a test using SherpaONNX TTS.")

    def test_watson_audio_creation(self) -> None:
        """
        Test audio file creation using IBM Watson TTS.
        """
        self._test_audio_creation("watson", "This is a test using IBM Watson TTS.")

    def test_witai_audio_creation(self) -> None:
        """
        Test audio file creation using Wit.ai TTS.
        """
        self._test_audio_creation("witai", "This is a test using Wit.ai TTS.")

    def test_sapi_audio_creation(self) -> None:
        """
        Test audio file creation using SAPI TTS.
        """
        self._test_audio_creation("sapi", "This is a test using SAPI TTS.")

if __name__ == "__main__":
    unittest.main(verbosity=2)