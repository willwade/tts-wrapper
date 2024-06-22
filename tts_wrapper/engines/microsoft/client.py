from typing import Tuple, List, Dict, Any, Optional
from tts_wrapper.tts import FileFormat

from ...exceptions import ModuleNotInstalled

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None  # type: ignore


Credentials = Tuple[str, Optional[str]]

class MicrosoftClient:
    FORMATS = {
        "wav": "Riff24Khz16BitMonoPcm",
        "mp3": "Audio24Khz160KBitRateMonoMp3",
    }
    def __init__(
        self,
        credentials: Optional[Credentials] = None,
    ) -> None:
        if speechsdk is None:
            raise ModuleNotInstalled("speechsdk")


        if not credentials or not credentials[0]:
            raise ValueError("subscription_key is required")
        
        self._subscription_key = credentials[0]
        self._subscription_region = credentials[1] or "eastus"
       
        self.speech_config = speechsdk.SpeechConfig(subscription=self._subscription_key, region=self._subscription_region)

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
                    'name': voice.local_name,
                    'gender': voice.gender.name,  # Convert enum to string
                }
                standardized_voices.append(voice_dict)
            return standardized_voices
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.error_details
            print(f"Speech synthesis canceled; error details: {cancellation_details}")
            return []  # Return an empty list or raise an exception

