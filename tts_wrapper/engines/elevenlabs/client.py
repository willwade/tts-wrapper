import requests
from ...exceptions import ModuleNotInstalled

FORMATS = {
    "wav": "audio/wav",  # Assuming ElevenLabs uses standard MIME types.
    "mp3": "audio/mp3",
}


class ElevenLabsClient:
    def __init__(self, credentials):
        if not credentials:
            raise ValueError("An API key for ElevenLabs must be provided")
        self.api_key = credentials
        self.base_url = "https://api.elevenlabs.io"

    def synth(self, text, voice_id, format):
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',  # assuming a default model; may need customization
            'voice_settings': {
                'stability': 0.5,  # Example settings, adjust as needed
                'similarity_boost': 0.5
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if format == "mp3":  # Assuming direct response is in desired format
            return response.content
        else:
            raise UnsupportedFileFormat(f"Format {format} is not supported by ElevenLabs API")

    def get_voices(self):
        url = f"{self.base_url}/v1/voices"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(url, headers=headers)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()
