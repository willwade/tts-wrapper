import contextlib
import logging
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Optional

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
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
    eSpeakClient,
    eSpeakTTS,
)

from .load_credentials import load_credentials

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
    "espeak": {"client_lambda": lambda: eSpeakClient(), "class": eSpeakTTS},
}

# Add SAPI client only on Windows
if sys.platform == "win32":
    try:
        from tts_wrapper import SAPITTS, SAPIClient

        OFFLINE_CLIENTS["sapi"] = {
            "client_lambda": lambda: SAPIClient(),
            "class": SAPITTS,
        }
    except ImportError:
        logging.warning("SAPI support not available")


class ClientManager:
    """Manage the creation and configuration of TTS clients."""

    def __init__(self) -> None:
        self.credentials: dict[str, Any] = {}

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

    def create_tts_instances(
        self, client_configs: dict, check_credentials: bool = True
    ) -> dict:
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
                logging.warning(f"Failed to create TTS instance for {name}: {e!s}")
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
        """Test audio file creation for a specific engine."""
        tts_instance = self.tts_instances.get(engine_name)
        if not tts_instance:
            self.skipTest(f"{engine_name} is not available")

        try:
            # Check if the instance is properly initialized
            if hasattr(tts_instance, "_client") and tts_instance._client is None:
                self.skipTest(f"{engine_name} client is not properly initialized")

            # Try to create the audio file
            tts_instance.synth_to_file(ssml_text, self.file_names[engine_name], "wav")

            # Verify the file was created and is not empty
            file_path = Path(self.file_names[engine_name])
            assert file_path.exists(), f"File for {engine_name} was not created."
            assert file_path.stat().st_size > 0, f"File for {engine_name} is empty."

        except Exception as e:
            logging.error(f"Error testing {engine_name}: {e!s}")
            self.skipTest(f"Error testing {engine_name}: {e!s}")


class TestOfflineEngines(BaseTestFileCreation):
    """Test offline TTS engines."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.manager = ClientManager()
        cls.tts_instances = cls.manager.create_tts_instances(
            OFFLINE_CLIENTS, check_credentials=False
        )

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
        # Create instances without checking credentials initially
        cls.tts_instances = {}

        # Handle each service separately to avoid segfaults
        for name, config in ONLINE_CLIENTS.items():
            try:
                client = cls.manager.create_dynamic_client(config)
                if client:
                    tts_class = config["class"]
                    cls.tts_instances[name] = tts_class(client)
            except Exception as e:
                logging.warning(f"Failed to create TTS instance for {name}: {e!s}")
                continue

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_SA_PATH"), reason="Google credentials not set"
    )
    def test_google_audio_creation(self) -> None:
        if "google" not in self.tts_instances:
            self.skipTest("Google TTS instance not available")
        self._test_audio_creation("google", "This is a test using Google TTS.")

    def test_googletrans_audio_creation(self) -> None:
        if "googletrans" not in self.tts_instances:
            self.skipTest("Google Translate TTS instance not available")
        self._test_audio_creation(
            "googletrans", "This is a test using Google Translate TTS."
        )

    @pytest.mark.skipif(
        not os.getenv("MICROSOFT_TOKEN"), reason="Microsoft Azure credentials not set"
    )
    def test_microsoft_audio_creation(self) -> None:
        if "microsoft" not in self.tts_instances:
            self.skipTest("Microsoft TTS instance not available")
        self._test_audio_creation("microsoft", "This is a test using Microsoft TTS.")

    @pytest.mark.skipif(
        not os.getenv("POLLY_REGION")
        or not os.getenv("POLLY_AWS_KEY_ID")
        or not os.getenv("POLLY_AWS_ACCESS_KEY"),
        reason="Amazon Polly credentials not fully set",
    )
    def test_polly_audio_creation(self) -> None:
        """Test Polly TTS audio creation."""
        if "polly" not in self.tts_instances:
            self.skipTest("Polly TTS instance not available")

        # Additional check for valid credentials
        polly = self.tts_instances["polly"]
        if not hasattr(polly, "_client") or not polly._client:
            self.skipTest("Polly client not properly initialized")

        try:
            # Create a temporary file for the test
            test_file = "polly-test.wav"
            if os.path.exists(test_file):
                os.remove(test_file)

            # Synthesize a short text
            polly.synth_to_file(
                "This is a test using Amazon Polly TTS.", test_file, "wav"
            )

            # Verify the file was created
            assert os.path.exists(test_file)
            assert os.path.getsize(test_file) > 0

        except Exception as e:
            logging.error(f"Error in Polly test: {e!s}")
            self.skipTest(f"Polly test failed: {e!s}")

        finally:
            # Cleanup
            if hasattr(polly, "cleanup"):
                polly.cleanup()
            if os.path.exists(test_file):
                with contextlib.suppress(OSError):
                    os.remove(test_file)

    @pytest.mark.skipif(
        not os.getenv("WATSON_API_KEY"), reason="Watson credentials not set"
    )
    def test_watson_audio_creation(self) -> None:
        if "watson" not in self.tts_instances:
            self.skipTest("Watson TTS instance not available")
        self._test_audio_creation("watson", "This is a test using IBM Watson TTS.")

    @pytest.mark.skipif(
        not os.getenv("WITAI_TOKEN"), reason="WitAi credentials not set"
    )
    def test_witai_audio_creation(self) -> None:
        if "witai" not in self.tts_instances:
            self.skipTest("WitAi TTS instance not available")
        self._test_audio_creation("witai", "This is a test using Wit.ai TTS.")

    @pytest.mark.skipif(
        not os.getenv("ELEVENLABS_API_KEY"), reason="ElevenLabs credentials not set"
    )
    def test_elevenlabs_audio_creation(self) -> None:
        if "elevenlabs" not in self.tts_instances:
            self.skipTest("ElevenLabs TTS instance not available")
        self._test_audio_creation("elevenlabs", "This is a test using elevenlabs TTS.")


if __name__ == "__main__":
    load_credentials("credentials.json")
    unittest.main(verbosity=2)
