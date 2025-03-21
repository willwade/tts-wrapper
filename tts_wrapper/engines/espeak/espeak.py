from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from tts_wrapper.tts import AbstractTTS

from .ssml import eSpeakSSML

if TYPE_CHECKING:
    from collections.abc import Generator

    from tts_wrapper.ssml import AbstractSSMLNode

    from . import eSpeakClient


class eSpeakTTS(AbstractTTS):
    """High-level TTS interface for eSpeak."""

    def __init__(
        self, client: eSpeakClient, lang: str | None = None, voice: str | None = None
    ) -> None:
        """Initialize the eSpeak TTS interface."""
        super().__init__()
        self._client = client
        self.set_voice(voice or "gmw/en")
        self._ssml = eSpeakSSML()
        self.audio_rate = 22050
        self.generated_audio = bytearray()
        self.word_timings: list[tuple[float, float, str]] = []
        self.on_end = None

    def synth_to_bytes(
        self, text: str | AbstractSSMLNode, voice_id: str | None = None
    ) -> bytes:
        """Convert text to audio bytes.

        Args:
            text: Text to synthesize, can be SSML formatted.
            voice_id: Optional voice ID to use for synthesis. If None, uses the default voice.

        Returns:
            Audio bytes for playback.
        """
        text_str = str(text)

        # Use voice_id if provided, otherwise use the default voice
        voice_to_use = voice_id or self._voice

        # Call the client for synthesis
        audio_data, word_timings = self._client.synth(text_str, voice_to_use)
        if not audio_data:
            msg = "Failed to synthesize audio"
            raise ValueError(msg)

        # Process word timings and set them
        processed_timings = self._process_word_timings(word_timings, text_str)
        self.set_timings(processed_timings)

        return audio_data

    def synth_to_bytestream(
        self, text: Any, format: str | None = "wav", voice_id: str | None = None
    ) -> tuple[Generator[bytes, None, None], list[dict]]:
        """
        Synthesizes text to an in-memory bytestream in the specified audio format.
        Yields audio data chunks as they are generated.

        Args:
            text: Text to synthesize, can be SSML formatted.
            format: Output audio format, default is "wav".
            voice_id: Optional voice ID to use for synthesis. If None, uses the default voice.

        Returns:
            A tuple containing:
            - A generator yielding bytes objects containing audio data
            - A list of word timing dictionaries
        """
        logging.debug("Synthesizing text to audio bytestream.")
        self.generated_audio = bytearray()
        self.word_timings = []

        # Use voice_id if provided, otherwise use the default voice
        voice_to_use = voice_id or self._voice

        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        # Use eSpeakClient to perform synthesis
        stream_queue, word_timings = self._client.synth_streaming(text, voice_to_use)
        self.word_timings = self._process_word_timings(word_timings, text)
        self.set_timings(self.word_timings)

        def audio_generator():
            while True:
                chunk = stream_queue.get()
                if chunk is None:
                    break
                yield chunk

        return audio_generator(), [
            {"start": start, "end": end, "word": word}
            for start, end, word in self.word_timings
        ]

    def _process_word_timings(
        self, word_timings: list[dict], input_text: str
    ) -> list[tuple[float, float, str]]:
        """Process raw word timings and format them as tuples.

        Parameters
        ----------
        word_timings: List of dictionaries with raw word timing information.
        input_text: The original text that was synthesized.

        Returns
        -------
        List of tuples in the format (start_time, end_time, word).
        """
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, word_info in enumerate(word_timings):
            start_time = word_info["start_time"]
            word_text = word_info["word"]

            # Determine the end time
            if i + 1 < len(word_timings):
                end_time = word_timings[i + 1]["start_time"]
            else:
                end_time = audio_duration  # Last word ends with audio duration

            # Append the processed tuple
            processed_timings.append((start_time, end_time, word_text))

            # Debugging for validation
            duration = end_time - start_time
            logging.debug(
                f"Word: '{word_text}', Start: {start_time}, "
                f"End: {end_time}, Duration: {duration:.3f}s"
            )

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

    def set_voice(self, voice_id: str, lang_id: str | None = None) -> None:
        """Set the voice and language."""
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or "en"

    def construct_prosody_tag(
        self,
        text: str,
        volume: str | None = None,
        rate: str | None = None,
        pitch: str | None = None,
        range: str | None = None,
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
