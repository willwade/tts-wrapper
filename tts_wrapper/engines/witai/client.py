import requests
from ...tts import AbstractTTS, FileFormat
from typing import Any, Dict, Optional, List
from ...exceptions import UnsupportedFileFormat
import requests
import logging
from ...tts import AbstractTTS, FileFormat
from typing import Any, Dict, Optional, List
from ...exceptions import UnsupportedFileFormat

FORMATS = {
    "mp3": "mp3",
    "pcm": "raw",
    "wav": "wav"
}

class WitAiClient:
    def __init__(self, credentials: tuple) -> None:
        if not credentials or not credentials[0]:
            raise ValueError("An API token for Wit.ai must be provided")
        
        # Assuming credentials is a tuple where the first item is the token
        self.token = credentials[0]
        self.base_url = "https://api.wit.ai"
        self.api_version = "20240601"
        self.logger = logging.getLogger(__name__)
        
    def _get_mime_type(self, format: str) -> str:
        """Maps logical format names to MIME types."""
        formats = {
            "pcm": "audio/raw",  # Default format
            "mp3": "audio/mpeg",
            "wav": "audio/wav"
        }
        return formats.get(format, "audio/raw")  # Default to PCM if unspecified
        
    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Wit.ai."""
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        try:
            response = requests.get(f"{self.base_url}/voices?v={self.api_version}", headers=headers)
            response.raise_for_status()
            voices = response.json()
            standardized_voices = []
            for locale, voice_list in voices.items():
                for voice in voice_list:
                    standardized_voices.append({
                        "id": voice["name"],
                        "language_codes": [locale],
                        "display_name": voice["name"].split("$")[1],
                        "gender": voice["gender"],
                        "styles": voice.get("styles", [])
                    })
            return standardized_voices
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch voices from Wit.ai: {e}")
            raise
        
    def synth(self, text: str, voice: str, format: str = "pcm") -> bytes:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": self._get_mime_type(format)
        }
        
        data = {
            "q": text,
            "voice": voice
        }
        
        try:
            print(headers)  # Debug print statement
            print(data)  # Debug print statement
            response = requests.post(f"{self.base_url}/synthesize?v={self.api_version}", headers=headers, json=data)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(e.response.text)  # Debug print statement
            self.logger.error(f"Failed to synthesize text with Wit.ai: {e}")
            raise
