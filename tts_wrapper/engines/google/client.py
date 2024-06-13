from typing import List, Dict, Any
from ...exceptions import ModuleNotInstalled

try:
    from google.cloud import texttospeech_v1beta1 as texttospeech
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

        if not credentials:
            raise ValueError("credentials file is required")
        
        self._credentials_file = credentials

        self._client = texttospeech.TextToSpeechClient(
            credentials=service_account.Credentials.from_service_account_file(
                credentials
            )
        )

    def synth(self, ssml: str, voice: str, lang: str, format: str, include_timepoints: bool = False) -> Dict[str, Any]:
        s_input = texttospeech.SynthesisInput(ssml=ssml)
        voice_params = texttospeech.VoiceSelectionParams(language_code=lang, name=voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=FORMATS[format])

        if include_timepoints:
            timepoints = [texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
        else:
            timepoints = []

        resp = self._client.synthesize_speech(
            request=texttospeech.SynthesizeSpeechRequest(
                input=s_input,
                voice=voice_params,
                audio_config=audio_config,
                enable_time_pointing=timepoints,
            )
        )

        result = {
            "audio_content": resp.audio_content,
        }
        
        if include_timepoints:
            result["timepoints"] = [{"markName": tp.mark_name, "timeSeconds": tp.time_seconds} for tp in resp.timepoints]

        return result
        
    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Google Cloud Text-to-Speech service."""
        response = self._client.list_voices()
        voices = response.voices  # Assuming this returns a list of voice objects
        standardized_voices = []
        for voice in voices:
            voice_data = voice.__dict__  # or convert to dict if not already one
            voice_data['id'] = voice.name
            voice_data['language_codes'] = voice.language_codes
            voice_data['name'] = voice.name
            voice_data['gender'] = voice.ssml_gender
            if voice.ssml_gender == 1:
                voice_data['gender'] = "Male"
            elif voice.ssml_gender == 2:
                voice_data['gender'] = "Female"
            elif voice.ssml_gender == 3:
                voice_data['gender'] = "Neutral"
            else:
                voice_data['gender'] = "Unknown"
            standardized_voices.append(voice_data)
        return standardized_voices
