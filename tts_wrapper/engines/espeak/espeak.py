from __future__ import annotations
from typing import Any, Optional
from collections.abc import Generator
from tts_wrapper.tts import AbstractTTS
from . import eSpeakClient
from .ssml import eSpeakSSML
import logging


class eSpeakTTS(AbstractTTS):
    """High-level TTS interface for eSpeak."""

    def __init__(self, client: eSpeakClient, lang: Optional[str] = None, voice: Optional[str] = None) -> None:
        """Initialize the eSpeak TTS interface."""
        super().__init__()
        self._client = client
        self.set_voice(voice or "gmw/en")
        self._ssml = eSpeakSSML()
        self.audio_rate = 22050
        self.generated_audio = bytearray()
        self.word_timings = []
        self.on_end = None 

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to audio bytes."""
        logging.debug("Synthesizing text to audio bytes.")
        self.generated_audio = bytearray()
        self.word_timings = []

        # Wrap text in SSML if not already formatted
        text = self.ssml.add(str(text)) if not self._is_ssml(str(text)) else str(text)

        # Call the client for synthesis
        audio_data, word_timings = self._client.synth(text, self._voice)
        if self.on_end:
            self.on_end() 
        self.word_timings = self._process_word_timings(word_timings, text)
        self.set_timings(self.word_timings)

        return audio_data


    def synth_to_bytestream(
            self, text: Any, format: Optional[str] = "wav"
        ) -> Generator[bytes, None, None]:
        """
        Synthesizes text to an in-memory bytestream in the specified audio format.
        Yields audio data chunks as they are generated.
        """
        logging.debug("Synthesizing text to audio bytestream.")
        self.generated_audio = bytearray()
        self.word_timings = []

        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        # Use eSpeakClient to perform synthesis 
        stream_queue, word_timings = self._client.synth_streaming(text, self._voice)
        if self.on_end:
            self.on_end()
        self.word_timings = self._process_word_timings(word_timings, text)
        self.set_timings(self.word_timings)

        while True:
            chunk = stream_queue.get()
            if chunk is None:
                break
            yield chunk

    def _process_word_timings(self, word_timings: list[dict], input_text: str) -> list[tuple[float, float, str]]:
        """Convert raw word timings to (start_time, end_time, word) tuples."""
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, word_info in enumerate(word_timings):
            start_time = word_info["start_time"]
            text_position = word_info["text_position"]
            length = word_info["length"]

            # Extract word text
            word_text = input_text[text_position : text_position + length]

            # Calculate end_time
            end_time = (
                word_timings[i + 1]["start_time"] if i + 1 < len(word_timings) else audio_duration
            )

            # Append the tuple
            processed_timings.append((start_time, end_time, word_text))

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

    def construct_prosody_tag(
        self,
        text: str,
        volume: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        range: Optional[str] = None,
    ) -> str:
        """
        Construct a <prosody> tag using the SSML handler.
        :param text: The text to wrap.
        :param volume: Volume setting (e.g., soft, +1dB).
        :param rate: Rate of speech (e.g., slow, 125%).
        :param pitch: Pitch level (e.g., high, 75).
        :param range: Pitch range (e.g., low, x-high).
        :return: A string with SSML <prosody> wrapping the text.
        """
        kwargs = {
            k: v
            for k, v in {
                "volume": volume,
                "rate": rate,
                "pitch": pitch,
                "range": range,
            }.items()
            if v
        }
        return self._ssml.construct_prosody(text, **kwargs)

    def set_property(self, property_name: str, value: float | str) -> None:
        """Set a property for the TTS engine and update its internal state."""
        super().set_property(property_name, value)
        # Update SSML defaults for corresponding properties
        if property_name in ("rate", "volume", "pitch"):
            self._ssml.add(f'<prosody {property_name}="{value}"/>', clear=True)