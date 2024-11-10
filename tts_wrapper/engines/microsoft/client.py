from typing import Any, Dict, List, Optional, Tuple

from tts_wrapper.exceptions import ModuleNotInstalled

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None  # type: ignore


Credentials = Tuple[str, Optional[str]]

FORMATS = {"wav": "Riff24Khz16BitMonoPcm"}


class MicrosoftClient:
    def __init__(
        self,
        credentials: Optional[Credentials] = None,
    ) -> None:
        if speechsdk is None:
            msg = "speechsdk"
            raise ModuleNotInstalled(msg)

        if not credentials or not credentials[0]:
            msg = "subscription_key is required"
            raise ValueError(msg)

        self._subscription_key = credentials[0]
        self._subscription_region = credentials[1] or "eastus"

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self._subscription_key, region=self._subscription_region,
        )

    def check_credentials(self) -> bool:
        """Verifies that the provided credentials are valid by initializing SpeechConfig."""
        try:
            # Attempt to create a synthesizer using the speech config
            # This checks if the subscription key and region are accepted without any API call.
            speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
            )
            return True
        except Exception:
            return False

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service using REST API with optimized connection handling."""
        import requests

        # Extract the subscription key and region from the speech_config
        subscription_key = self.speech_config.subscription_key
        region = self.speech_config.region

        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}

        try:
            # Use a Session to reuse the connection
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.get(url)
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.exception("Error fetching voices: %s", e)
            msg = f"Failed to fetch voices; error details: {e}"
            raise Exception(msg)

        voices = response.json()
        standardized_voices = []
        for voice in voices:
            voice_dict = {
                "id": voice["ShortName"],
                "language_codes": [voice["Locale"]],
                "name": voice["LocalName"],
                "gender": voice["Gender"],  # 'Gender' is already a string
            }
            standardized_voices.append(voice_dict)
        return standardized_voices
