from typing import Any, Optional
from tts_wrapper.tts import AbstractTTS
from . import eSpeakClient
from .ssml import eSpeakSSML

class eSpeakTTS(AbstractTTS):
    """High-level TTS interface for eSpeak."""

    def __init__(self, client: eSpeakClient, lang: Optional[str] = None, voice: Optional[str] = None) -> None:
        """Initialize the eSpeak TTS interface."""
        super().__init__()
        self._client = client
        self.set_voice(voice or "default", lang or "en")
        self._ssml = eSpeakSSML()
        self.audio_rate = 22050

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to synthesized audio bytes."""
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        audio_data, word_timings = self._client.synth_with_timings(str(text), self._voice)
        self.set_timings(self._process_word_timings(word_timings))

        return audio_data

    def _process_word_timings(self, word_timings: list[tuple[float, str]]) -> list[tuple[float, float, str]]:
        """Process raw word timings into start-end intervals."""
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, (start, word) in enumerate(word_timings):
            end = word_timings[i + 1][0] if i + 1 < len(word_timings) else audio_duration
            processed_timings.append((start, end, word))

        return processed_timings

    def get_audio_duration(self) -> float:
        """Get the duration of the generated audio."""
        return len(self.generated_audio) / (2 * self.audio_rate)

    @property
    def ssml(self) -> eSpeakSSML:
        """Return the SSML handler."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Return available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Set the voice and language."""
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or "en"