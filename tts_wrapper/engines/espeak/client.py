import logging
import queue
from typing import Any

from ._espeak import EspeakLib


class eSpeakClient:
    """Client interface for the eSpeak TTS engine."""

    def __init__(self) -> None:
        """Initialize the eSpeak library client."""
        self._espeak = EspeakLib()
        logging.debug("eSpeak client initialized")

    def synth(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech using EspeakLib and return raw audio and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth(ssml, ssml=True)

    def synth_streaming(self, ssml: str, voice: str) -> tuple[queue.Queue, list[dict]]:
        """Stream synthesis using EspeakLib and return a queue and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth_streaming(ssml, ssml=True)

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from eSpeak."""
        voices = self._espeak.get_available_voices()
        return [
            {
                "id": voice["id"],
                "name": voice["name"],
                "language_codes": voice["language_codes"],
                "gender": voice["gender"],
                "age": voice.get("age", 0),  # Age is optional
            }
            for voice in voices
        ]
