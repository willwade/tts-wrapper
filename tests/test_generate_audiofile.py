import os
import sys
import unittest
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .load_credentials import load_credentials

import pytest

from tts_wrapper import (
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
    SherpaOnnxClient,
    SherpaOnnxTTS,
    SystemTTS,
    SystemTTSClient,
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
    eSpeakClient,
    eSpeakTTS,
)

# Split clients into online and offline
ONLINE_CLIENTS = {
    "polly": {
        "client": PollyClient,
        "class": PollyTTS,
        "credential_keys": ["POLLY_REGION", "POLLY_AWS_KEY_ID", "POLLY_AWS_ACCESS_KEY"],
    },
    "google": {
        "client": GoogleClient,
        "class": GoogleTTS,
        "credential_keys": ["GOOGLE_SA_PATH"],
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
}

OFFLINE_CLIENTS = {
    "sherpaonnx": {
        "client_lambda": lambda: SherpaOnnxClient(
            model_path=None, tokens_path=None, model_id="mms_eng"
        ),
        "class": SherpaOnnxTTS,
    },
    "systemtts": {
        "client_lambda": lambda: SystemTTSClient(),
        "class": SystemTTS,
    },
    "espeak": {"client_lambda": lambda: eSpeakClient(), "class": eSpeakTTS},
}

# Add SAPI client only on Windows
if sys.platform == "win32":
    try:
        from tts_wrapper import SAPIClient, SAPITTS
        OFFLINE_CLIENTS["sapi"] = {
            "client_lambda": lambda: SAPIClient(),
            "class": SAPITTS,
        }
    except ImportError:
        logging.warning("SAPI support not available")

class ClientManager:
    """Manage the creation and configuration of TTS clients."""

    def __init__(self) -> None:
        self.credentials: Dict[str, Any] = {}

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential value by key from environment variables."""
        return os.getenv(key)

    def create_dynamic_client(self, config: dict) -> Optional[object]:
        """Create a dynamic TTS client based on the provided configuration."""
        if "client_lambda" in config:
            return config["client_lambda"]()
        if "client" in config and config["client"] is None:
            return None
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

    def create_tts_instances(self, client_configs: dict, check_credentials: bool = True) -> dict:
        """Create TTS instances for all configured clients."""
        tts_instances = {}
        for name, config in client_configs.items():
            try:
                client = self.create_dynamic_client(config)
                tts_class = config["class"]
                tts_instance = tts_class(client)

                if not check_credentials or tts_instance.check_credentials():
                    tts_instances[name] = tts_instance
            except Exception as e:
                logging.warning(f"Failed to create TTS instance for {name}: {str(e)}")
                continue

        return tts_instances


class BaseTestFileCreation(unittest.TestCase):
    """Base class for TTS audio file creation tests."""

    def setUp(self) -> None:
        """Define file names for each TTS engine."""
        self.file_names = {
            engine: f"{engine}-test.wav"
            for engine in list(ONLINE_CLIENTS.keys()) + list(OFFLINE_CLIENTS.keys())
        }

    def tearDown(self) -> None:
        """Remove created audio files after each test."""
        for filename in self.file_names.values():
            if Path(filename).exists():
                Path(filename).unlink()

    def _test_audio_creation(self, engine_name: str, ssml_text: str) -> None:
        tts_instance = self.tts_instances.get(engine_name)
        if tts_instance:
            tts_instance.synth_to_file(ssml_text, self.file_names[engine_name], "wav")
            assert Path(self.file_names[engine_name]).exists(), f"File for {engine_name} was not created."
            assert Path(self.file_names[engine_name]).stat().st_size > 0, f"File for {engine_name} is empty."
        else:
            self.skipTest(f"{engine_name} is not available")


class TestOfflineEngines(BaseTestFileCreation):
    """Test offline TTS engines."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = ClientManager()
        cls.tts_instances = cls.manager.create_tts_instances(OFFLINE_CLIENTS, check_credentials=False)

    def test_espeak_audio_creation(self) -> None:
        self._test_audio_creation(
            "espeak",
            "This is a test using espeak TTS.",
        )

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SAPI only available on Windows",
    )
    def test_sapi_audio_creation(self) -> None:
        self._test_audio_creation(
            "sapi",
            "This is a test using SAPI.",
        )

    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="systemtts has issues with pyttsx3 on macOS",
    )
    def test_systemtts_audio_creation(self) -> None:
        self._test_audio_creation(
            "systemtts",
            "This is a test using System TTS.",
        )

    def test_sherpaonnx_audio_creation(self) -> None:
        self._test_audio_creation(
            "sherpaonnx",
            "This is a test using SherpaONNX TTS.",
        )


class TestOnlineEngines(BaseTestFileCreation):
    """Test online TTS engines."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = ClientManager()
        cls.tts_instances = cls.manager.create_tts_instances(ONLINE_CLIENTS, check_credentials=True)

    @pytest.mark.skipif(not os.getenv("GOOGLE_SA_PATH"), reason="Google credentials not set")
    def test_google_audio_creation(self) -> None:
        self._test_audio_creation("google", "This is a test using Google TTS.")

    def test_googletrans_audio_creation(self) -> None:
        self._test_audio_creation("googletrans", "This is a test using Google Translate TTS.")

    @pytest.mark.skipif(not os.getenv("MICROSOFT_TOKEN"), reason="Microsoft Azure credentials not set")
    def test_microsoft_audio_creation(self) -> None:
        self._test_audio_creation("microsoft", "This is a test using Microsoft TTS.")

    @pytest.mark.skipif(not os.getenv("POLLY_REGION"), reason="Amazon Polly credentials not set")
    def test_polly_audio_creation(self) -> None:
        self._test_audio_creation("polly", "This is a test using Amazon Polly TTS.")

    @pytest.mark.skipif(not os.getenv("WATSON_API_KEY"), reason="Watson credentials not set")
    def test_watson_audio_creation(self) -> None:
        self._test_audio_creation("watson", "This is a test using IBM Watson TTS.")

    @pytest.mark.skipif(not os.getenv("WITAI_TOKEN"), reason="WitAi credentials not set")
    def test_witai_audio_creation(self) -> None:
        self._test_audio_creation("witai", "This is a test using Wit.ai TTS.")

    @pytest.mark.skipif(not os.getenv("ELEVENLABS_API_KEY"), reason="ElevenLabs credentials not set")
    def test_elevenlabs_audio_creation(self) -> None:
        self._test_audio_creation("elevenlabs", "This is a test using elevenlabs TTS.")


if __name__ == "__main__":
    load_credentials("credentials.json")
    unittest.main(verbosity=2)
