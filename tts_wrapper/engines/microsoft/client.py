from typing import List, Dict, Any, Optional
import azure.cognitiveservices.speech as speechsdk
from tts_wrapper.tts import FileFormat

from ...exceptions import ModuleNotInstalled

try:
    import requests
except ImportError:
    requests = None  # type: ignore

FORMATS = {
    "wav": "riff-24khz-16bit-mono-pcm",
    "mp3": "audio-24khz-160kbitrate-mono-mp3",
}

class MicrosoftClient:
    @property
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(
        self, credentials: str, region: Optional[str] = None
    ) -> None:
        if speechsdk is None:
            raise ModuleNotInstalled("speechsdk")

        self._credentials = credentials
        self._region = region or "eastus"
        self.speech_config = speechsdk.SpeechConfig(subscription=self._credentials, region=self._region)


    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service."""
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
        result = speech_synthesizer.get_voices_async().get()
        # Check the result
        if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
            standardized_voices = []
            for voice in result.voices:
                voice_dict = {
                    'id': voice.short_name,
                    'language_codes': [voice.locale],
                    'display_name': voice.local_name,
                    'gender': voice.gender.name,  # Convert enum to string
                }
                standardized_voices.append(voice_dict)
            return standardized_voices
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled; error details: {cancellation_details.error_details}")
            return []  # Return an empty list or raise an exception

