from __future__ import annotations

import json
import logging
import struct
import threading
from pathlib import Path
from typing import Any, Callable

from tts_wrapper.exceptions import ModuleNotInstalled
from tts_wrapper.tts import AbstractTTS

Credentials = tuple[str, str, str]  # api_key, region, instance_id

# FORMATS = {"wav": "audio/wav", "mp3": "audio/mp3"}


class WatsonClient(AbstractTTS):
    def __init__(
        self,
        credentials: Credentials,
        disableSSLVerification: bool = False,
    ) -> None:
        super().__init__()
        self.api_key, self.region, self.instance_id = credentials
        self.disableSSLVerification = disableSSLVerification

        self._client = None
        self.iam_token = None
        self.ws_url = None
        self.word_timings: list[dict[str, Any]] = []
        self.audio_rate = 22050  # Default sample rate for Watson TTS

        self._initialize_ibm_watson()

    def check_credentials(self) -> bool:
        """Check if the Watson credentials are valid.

        Returns:
            True if the credentials are valid, False otherwise
        """
        # Check if credentials are provided
        if not self.api_key or not self.region or not self.instance_id:
            logging.warning("Watson credentials are missing")
            return False

        try:
            # Try to get voices to check if credentials are valid
            voices = self._client.list_voices().get_result()
            if not voices or "voices" not in voices:
                logging.warning("Watson returned empty voices list")
                return False
            return True
        except Exception as e:
            # Check for specific error messages that indicate invalid credentials
            error_str = str(e)
            if (
                "403" in error_str
                or "Forbidden" in error_str
                or "Unauthorized" in error_str
            ):
                logging.warning("Watson credentials are invalid (403 Forbidden): %s", e)
                return False
            if "401" in error_str:
                logging.warning(
                    "Watson credentials are invalid (401 Unauthorized): %s", e
                )
                return False
            # For other errors, log but still return False to skip the test
            logging.warning("Watson error (not credential-related): %s", e)
            return False

    def _initialize_ibm_watson(self) -> None:
        if self._client is None:
            try:
                import requests
                from ibm_cloud_sdk_core.authenticators import (
                    IAMAuthenticator,  # type: ignore[import]
                )
                from ibm_watson import TextToSpeechV1  # type: ignore[import]

                self.IAMAuthenticator = IAMAuthenticator
                self.TextToSpeechV1 = TextToSpeechV1
                self.requests = requests
            except ImportError:
                msg = "ibm-watson"
                raise ModuleNotInstalled(msg)

            authenticator = self.IAMAuthenticator(self.api_key)
            self._client = self.TextToSpeechV1(authenticator=authenticator)
            api_url = f"https://api.{self.region}.text-to-speech.watson.cloud.ibm.com/"
            self._client.set_service_url(api_url)
            if self.disableSSLVerification:
                self._client.set_disable_ssl_verification(True)
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Get IAM token
            response = self.requests.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "apikey": self.api_key,
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self.iam_token = response.json()["access_token"]

            # Construct the WebSocket URL
            self.ws_url = f"wss://api.{self.region}.text-to-speech.watson.cloud.ibm.com/instances/{self.instance_id}/v1/synthesize"

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in Watson)
        """
        self.voice_id = voice_id

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes in WAV format
        """
        self._initialize_ibm_watson()

        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        if not voice:
            # Use a default voice if none is set
            voices = self._get_voices()
            voice = (
                voices[0]["id"] if voices else "en-US_AllisonV3Voice"
            )  # Default voice

        return (
            self._client.synthesize(text=str(text), voice=voice, accept="audio/wav")
            .get_result()
            .content
        )

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        output_path = Path(output_file) if isinstance(output_file, str) else output_file
        with output_path.open("wb") as f:
            f.write(audio_bytes)

    def synth_raw(self, ssml: str, voice: str) -> bytes:
        """Legacy method for backward compatibility."""
        self._initialize_ibm_watson()
        return (
            self._client.synthesize(text=str(ssml), voice=voice, accept="audio/wav")
            .get_result()
            .content
        )

    def synth_with_timings(self, ssml: str, voice: str) -> bytes:
        self._initialize_ibm_watson()
        audio_data = []
        self.word_timings = []

        def on_message(ws, message) -> None:
            if isinstance(message, bytes):
                audio_data.append(message)
            else:
                data = json.loads(message)
                if "words" in data:
                    self.word_timings.extend(
                        [(float(timing[2]), timing[0]) for timing in data["words"]],
                    )

        def on_open(ws) -> None:
            message = {
                "text": ssml,
                "accept": "audio/wav",
                "voice": voice,
                "timings": ["words"],
            }
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logging.exception("Error sending message: %s", e)

        def on_error(ws, error) -> None:
            logging.error("WebSocket error: %s", error)

        def on_close(ws, status_code, reason) -> None:
            logging.info(
                "WebSocket closed with status code: %s, reason: %s", status_code, reason
            )

        import websocket

        ws = websocket.WebSocketApp(
            self.ws_url + f"?access_token={self.iam_token}&voice={voice}",
            on_message=on_message,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close,
        )

        wst = threading.Thread(target=ws.run_forever)
        try:
            wst.daemon = True
            wst.start()
            wst.join()
            return b"".join(audio_data)

        except Exception as e:
            logging.exception("Error in WebSocket thread: %s", e)
            return b""
        finally:
            ws.close()

    def get_audio_duration(self) -> float:
        """Get the duration of the loaded audio in seconds.

        Returns:
            Duration in seconds
        """
        if not hasattr(self, "_audio_bytes") or not self._audio_bytes:
            return 0.0

        return self._get_audio_duration(self._audio_bytes)

    def _get_audio_duration(self, audio_content: bytes) -> float:
        """Parse WAV header to get audio duration.

        Args:
            audio_content: Raw WAV audio bytes

        Returns:
            Duration in seconds
        """
        # Constants for WAV header parsing
        RIFF_MAGIC = b"RIFF"
        WAVE_MAGIC = b"WAVE"
        FMT_MAGIC = b"fmt "
        DATA_MAGIC = b"data"

        # Parse WAV header to get sample rate and number of samples
        riff, size, fformat = struct.unpack("<4sI4s", audio_content[:12])
        if riff != RIFF_MAGIC or fformat != WAVE_MAGIC:
            msg = "Not a WAV file"
            raise ValueError(msg)

        subchunk1, subchunk1_size = struct.unpack("<4sI", audio_content[12:20])
        if subchunk1 != FMT_MAGIC:
            msg = "Not a valid WAV file"
            raise ValueError(msg)

        aformat, channels, sample_rate, byte_rate, block_align, bits_per_sample = (
            struct.unpack("HHIIHH", audio_content[20:36])
        )

        subchunk2, subchunk2_size = struct.unpack("<4sI", audio_content[36:44])
        if subchunk2 != DATA_MAGIC:
            msg = "Not a valid WAV file"
            raise ValueError(msg)

        num_samples = subchunk2_size // (channels * (bits_per_sample // 8))
        return num_samples / sample_rate

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable[[], None]]] = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def _trigger_callbacks(self, event_name: str) -> None:
        """Trigger callbacks for a specific event.

        Args:
            event_name: Name of the event to trigger callbacks for
        """
        if hasattr(self, "_callbacks") and event_name in self._callbacks:
            for cb in self._callbacks[event_name]:
                cb()

    def _get_voice_for_synthesis(self, voice_id: str | None) -> str:
        """Get the voice to use for synthesis.

        Args:
            voice_id: Optional voice ID to use

        Returns:
            Voice ID to use for synthesis
        """
        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        if not voice:
            # Use a default voice if none is set
            voices = self._get_voices()
            voice = (
                voices[0]["id"] if voices else "en-US_AllisonV3Voice"
            )  # Default voice

        return voice

    def _process_word_timings(self, callback: Callable | None, text: str) -> None:
        """Process word timings and call the callback for each word.

        Args:
            callback: Function to call for each word timing
            text: The text that was synthesized
        """
        if callback is None:
            return

        if self.word_timings:
            # Use actual word timings if available
            for timing in self.word_timings:
                if isinstance(timing, tuple) and len(timing) == 2:
                    start_time, word = timing
                    # Estimate end time as start time + 0.3 seconds
                    callback(word, start_time, start_time + 0.3)
        else:
            # Estimate word timings based on text length
            words = str(text).split()
            if not words:
                return

            total_duration = self._get_audio_duration(self._audio_bytes)
            time_per_word = total_duration / len(words)

            current_time = 0.0
            for word in words:
                end_time = current_time + time_per_word
                callback(word, current_time, end_time)
                current_time = end_time

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Trigger onStart callbacks
        self._trigger_callbacks("onStart")

        # Get the voice to use
        voice = self._get_voice_for_synthesis(voice_id)

        # Synthesize with word timings
        try:
            self._audio_bytes = self.synth_with_timings(str(text), voice)
            self._process_word_timings(callback, text)
        except Exception:
            # Fallback to regular synthesis without timings
            self._audio_bytes = self.synth_to_bytes(text, voice)
            self._process_word_timings(callback, text)

        # Trigger onEnd callbacks
        self._trigger_callbacks("onEnd")

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Watson.

        Returns:
            List of voice dictionaries with raw language information
        """
        self._initialize_ibm_watson()
        voice_data = self._client.list_voices().get_result()
        voices = voice_data["voices"]
        standardized_voices = []

        for voice in voices:
            standardized_voice = {
                "id": voice["name"],
                "language_codes": [voice["language"]],
                "name": voice["name"].split("_")[1].replace("V3Voice", ""),
                "gender": voice["gender"],
            }
            standardized_voices.append(standardized_voice)

        return standardized_voices
