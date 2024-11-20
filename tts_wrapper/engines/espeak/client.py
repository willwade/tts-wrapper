from typing import Any

from tts_wrapper.engines.utils import process_wav

from ._espeak import EspeakLib

import logging 

class eSpeakClient:
    """Client interface for the eSpeak TTS engine."""

    def __init__(self) -> None:
        """Initialize the eSpeak library client."""
        self._espeak = EspeakLib()
        logging.debug("eSpeak client initialized")

    def synth(self, ssml: str, voice: str) -> bytes:
        """Synthesize speech and return audio data."""
        self._espeak.set_voice(voice)
        self._espeak.speak(ssml, ssml=True)
        # Assuming process_wav is used to standardize audio formats
        return process_wav(self._espeak.generated_audio)

    def synth_with_timings(self, ssml: str, voice: str) -> tuple[bytes, list[tuple[float, str]]]:
        """Synthesize speech and return audio data with word timings."""
        self._espeak.set_voice(voice)
        self._espeak.speak(ssml, ssml=True)

        # Extract word timings as (start_time, word_text)
        word_timings = [
            (word["start_time"], ssml[word["text_position"]:word["text_position"] + word["length"]])
            for word in self._espeak.word_timings
        ]

        processed_audio = process_wav(self._espeak.generated_audio)
        return processed_audio, word_timings

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from eSpeak."""
        voices = self._espeak.get_available_voices()
        standardized_voices = []
        for voice in voices:
            standardized_voices.append({
                "id": voice["id"],
                "name": voice["name"],
                "language_codes": voice["language_codes"],
                "gender": voice["gender"],
                "age": voice.get("age", 0),  # Age is optional
            })
        return standardized_voices
