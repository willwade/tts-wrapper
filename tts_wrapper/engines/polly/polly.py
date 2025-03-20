from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from . import PollyClient
    from .ssml import PollySSML
else:
    from .ssml import PollySSML


# Define constant for WAV header detection
WAV_HEADER_SIGNATURE = b"RIFF"


class PollyTTS(AbstractTTS):
    def __init__(
        self,
        client: PollyClient,
        lang: str | None = None,
        voice: str | None = None,
    ) -> None:
        super().__init__()
        self._client = client
        self.set_voice(voice or "Joanna", lang or "en-US")
        self._ssml = PollySSML()
        self.audio_rate = 16000
        self.generated_audio: bytes | None = None

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        # Use voice_id if provided, otherwise use the default voice
        voice_to_use = voice_id or self._voice

        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        result = self._client.synth_with_timings(str(text), voice_to_use)

        if isinstance(result, tuple) and len(result) == 2:
            audio_data, word_timings = result
            self.generated_audio = audio_data
        else:
            self.generated_audio = result
            word_timings = []  # or get word timings from somewhere else if available

        processed_timings = self._process_word_timings(word_timings)
        self.set_timings(processed_timings)

        if self.generated_audio and self.generated_audio[:4] == WAV_HEADER_SIGNATURE:
            self.generated_audio = self._strip_wav_header(self.generated_audio)

        # At this point, generated_audio should never be None
        if not self.generated_audio:
            return b""  # Return empty bytes as a fallback

        return self.generated_audio

    def _process_word_timings(
        self,
        word_timings: list[tuple[float, str]],
    ) -> list[tuple[float, float, str]]:
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, (start, word) in enumerate(word_timings):
            if i < len(word_timings) - 1:
                end = word_timings[i + 1][0]
            else:
                end = min(
                    start + 0.5,
                    audio_duration,
                )  # Use the lesser of 0.5s or remaining audio duration
            processed_timings.append((start, end, word))

        return processed_timings

    def get_audio_duration(self) -> float:
        if self.generated_audio:
            return len(self.generated_audio) / 2 / self.audio_rate
        return 0.0

    @property
    def ssml(self) -> PollySSML:
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str | None = None) -> None:
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or "en-US"

    def construct_prosody_tag(self, text: str) -> str:
        properties = []

        volume_in_number = self.get_property("volume")
        if volume_in_number and volume_in_number != "":
            volume_in_words = self.mapped_to_predefined_word(volume_in_number)
            properties.append(f'volume="{volume_in_words}"')

        prosody_content = " ".join(properties)
        return f"<prosody {prosody_content}>{text}</prosody>"

    def mapped_to_predefined_word(self, volume: str) -> str:
        try:
            volume_in_float = float(volume)
        except ValueError:
            return "medium"  # Default to medium if not a valid number

        # Use a mapping dictionary instead of multiple returns
        volume_map = {
            (0, 0): "silent",
            (1, 20): "x-soft",
            (21, 40): "soft",
            (41, 60): "medium",
            (61, 80): "loud",
            (81, 100): "x-loud",
        }

        for (min_val, max_val), word in volume_map.items():
            if min_val <= volume_in_float <= max_val:
                return word

        return "medium"  # Default if out of all ranges
