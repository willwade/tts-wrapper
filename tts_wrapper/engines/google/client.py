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
        voices = self._client.list_voices()
        return [{
            'name': voice.name,
            'language_codes': voice.language_codes,
            'ssml_gender': voice.ssml_gender,
            'natural_sample_rate_hertz': voice.natural_sample_rate_hertz
        } for voice in voices.voices]