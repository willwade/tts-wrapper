import requests
from typing import Any, Dict, Optional, List

class WitAiClient:
    def __init__(self, token: str) -> None:
        self.base_url = "https://api.wit.ai"
        self.token = token
        self.api_version = "20240304"

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
        
        response = requests.post(f"{self.base_url}/synthesize?v={self.api_version}", headers=headers, json=data)
        response.raise_for_status()
        return response.content

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