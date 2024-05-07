from typing import List, Dict, Any, Optional
from ...tts import FileFormat
import requests
from ...exceptions import ModuleNotInstalled
from ...exceptions import UnsupportedFileFormat


FORMATS = {
    "mp3": "audio/mp3",
}


class ElevenLabsClient:
    def __init__(self, credentials):
        if not credentials:
            raise ValueError("An API key for ElevenLabs must be provided")
        self.api_key = credentials
        self.base_url = "https://api.elevenlabs.io"

    def synth(self, text: str, voice_id: str, format: FileFormat) -> bytes:
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        print(url)
        headers = {
            'Content-Type': 'application/json',
            "xi-api-key": self.api_key,
            "Accept": "audio/mpeg"
        }
        print(headers)
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',  # assuming a default model; may need customization
            'voice_settings': {
                'stability': 0.5,  # Example settings, adjust as needed
                'similarity_boost': 0.5
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            if format == "mp3":
                return response.content
            else:
                raise UnsupportedFileFormat(format, "ElevenLabs API")
        else:
            error_message = f"Failed to synthesize speech: {response.status_code} - {response.reason}"
            if response.content:
                error_details = response.json().get('error', {}).get('message', 'No error details available.')
                error_message += f" Details: {error_details}"
            raise Exception(error_message)


    def get_voices(self):
        url = f"{self.base_url}/v1/voices"
        response = requests.get(url)
        if response.ok:
            voices_data =  response.json()
            voices = voices_data['voices']
            standardized_voices = []
            for voice in voices:
                voice['id'] = voice['voice_id']
                voice['language_codes'] = [voice['fine_tuning']['language']]
                voice['display_name'] = voice['name']
                voice['gender'] = 'Unknown'
                standardized_voices.append(voice)
            return standardized_voices
        else:
            response.raise_for_status()
