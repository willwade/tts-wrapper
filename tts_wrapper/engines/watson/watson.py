import logging
from typing import Any, Dict, List, Optional, Tuple

from tts_wrapper.tts import AbstractTTS

from . import WatsonClient, WatsonSSML


class WatsonTTS(AbstractTTS):
    def __init__(
        self,
        client: WatsonClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._client = client
        self._voice = voice or "en-US_LisaV3Voice"
        self.audio_rate = 22050
        self.word_timings = []

    def get_audio_duration(self) -> float:
        if self.generated_audio:
            return len(self.generated_audio) / (
                self.audio_rate * 2
            )  # Assuming 16-bit audio
        return 0.0

    def _process_word_timings(
        self, word_timings: List[Tuple[float, str]],
    ) -> List[Tuple[float, float, str]]:
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, (start_time, word) in enumerate(word_timings):
            if i < len(word_timings) - 1:
                end_time = word_timings[i + 1][0]
            else:
                end_time = min(
                    float(start_time) + 0.5, audio_duration,
                )  # Convert start_time to float
            processed_timings.append((float(start_time), float(end_time), word))

        return processed_timings

    def synth_to_bytes(self, text: Any) -> bytes:
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        try:
            self.generated_audio = self._client.synth_with_timings(
                str(text), self._voice,
            )
            self.audio_format = "wav"

            processed_timings = self._process_word_timings(self._client.word_timings)
            self.set_timings(processed_timings)

            if self.generated_audio[:4] == b"RIFF":
                self.generated_audio = self._strip_wav_header(self.generated_audio)

            return self.generated_audio
        except Exception as e:
            logging.exception("Error in synth_to_bytes: %s", e)
            raise

    @property
    def ssml(self) -> WatsonSSML:
        return WatsonSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Watson TTS service."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str) -> None:
        """Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(
            voice_id,
        )  # Optionally manage voice at the AbstractTTS level if needed
        self._voice = voice_id
        self._lang = lang_id

    def construct_prosody_tag(self, text: str) -> str:
        pass
