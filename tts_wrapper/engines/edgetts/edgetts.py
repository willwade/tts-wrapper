import logging
from typing import Any, Generator
import asyncio
from tts_wrapper.tts import AbstractTTS

from ._typing import TTSChunk, Voice
from .client import EdgeTTSClient
from .ssml import EdgeSSML


class EdgeTTS(AbstractTTS):
    """Microsoft Edge TTS Engine."""

    def __init__(self, client: EdgeTTSClient | None = None, proxy: str | None = None, voice: str = "en-US-EmmaMultilingualNeural"):
        super().__init__()
        self._client = client or EdgeTTSClient(proxy)
        self.set_voice(voice)
        self._ssml = EdgeSSML()
        self.generated_audio = bytearray()
        self.word_timings = []

    def synth_to_bytes(self, text: str) -> bytes:
        """Convert text to audio bytes synchronously."""
        logging.debug("Synthesizing text to audio bytes.")
        ssml = self._ssml.add(text)
        audio, metadata = asyncio.run(self._client.synth(ssml, self._voice))  # Use asyncio.run here
        self.word_timings = self._process_word_timings(metadata)
        self.set_timings(self.word_timings)
        return audio

    def synth_to_bytestream(self, text: str) -> Generator[bytes, None, None]:
        """Stream synthesized audio in chunks."""
        ssml = self._ssml.add(text)
        audio, metadata = self._client.synth(ssml, self._voice)
        self.word_timings = self._process_word_timings(metadata)
        self.set_timings(self.word_timings)

        for i in range(0, len(audio), 1024):
            yield audio[i:i+1024]

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetch available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str | None = None) -> None:
        """Set the voice for synthesis."""
        if not isinstance(voice_id, str):
            raise ValueError("voice_id must be a string")
        if lang_id is not None and not isinstance(lang_id, str):
            raise ValueError("lang_id must be a string")
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or "en"

    def _process_word_timings(self, metadata: list[TTSChunk]) -> list[tuple[float, float, str]]:
        """Process word boundary metadata into timings."""
        timings = []
        for chunk in metadata:
            if chunk["type"] == "WordBoundary":
                timings.append((chunk["offset"], chunk["offset"] + chunk["duration"], chunk["text"]))
        return timings

    @property
    def ssml(self) -> EdgeSSML:
        """Access the SSML handler."""
        return self._ssml