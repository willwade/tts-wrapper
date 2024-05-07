from typing import List, Dict, Any
from ...exceptions import ModuleNotInstalled

try:
    from google.cloud import texttospeech
    from google.oauth2 import service_account  # type: ignore

    FORMATS = {
        "wav": texttospeech.AudioEncoding.LINEAR16,
        "mp3": texttospeech.AudioEncoding.MP3,
    }
except ImportError:
    texttospeech = None  # type: ignore
    service_account = None  # type: ignore
    FORMATS = {}


class GoogleClient:
    def __init__(self, credentials: str) -> None:
        if texttospeech is None or service_account is None:
            raise ModuleNotInstalled("google-cloud-texttospeech")

        self._client = texttospeech.TextToSpeechClient(
            credentials=service_account.Credentials.from_service_account_file(
                credentials
            )
        )

    def synth(self, ssml: str, voice: str, lang: str, format: str) -> bytes:
        s_input = texttospeech.SynthesisInput(ssml=ssml)
        voice = texttospeech.VoiceSelectionParams(language_code=lang, name=voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=FORMATS[format])

        resp = self._client.synthesize_speech(
            input=s_input, voice=voice, audio_config=audio_config
        )
        return resp.audio_content


    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Google Cloud Text-to-Speech service."""
        response = self._client.list_voices()
        voices = response.voices  # Assuming this returns a list of voice objects
        standardized_voices = []
        for voice in voices:
            voice_data = voice.__dict__  # or convert to dict if not already one
            voice_data['id'] = voice.name
            voice_data['language_codes'] = voice.language_codes
            voice_data['display_name'] = voice.name
            voice_data['gender'] = voice.ssml_gender
            standardized_voices.append(voice_data)
        return standardized_voices
