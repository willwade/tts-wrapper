from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path

FORMATS = {"mp3": "mp3", "pcm": "raw", "wav": "wav"}


class WitAiClient(AbstractTTS):
    def __init__(self, credentials: tuple) -> None:
        super().__init__()
        if not credentials or not credentials[0]:
            msg = "An API token for Wit.ai must be provided"
            raise ValueError(msg)

        # Extract the token from credentials
        self.token = credentials[0]
        self.base_url = "https://api.wit.ai"
        self.api_version = "20240601"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.audio_rate = 22050  # Default sample rate for WitAI
        # Will be set with set_voice - type is defined in AbstractTTS
        self.voice_id = None

    def _get_mime_type(self, format: str) -> str:
        """Maps logical format names to MIME types."""
        formats = {
            "pcm": "audio/raw",  # Default format
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
        }
        return formats.get(format, "audio/raw")  # Default to PCM if unspecified

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in WitAI)
        """
        self.voice_id = voice_id

    def check_credentials(self) -> bool:
        """Check if the WitAI credentials are valid.

        Returns:
            True if the credentials are valid, False otherwise
        """
        try:
            # Try to get voices to check if credentials are valid
            voices = self._get_voices()
            return len(voices) > 0
        except Exception as e:
            self.logger.warning(f"WitAI credentials are invalid: {e}")
            return False

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Wit.ai.

        Returns:
            List of voice dictionaries with raw language information
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(
                f"{self.base_url}/voices?v={self.api_version}",
                headers=headers,
            )
            response.raise_for_status()
            voices = response.json()
            standardized_voices = []

            for locale_key, voice_list in voices.items():
                # Get the original locale (e.g., "en_US")
                locale = locale_key.replace("_", "-")

                for voice in voice_list:
                    standardized_voices.append(
                        {
                            "id": voice["name"],
                            "language_codes": [locale],
                            "name": voice["name"].split("$")[1],
                            "gender": voice["gender"],
                            "styles": voice.get("styles", []),
                        }
                    )

            return standardized_voices
        except requests.exceptions.RequestException as e:
            self.logger.exception("Failed to fetch voices from Wit.ai: %s", e)
            raise

    def get_voices(self, lang_format: str | None = None) -> list[dict[str, Any]]:
        """Get available voices.

        Args:
            lang_format: Optional language format (not used in WitAI)

        Returns:
            A list of voice dictionaries with id, name, and language fields
        """
        # The _get_voices method already returns standardized voices
        return self._get_voices()

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        self.headers["Content-Type"] = "application/json"
        self.headers["Accept"] = "audio/raw"

        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        if not voice:
            # Use a default voice if none is set
            voices = self._get_voices()
            if voices:
                voice = voices[0]["id"]
            else:
                msg = "No voice ID provided and no default voice available"
                raise ValueError(msg)

        data = {"q": str(text), "voice": voice}

        try:
            response = requests.post(
                f"{self.base_url}/synthesize?v={self.api_version}",
                headers=self.headers,
                json=data,
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.exception("Failed to synthesize text with Wit.ai: %s", e)
            raise

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
