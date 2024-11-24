import logging
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from tts_wrapper.tts import AbstractTTS

from .client import AVSynthClient
from .ssml import AVSynthSSML

if TYPE_CHECKING:
    from .client import AVSynthClient


class AVSynthTTS(AbstractTTS):
    """High-level TTS interface for AVSynth."""

    def __init__(self, client: AVSynthClient, voice: str = "en-US") -> None:
        """Initialize the AVSynth TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self.audio_rate = 22050
        self.ssml = AVSynthSSML()
        self.word_timings = []
        self.generated_audio = bytearray()

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to audio bytes."""
        logging.debug("Synthesizing text to audio bytes.")
        self.generated_audio = bytearray()
        self.word_timings = []

        # Wrap text in SSML if not already formatted
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))
        text = str(text)

        # Call the client for synthesis
        audio_data, word_timings = self._client.synth(text, self._voice)
        self.word_timings = word_timings
        self.set_timings(self._process_word_timings(word_timings, text))

        return audio_data

    def synth_to_bytestream(self, text: Any) -> Generator[bytes, None, None]:
        """Synthesize text to an in-memory bytestream."""
        logging.debug("Synthesizing text to audio bytestream.")
        self.generated_audio = bytearray()
        self.word_timings = []

        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        # Streaming synthesis
        stream_queue, word_timings = self._client.synth_streaming(text, self._voice)
        self.word_timings = word_timings
        self.set_timings(self._process_word_timings(word_timings, text))

        while True:
            chunk = stream_queue.get()
            if chunk is None:
                break
            yield chunk

    def get_voices(self) -> list[dict]:
        """Fetch available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """Set the voice and language."""
        self._voice = voice_id

    def _process_word_timings(self, word_timings: list[dict], input_text: str) -> list[tuple]:
        """Convert word timings into the format (start_time, end_time, word)."""
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, word_info in enumerate(word_timings):
            start_time = word_info.get("start_time", 0)
            word_text = word_info.get("word", "")

            # Determine the end time
            end_time = word_timings[i + 1].get("start_time", audio_duration) if i + 1 < len(word_timings) else audio_duration

            processed_timings.append((start_time, end_time, word_text))

        return processed_timings

    def get_audio_duration(self) -> float:
        """Return the duration of the generated audio."""
        return len(self.generated_audio) / (2 * self.audio_rate)