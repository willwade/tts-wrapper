from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import requests

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator


logger = logging.getLogger(__name__)


class UpliftAIClient(AbstractTTS):
    """Client for the UpliftAI text-to-speech API."""

    BASE_URL = "https://api.upliftai.org/v1/synthesis/text-to-speech"
    STREAM_URL = f"{BASE_URL}/stream"
    DEFAULT_VOICE = "v_8eelc901"  # Info/Education Urdu

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__()
        self.api_key = api_key or os.getenv("UPLIFTAI_KEY")
        if not self.api_key:
            msg = "UpliftAI API key is required. Set UPLIFTAI_KEY or pass api_key."
            raise ValueError(msg)

        self.headers = {"Authorization": self.api_key, "Content-Type": "application/json"}
        self.audio_rate = 22050
        self.voice_id = self.DEFAULT_VOICE

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice for synthesis."""
        self.voice_id = voice_id
        if lang:
            self.lang = lang

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio bytes using the non-streaming endpoint."""
        voice = voice_id or self.voice_id or self.DEFAULT_VOICE
        payload = {
            "voiceId": voice,
            "text": str(text),
            "outputFormat": "WAV_22050_16",
        }
        response = requests.post(self.BASE_URL, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.content

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None
    ) -> Generator[bytes, None, None]:
        """Stream synthesized audio chunks from the API."""
        voice = voice_id or self.voice_id or self.DEFAULT_VOICE
        payload = {
            "voiceId": voice,
            "text": str(text),
            "outputFormat": "WAV_22050_16",
        }
        with requests.post(
            self.STREAM_URL, json=payload, headers=self.headers, stream=True, timeout=30
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to a file."""
        audio_bytes = self.synth_to_bytes(text, voice_id)
        with Path(output_file).open("wb") as f:
            f.write(audio_bytes)

    def _get_voices(self) -> list[dict[str, Any]]:
        """Return the list of available voices.

        The UpliftAI service does not provide a voices endpoint,
        so the voices are hardcoded.
        """
        return [
            {
                "id": "v_meklc281",
                "name": "Info/Education V2",
                "gender": "neutral",
                "language_codes": ["ur"],
            },
            {
                "id": "v_8eelc901",
                "name": "Info/Education",
                "gender": "neutral",
                "language_codes": ["ur"],
            },
            {
                "id": "v_30s70t3a",
                "name": "Nostalgic News",
                "gender": "neutral",
                "language_codes": ["ur"],
            },
            {
                "id": "v_yypgzenx",
                "name": "Dada Jee",
                "gender": "male",
                "language_codes": ["ur"],
            },
            {
                "id": "v_kwmp7zxt",
                "name": "Gen Z",
                "gender": "neutral",
                "language_codes": ["ur"],
            },
            {"id": "v_sd0kl3m9", "name": "Female", "gender": "female", "language_codes": ["sd"]},
            {
                "id": "v_sd6mn4p2",
                "name": "Male Calm",
                "gender": "male",
                "language_codes": ["sd"],
            },
            {
                "id": "v_sd9qr7x5",
                "name": "Male News",
                "gender": "male",
                "language_codes": ["sd"],
            },
            {
                "id": "v_bl0ab8c4",
                "name": "Balochi Male",
                "gender": "male",
                "language_codes": ["bal"],
            },
            {
                "id": "v_bl1de2f7",
                "name": "Balochi Female",
                "gender": "female",
                "language_codes": ["bal"],
            },
        ]

    def check_credentials(self) -> bool:  # pragma: no cover - network call
        """Verify that the API key works by making a small request."""
        try:
            payload = {
                "voiceId": self.voice_id or self.DEFAULT_VOICE,
                "text": "ping",
                "outputFormat": "WAV_22050_16",
            }
            response = requests.post(self.BASE_URL, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return True
        except Exception:
            logger.debug("UpliftAI credential check failed", exc_info=True)
            return False

    def connect(self, event_name: str, callback: Callable) -> None:
        """Connect a callback function to an event."""
        super().connect(event_name, callback)
