from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.engines.utils import process_wav
from tts_wrapper.exceptions import ModuleNotInstalled
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path

Credentials = tuple[str, str, str]

FORMATS = {
    "wav": "pcm",
    "mp3": "mp3",
}


class PollyClient(AbstractTTS):
    def __init__(
        self,
        credentials: Credentials | None = None,
        verify_ssl: bool = False,
    ) -> None:
        super().__init__()
        self.audio_rate = 16000  # Default sample rate for Polly
        try:
            import boto3
        except ImportError:
            msg = "boto3"
            raise ModuleNotInstalled(msg)

        from boto3.session import Session

        if credentials is None:
            boto_session = Session()
        else:
            region, aws_key_id, aws_access_key = credentials
            boto_session = Session(
                aws_access_key_id=aws_key_id,
                aws_secret_access_key=aws_access_key,
                region_name=region,
            )
        self._client = boto_session.client("polly", verify=verify_ssl)

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in Polly)
        """
        self.voice_id = voice_id

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        # If no voice is set, use a default voice
        if voice is None:
            voice = "Joanna"

        # Determine if the text is SSML
        text_type = "ssml" if str(text).strip().startswith("<speak>") else "text"

        # Synthesize speech
        raw = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="pcm",
            VoiceId=voice,
            TextType=text_type,
            Text=str(text),
        )["AudioStream"].read()

        return process_wav(raw)

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
            output_format: Format to save as ("wav" or "mp3")
            voice_id: Optional voice ID to use for this synthesis
        """
        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    def synth_raw(self, text: str, voice: str) -> bytes:
        """Legacy method for backward compatibility."""
        # Determine if the text is SSML
        text_type = "ssml" if str(text).strip().startswith("<speak>") else "text"

        raw = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="pcm",
            VoiceId=voice,
            TextType=text_type,
            Text=text,
        )["AudioStream"].read()

        return process_wav(raw)

    def synth_with_timings(
        self,
        text: str,
        voice: str,
    ) -> tuple[bytes, list[tuple[float, str]]]:
        audio_data, word_timings = self._synth_with_marks(text, voice)
        return audio_data, word_timings

    def _synth_with_marks(
        self,
        text: str,
        voice: str,
    ) -> tuple[bytes, list[tuple[float, str]]]:
        # Determine if the text is SSML
        text_type = "ssml" if str(text).strip().startswith("<speak>") else "text"

        # Get speech marks
        marks_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="json",
            VoiceId=voice,
            TextType=text_type,
            Text=text,
            SpeechMarkTypes=["word"],
        )

        speech_marks_str = marks_response["AudioStream"].read().decode("utf-8")
        speech_marks_lines = speech_marks_str.splitlines()
        speech_marks = [json.loads(line) for line in speech_marks_lines]
        word_timings = [
            (float(mark["time"]) / 1000, mark["value"])
            for mark in speech_marks
            if mark["type"] == "word"
        ]

        # Get audio data
        audio_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="pcm",
            VoiceId=voice,
            TextType=text_type,
            Text=text,
        )

        audio_data = audio_response["AudioStream"].read()

        audio_data = process_wav(audio_data)

        return audio_data, word_timings

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Amazon Polly.

        Returns:
            List of voice dictionaries with raw language information
        """
        response = self._client.describe_voices()
        voices = response.get("Voices", [])
        standardized_voices = []
        for voice in voices:
            standardized_voices.append(
                {
                    "id": voice["Id"],
                    "language_codes": [voice["LanguageCode"]],
                    "name": voice["Name"],
                    "gender": voice["Gender"],
                }
            )
        return standardized_voices

    def check_credentials(self) -> bool:
        """Check if the provided credentials are valid."""
        try:
            self._get_voices()
            return True
        except Exception:
            return False

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable[[], None]]] = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
        """
        # Trigger onStart callbacks
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Get voice ID
        if voice_id is None:
            voice_id = getattr(self, "voice_id", None)

        # If no voice is set, use a default voice
        if voice_id is None:
            voice_id = "Joanna"

        # Get audio data and word timings
        audio_data, word_timings = self._synth_with_marks(str(text), voice_id)

        # Call the callback for each word timing if provided
        if callback is not None:
            for time_ms, word in word_timings:
                callback(word, time_ms, time_ms + 0.3)  # Estimate end time

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()
