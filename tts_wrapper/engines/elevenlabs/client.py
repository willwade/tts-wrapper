from typing import List, Dict, Any, Optional
from ...tts import FileFormat
import requests
from ...exceptions import ModuleNotInstalled
from ...exceptions import UnsupportedFileFormat


FORMATS = {
    "wav": "pcm_22050",
    "mp3": "mp3_22050_32",
}

class ElevenLabsClient:
    def __init__(self, credentials):
        if not credentials:
            raise ValueError("An API key for ElevenLabs must be provided")
        self.api_key = credentials
        self.base_url = "https://api.elevenlabs.io"

    def synth(self, text: str, voice_id: str, format: FileFormat) -> bytes:
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        headers = {
            'Content-Type': 'application/json',
            "xi-api-key": self.api_key,
            "Accept": "audio/wav"
        }
        params = {"output_format": FORMATS[format]}  # Ensuring the format is passed as a query parameter
        data = {
            'text': text,
            'model_id': 'eleven_monolingual_v1',  # assuming a default model; may need customization
            'voice_settings': {
                'stability': 0.5,  # Example settings, adjust as needed
                'similarity_boost': 0.5
            }
        }
        response = requests.post(url, headers=headers, json=data, params=params)
        if response.status_code == 200:
            return response.content
        else:
            error_message = f"[Elevenlabs.Client.Synth] Failed to synthesize speech: {response.status_code} - {response.reason}"
            try:
                json_response = response.json()
                if 'detail' in json_response:
                    status = json_response['detail'].get('status', 'No status available')
                    message = json_response['detail'].get('message', 'No message provided')
                    error_message += f" Status: {status}. Message: {message}"
                else:
                    error_details = json_response.get('error', {}).get('message', 'No error details available.')
                    error_message += f" Details: {error_details}"
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                error_message += " Error details not in JSON format."
            raise Exception(error_message)


    def get_voices(self):
        url = f"{self.base_url}/v1/voices"
        response = requests.get(url)
        if response.ok:
            voices_data = response.json()
            voices = voices_data['voices']
            standardized_voices = []
            accent_to_language_code = {
                'american': 'en-US',
                'british': 'en-GB',
                'british-essex': 'en-GB',
                'american-southern': 'en-US',
                'australian': 'en-AU',
                'irish': 'en-IE',
                'english-italian': 'en-IT',
                'english-swedish': 'en-SE',
                'american-irish': 'en-IE-US',
                'chinese': 'zh-CN',
                'korean': 'ko-KR',
                'dutch': 'nl-NL',
                'turkish': 'tr-TR',
                'swedish': 'sv-SE',
                'indonesian': 'id-ID',
                'filipino': 'fil-PH',
                'japanese': 'ja-JP',
                'ukrainian': 'uk-UA',
                'greek': 'el-GR',
                'czech': 'cs-CZ',
                'finnish': 'fi-FI',
                'romanian': 'ro-RO',
                'danish': 'da-DK',
                'bulgarian': 'bg-BG',
                'malay': 'ms-MY',
                'slovak': 'sk-SK',
                'croatian': 'hr-HR',
                'classic-arabic': 'ar-SA',
                'tamil': 'ta-IN'
            }
            supported_languages_v1 = {
                'en-US': 'English',
                'pl-PL': 'Polish',
                'de-DE': 'German',
                'es-ES': 'Spanish',
                'fr-FR': 'French',
                'it-IT': 'Italian',
                'hi-IN': 'Hindi',
                'pt-BR': 'Portuguese'
            }
            supported_languages_v2 = {
                'en-US': 'English',
                'pl-PL': 'Polish',
                'de-DE': 'German',
                'es-ES': 'Spanish',
                'fr-FR': 'French',
                'it-IT': 'Italian',
                'hi-IN': 'Hindi',
                'pt-BR': 'Portuguese',
                'zh-CN': 'Chinese',
                'ko-KR': 'Korean',
                'nl-NL': 'Dutch',
                'tr-TR': 'Turkish',
                'sv-SE': 'Swedish',
                'id-ID': 'Indonesian',
                'fil-PH': 'Filipino',
                'ja-JP': 'Japanese',
                'uk-UA': 'Ukrainian',
                'el-GR': 'Greek',
                'cs-CZ': 'Czech',
                'fi-FI': 'Finnish',
                'ro-RO': 'Romanian',
                'da-DK': 'Danish',
                'bg-BG': 'Bulgarian',
                'ms-MY': 'Malay',
                'sk-SK': 'Slovak',
                'hr-HR': 'Croatian',
                'ar-SA': 'Classic Arabic',
                'ta-IN': 'Tamil'
            }
            for voice in voices:
                voice['id'] = voice['voice_id']
                accent = voice['labels'].get('accent', 'american')
                language_code = accent_to_language_code.get(accent, 'en-US')  # Default to 'en-US'
                if voice['high_quality_base_model_ids'] == 'eleven_multilingual_v1':
                    voice['language_codes'] = [language_code for language_code in supported_languages_v1.keys()]
                else:
                    voice['language_codes'] = [language_code for language_code in supported_languages_v2.keys()]
                voice['name'] = voice['name']
                voice['gender'] = 'Unknown'
                standardized_voices.append(voice)
            return standardized_voices
        else:
            response.raise_for_status()
