from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from tts_wrapper.exceptions import ModuleNotInstalled
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None  # type: ignore


Credentials = tuple[str, Optional[str]]

FORMATS = {"wav": "Riff24Khz16BitMonoPcm"}


class MicrosoftClient(AbstractTTS):
    """Client for Microsoft Azure TTS service."""

    def __init__(
        self,
        credentials: Credentials | None = None,
    ) -> None:
        """Initialize the client with credentials.

        Args:
            credentials: Tuple of (subscription_key, region)
        """
        super().__init__()

        if speechsdk is None:
            msg = "speechsdk"
            raise ModuleNotInstalled(msg)

        if not credentials or not credentials[0]:
            msg = "subscription_key is required"
            raise ValueError(msg)

        self._subscription_key = credentials[0]
        self._subscription_region = credentials[1] or "eastus"

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self._subscription_key,
            region=self._subscription_region,
        )

        # Default audio rate for playback
        self.audio_rate = 16000

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

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service.

        Returns:
            List of voice dictionaries with raw language information
        """
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

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use (e.g., "en-US-AriaNeural")
            lang: Optional language code (not used in Microsoft)
        """
        self.speech_config.speech_synthesis_voice_name = voice_id

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes in WAV format
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        # Create a synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)

        # Synthesize text to audio
        result = synthesizer.speak_text_async(str(text)).get()

        # Check for errors
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            msg = f"Speech synthesis failed: {result.reason}"
            raise Exception(msg)

        # Get audio data
        return result.audio_data


    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
