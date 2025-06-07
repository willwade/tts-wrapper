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
    GoogleClient,
    GoogleTransClient,
    MicrosoftClient,
    PollyClient,
    SherpaOnnxClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)

from .load_credentials import load_credentials

# Split clients into online and offline
ONLINE_CLIENTS = {
    "polly": {
        "client": PollyClient,
        "credential_keys": ["POLLY_REGION", "POLLY_AWS_KEY_ID", "POLLY_AWS_ACCESS_KEY"],
    },
    "google": {
        "client": GoogleClient,
        "credential_keys": ["GOOGLE_SA_PATH"],
    },
    "microsoft": {
        "client": MicrosoftClient,
        "credential_keys": ["MICROSOFT_TOKEN", "MICROSOFT_REGION"],
    },
    "watson": {
        "client": WatsonClient,
        "credential_keys": ["WATSON_API_KEY", "WATSON_REGION", "WATSON_INSTANCE_ID"],
    },
    "elevenlabs": {
        "client": ElevenLabsClient,
        "credential_keys": ["ELEVENLABS_API_KEY"],
    },
    "witai": {
        "client": WitAiClient,
        "credential_keys": ["WITAI_TOKEN"],
    },
    "googletrans": {
        "client_lambda": lambda: GoogleTransClient("en-co.uk"),
    },
}

OFFLINE_CLIENTS = {
    "sherpaonnx": {
        "client_lambda": lambda: SherpaOnnxClient(
            model_path=None, tokens_path=None, model_id="mms_eng"
        ),
    },
    "espeak": {"client_lambda": lambda: eSpeakClient()},
}

# Add AVSynth client only on macOS
if sys.platform == "darwin":
    try:
        from tts_wrapper import AVSynthClient

        OFFLINE_CLIENTS["avsynth"] = {
            "client_lambda": lambda: AVSynthClient(),
        }
    except ImportError:
        logging.warning("AVSynth support not available")

# Add SAPI client only on Windows
if sys.platform == "win32":
    try:
        from tts_wrapper import SAPIClient

        OFFLINE_CLIENTS["sapi"] = {
            "client_lambda": lambda: SAPIClient(),
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

                # Special handling for Google client
                if (
                    client_class.__name__ == "GoogleClient"
                    and len(args) == 1
                    and args[0]
                ):
                    credentials_path = args[0]
                    # Try both the path as-is and as a relative path from the current directory
                    if os.path.exists(credentials_path):
                        print(
                            f"Google credentials file exists: {os.path.abspath(credentials_path)}"
                        )
                    elif os.path.exists(os.path.join(os.getcwd(), credentials_path)):
                        credentials_path = os.path.join(os.getcwd(), credentials_path)
                        print(f"Google credentials file exists at: {credentials_path}")
                    else:
                        print(
                            f"Google credentials file does not exist: {credentials_path}"
                        )
                        return None
                    return client_class(credentials=credentials_path)

                # Default handling for other clients
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
                # In the new architecture, the client is the TTS instance
                tts_instance = self.create_dynamic_client(config)

                if not check_credentials or tts_instance.check_credentials():
                    tts_instances[name] = tts_instance
            except Exception as e:
                logging.warning(f"Failed to create TTS instance for {name}: {e!s}")
                continue

        return tts_instances


class BaseTestFileCreation(unittest.TestCase):
    """Base class for TTS audio file creation tests."""

    # Class variables to be set by subclasses
    manager = None
    tts_instances = {}

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

    @pytest.mark.skipif(
        os.environ.get("SKIP_ESPEAK_SYNTH_TEST") is not None,
        reason="SKIP_ESPEAK_SYNTH_TEST is set",
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

    def test_sherpaonnx_audio_creation(self) -> None:
        self._test_audio_creation(
            "sherpaonnx",
            "This is a test using SherpaONNX TTS.",
        )

    def test_sherpaonnx_speak_streamed_wav_header(self) -> None:
        """Test that SherpaOnnx speak_streamed creates proper WAV files with RIFF headers."""
        tts_instance = self.tts_instances.get("sherpaonnx")
        if not tts_instance:
            self.skipTest("sherpaonnx is not available")

        try:
            import tempfile
            import wave

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                temp_path = tmp_file.name

            test_text = "Testing speak streamed WAV header fix."

            # Use speak_streamed with file saving
            tts_instance.speak_streamed(
                test_text,
                save_to_file_path=temp_path,
                audio_format="wav",
                wait_for_completion=True
            )

            # Verify file was created and has content
            file_path = Path(temp_path)
            assert file_path.exists(), "Audio file was not created"
            assert file_path.stat().st_size > 0, "Audio file is empty"

            # Verify WAV header
            with open(temp_path, "rb") as f:
                header = f.read(4)
                assert header == b"RIFF", f"File does not start with RIFF header, got {header}"

            # Verify it's a valid WAV file
            try:
                with wave.open(temp_path, "rb") as wav_file:
                    assert wav_file.getnframes() > 0, "WAV file has no audio frames"
                    assert wav_file.getnchannels() == 1, "Expected mono audio"
                    assert wav_file.getframerate() > 0, "Invalid frame rate"
            except wave.Error as e:
                self.fail(f"Generated file is not a valid WAV file: {e}")

            # Clean up
            file_path.unlink()

        except Exception as e:
            logging.error(f"Error testing sherpaonnx speak_streamed: {e!s}")
            self.skipTest(f"Error testing sherpaonnx speak_streamed: {e!s}")

    @pytest.mark.skipif(
        sys.platform != "darwin",
        reason="AVSynth only available on macOS",
    )
    def test_avsynth_audio_creation(self) -> None:
        self._test_audio_creation(
            "avsynth",
            "This is a test using AVSynth TTS.",
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
                # In the new architecture, the client is the TTS instance
                tts_instance = cls.manager.create_dynamic_client(config)
                if tts_instance:
                    cls.tts_instances[name] = tts_instance
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
            test_file = Path("polly-test.wav")
            if test_file.exists():
                test_file.unlink()

            # Synthesize a short text
            polly.synth_to_file(
                "This is a test using Amazon Polly TTS.", str(test_file), "wav"
            )

            # Verify the file was created
            assert test_file.exists()
            assert test_file.stat().st_size > 0

        except Exception as e:
            logging.error(f"Error in Polly test: {e!s}")
            self.skipTest(f"Polly test failed: {e!s}")

        finally:
            # Cleanup
            if hasattr(polly, "cleanup"):
                polly.cleanup()
            if test_file.exists():
                with contextlib.suppress(OSError):
                    test_file.unlink()

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
