from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

import requests

from tts_wrapper.engines.playht.ssml import PlayHTSSML
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path


class PlayHTClient(AbstractTTS):
    """Client for Play.HT TTS API."""

    def __init__(self, credentials=None, api_key=None, user_id=None) -> None:
        """
        Initialize the Play.HT client.

        Args:
            credentials: Tuple of (api_key, user_id)
            api_key: API key for Play.HT
            user_id: User ID for Play.HT
        """
        super().__init__()
        if credentials:
            if isinstance(credentials, tuple) and len(credentials) == 2:
                self.api_key, self.user_id = credentials
            else:
                self.api_key = credentials
                self.user_id = user_id
        else:
            self.api_key = api_key
            self.user_id = user_id

        if not self.api_key:
            msg = "API key is required"
            raise ValueError(msg)

        if not self.user_id:
            # Try to get user_id from environment variable
            import os

            self.user_id = os.getenv("PLAYHT_USER_ID")
            if not self.user_id:
                msg = "User ID is required"
                raise ValueError(msg)

        self.base_url = "https://api.play.ht/api/v2"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-USER-ID": self.user_id,
        }
        self.ssml = PlayHTSSML()
        self.audio_rate = 24000  # Default sample rate for PlayHT
        # Separate headers for synthesis which needs audio/mpeg
        self.synth_headers = {**self.headers, "accept": "audio/mpeg"}

    def synth_raw(self, text: str, options: dict[str, Any] | None = None) -> bytes:
        """Synthesize text to speech."""
        url = "https://api.play.ht/api/v2/tts/stream"

        options = options or {}

        # Default voice with full S3 URL
        default_voice = (
            "s3://voice-cloning-zero-shot/d9ff78ba-d016-47f6-b0ef-dd630f59414e/"
            "female-cs/manifest.json"
        )

        # Base payload with required parameters
        payload = {
            "text": text,
            "voice": options.get("voice", default_voice),
            "output_format": "wav",  # Request WAV instead of MP3
            "voice_engine": options.get("voice_engine", "PlayDialog"),
            "sample_rate": 44100,  # Standard audio rate
        }

        # Optional parameters
        if "quality" in options:
            payload["quality"] = options["quality"]
        if "speed" in options:
            payload["speed"] = float(options["speed"])
        if "sample_rate" in options:
            payload["sample_rate"] = int(options["sample_rate"])

        # Advanced parameters for PlayHT2.0 and Play3.0-mini
        for param in ["emotion", "voice_guidance", "style_guidance", "text_guidance"]:
            if param in options:
                payload[param] = options[param]

        # Set headers based on output format
        headers = {**self.headers}
        if payload["output_format"] == "wav":
            headers["accept"] = "audio/wav"
        else:
            headers["accept"] = "audio/mpeg"

        logging.debug("Sending synthesis request to Play.HT:")
        logging.debug(f"URL: {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Payload: {payload}")

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            status = response.status_code
            error = response.json() if response.content else {"error": "Unknown error"}
            logging.error(f"Play.HT synthesis failed with status {status}")
            logging.error(f"Response content: {error}")
            response.raise_for_status()

        return response.content

    def _get_voices(self) -> list[dict[str, Any]]:
        """
        Get available voices from Play.HT.

        Returns:
            List of standardized voice dictionaries with raw language information
        """
        standardized_voices = []

        # Get standard voices
        url = f"{self.base_url}/voices"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        voices_data = response.json()

        for voice in voices_data:
            standardized_voices.append(
                {
                    "id": voice.get("id"),
                    "name": voice.get("name", "Unknown"),
                    "language_codes": [voice.get("language", "en-US")],
                    "gender": voice.get("gender", "unknown").lower(),
                }
            )

        # Get cloned voices
        url = f"{self.base_url}/cloned-voices"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            cloned_voices_data = response.json()

            for voice in cloned_voices_data:
                standardized_voices.append(
                    {
                        "id": voice.get("id"),
                        "name": f"{voice.get('name', 'Unknown')} (Cloned)",
                        "language_codes": [voice.get("language", "en-US")],
                        "gender": voice.get("gender", "unknown").lower(),
                    }
                )
        except requests.RequestException:
            # If cloned voices request fails, continue with standard voices
            pass

        return standardized_voices

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in PlayHT)
        """
        self.voice_id = voice_id

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        options = {}

        # Use provided voice_id or the one set with set_voice
        if voice_id:
            options["voice"] = voice_id
        elif hasattr(self, "voice_id") and self.voice_id:
            options["voice"] = self.voice_id

        # Get audio data
        return self.synth_raw(str(text), options)

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
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

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
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Get audio bytes
        self.synth_to_bytes(text, voice_id)

        # Estimate word timings based on text length
        if callback is not None:
            words = str(text).split()
            total_duration = 2.0  # Estimate 2 seconds for the audio
            time_per_word = total_duration / len(words) if words else 0

            current_time = 0.0
            for word in words:
                end_time = current_time + time_per_word
                callback(word, current_time, end_time)
                current_time = end_time

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()

    def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """Get available voices.

        Args:
            langcodes: Format for language codes (not used in PlayHT)

        Returns:
            List of standardized voice dictionaries
        """
        return self._get_voices()

    def set_property(self, key: str, value: Any) -> None:
        """Set a property for synthesis.

        Args:
            key: Property name
            value: Property value
        """
        if not hasattr(self, "_properties"):
            self._properties = {}
        self._properties[key] = value

    def check_credentials(self) -> bool:
        """Check if the provided credentials are valid."""
        try:
            self._get_voices()
            return True
        except requests.RequestException:
            return False
