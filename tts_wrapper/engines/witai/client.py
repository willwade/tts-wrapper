import logging
from typing import Any

import requests

FORMATS = {"mp3": "mp3", "pcm": "raw", "wav": "wav"}


class WitAiClient:
    def __init__(self, credentials: tuple) -> None:
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

    def _get_mime_type(self, format: str) -> str:
        """Maps logical format names to MIME types."""
        formats = {
            "pcm": "audio/raw",  # Default format
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
        }
        return formats.get(format, "audio/raw")  # Default to PCM if unspecified

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Wit.ai."""
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
                locale = locale_key.replace("_", "-")
                voice_entries = [
                    {
                        "id": voice["name"],
                        "language_codes": [locale],
                        "name": voice["name"].split("$")[1],
                        "gender": voice["gender"],
                        "styles": voice.get("styles", []),
                    }
                    for voice in voice_list
                ]
                standardized_voices.extend(voice_entries)
            return standardized_voices
        except requests.exceptions.RequestException as e:
            self.logger.exception("Failed to fetch voices from Wit.ai: %s", e)
            raise

    def synth(self, text: str, voice: str, format: str = "pcm") -> bytes:
        self.headers["Content-Type"] = "application/json"
        self.headers["Accept"] = "audio/raw"

        data = {"q": text, "voice": voice}

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
