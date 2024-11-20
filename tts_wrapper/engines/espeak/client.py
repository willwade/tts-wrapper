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

    def synth(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech and return raw audio data and word timings."""
        self._espeak.set_voice(voice)
        ssml_text = str(ssml)
        audio_data, word_timings = self._espeak.speak_and_wait(ssml_text, ssml=True)
        logging.debug("Client - Audio size: %d bytes", len(audio_data))
        logging.debug("Client - Word timings: %s", word_timings)
        return audio_data, word_timings

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
