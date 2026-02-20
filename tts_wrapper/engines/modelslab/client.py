"""ModelsLab TTS client implementation."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import TYPE_CHECKING, Any, Callable

import requests

from tts_wrapper.engines.modelslab.ssml import ModelsLabSSML
from tts_wrapper.ssml import AbstractSSMLNode
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class ModelsLabClient(AbstractTTS):
    """
    ModelsLab TTS client implementation.

    Uses the ModelsLab Voice API to generate speech from text.
    Supports multiple voices and languages, with optional emotion tags.

    API docs: https://docs.modelslab.com/voice-cloning/text-to-speech
    """

    API_URL = "https://modelslab.com/api/v6/voice/text_to_speech"

    # Voices that support emotion tags (English only)
    EMOTION_VOICES = {
        "tara", "leah", "jess", "mia", "zoe",   # female
        "leo", "dan", "zac",                      # male
    }

    # All available voices with metadata
    _VOICES = [
        {"id": "madison",  "name": "Madison",  "gender": "Female", "language_codes": ["en"]},
        {"id": "tara",     "name": "Tara",     "gender": "Female", "language_codes": ["en"]},
        {"id": "leah",     "name": "Leah",     "gender": "Female", "language_codes": ["en"]},
        {"id": "jess",     "name": "Jess",     "gender": "Female", "language_codes": ["en"]},
        {"id": "mia",      "name": "Mia",      "gender": "Female", "language_codes": ["en"]},
        {"id": "zoe",      "name": "Zoe",      "gender": "Female", "language_codes": ["en"]},
        {"id": "leo",      "name": "Leo",      "gender": "Male",   "language_codes": ["en"]},
        {"id": "dan",      "name": "Dan",      "gender": "Male",   "language_codes": ["en"]},
        {"id": "zac",      "name": "Zac",      "gender": "Male",   "language_codes": ["en"]},
    ]

    def __init__(
        self,
        api_key: str | None = None,
        voice: str = "madison",
        language: str = "american english",
        speed: float = 1.0,
    ) -> None:
        """
        Initialize the ModelsLab TTS client.

        Args:
            api_key: ModelsLab API key. If None, uses MODELSLAB_API_KEY env var.
            voice: Voice ID to use. Default is "madison".
            language: Language descriptor. Default is "american english".
            speed: Speech speed multiplier (default 1.0).
        """
        super().__init__()

        self.api_key = api_key or os.environ.get("MODELSLAB_API_KEY")
        if not self.api_key:
            msg = (
                "ModelsLab API key is required. Provide it as an argument "
                "or set the MODELSLAB_API_KEY environment variable."
            )
            raise ValueError(msg)

        self.ssml = ModelsLabSSML()  # type: ignore[assignment]
        self.language = language
        self.speed = speed

        self.voice_id = None  # type: ignore[assignment]
        self.set_voice(voice)

        logging.debug("Initialized ModelsLab TTS client with voice %s", voice)

    def connect(self, event_name: str, callback: Callable) -> None:
        """Connect a callback function to an event."""
        super().connect(event_name, callback)

    def _get_voices(self) -> list[dict[str, Any]]:
        """Return available ModelsLab voices."""
        return self._VOICES

    def check_credentials(self) -> bool:
        """
        Check if the provided API key is valid.

        Returns:
            True if credentials are valid, False otherwise.
        """
        try:
            resp = requests.post(
                self.API_URL,
                json={"key": self.api_key, "prompt": "test", "voice_id": "madison"},
                timeout=10,
            )
            # A 401/403 means bad key; 200/422 means key was accepted
            return resp.status_code not in (401, 403)
        except Exception as exc:
            logging.error("Failed to validate ModelsLab credentials: %s", exc)
            return False

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """
        Set the voice for synthesis.

        Args:
            voice_id: Voice identifier (e.g. "madison", "leo").
            lang: Language code (updates self.language when provided).
        """
        available = [v["id"] for v in self._VOICES]
        if voice_id not in available:
            msg = f"Invalid voice '{voice_id}'. Available voices: {', '.join(available)}"
            raise ValueError(msg)
        self.voice_id = voice_id  # type: ignore[assignment]
        if lang:
            self.language = lang
        logging.debug("Set ModelsLab voice to %s", voice_id)

    def _is_ssml(self, text: str) -> bool:
        """Return True if the text looks like SSML."""
        stripped = text.strip()
        return stripped.startswith("<speak>") and stripped.endswith("</speak>")

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """
        Synthesize text to raw audio bytes.

        The ModelsLab API may respond with either inline audio bytes or
        a URL pointing to the generated audio file.  Both cases are handled.

        Args:
            text: Text (or SSML) to synthesise.
            voice_id: Override voice for this call only.

        Returns:
            Raw WAV/MP3 audio bytes.
        """
        voice = voice_id or self.voice_id

        try:
            text_str = str(text)
        except Exception as exc:
            logging.error("Could not convert text to str: %s", exc)
            text_str = ""

        # Strip SSML tags if present (ModelsLab uses plain text)
        if self._is_ssml(text_str):
            text_str = re.sub(r"<[^>]+>", "", text_str).strip()

        # Resolve speed from property overrides; base class defaults rate to ""
        rate = self.get_property("rate")
        speed = float(rate) if rate else self.speed

        payload: dict[str, Any] = {
            "key": self.api_key,
            "prompt": text_str,
            "language": self.language,
            "voice_id": voice,
            "speed": speed,
            "emotion": False,
        }

        try:
            resp = requests.post(self.API_URL, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logging.error("ModelsLab synthesis request failed: %s", exc)
            return b""

        status = data.get("status")

        if status == "error":
            logging.error("ModelsLab API error: %s", data.get("message", data))
            return b""

        # Handle async generation — poll until complete
        if status == "processing":
            audio_url = self._poll_for_url(data)
        elif status == "success":
            outputs = data.get("output", [])
            audio_url = outputs[0] if outputs else None
        else:
            logging.error("Unexpected ModelsLab status: %s", status)
            return b""

        if not audio_url:
            logging.error("ModelsLab returned no audio URL")
            return b""

        return self._download_audio(audio_url)

    def _poll_for_url(
        self,
        initial_response: dict[str, Any],
        max_retries: int = 20,
        poll_interval: float = 2.0,
    ) -> str | None:
        """
        Poll the ModelsLab API until the audio is ready.

        Args:
            initial_response: The initial response dict that had status=processing.
            max_retries: Maximum number of polling attempts.
            poll_interval: Seconds to wait between polls.

        Returns:
            Audio URL string or None on failure.
        """
        fetch_url = initial_response.get("fetch_result") or initial_response.get("link")
        if not fetch_url:
            logging.error("No fetch URL in processing response: %s", initial_response)
            return None

        for attempt in range(max_retries):
            time.sleep(poll_interval)
            try:
                resp = requests.post(
                    fetch_url,
                    json={"key": self.api_key},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "success":
                    outputs = data.get("output", [])
                    return outputs[0] if outputs else None
                if data.get("status") == "error":
                    logging.error("ModelsLab poll error: %s", data.get("message"))
                    return None
                logging.debug("ModelsLab still processing (attempt %d/%d)", attempt + 1, max_retries)
            except Exception as exc:
                logging.warning("ModelsLab poll attempt %d failed: %s", attempt + 1, exc)

        logging.error("ModelsLab audio generation timed out after %d attempts", max_retries)
        return None

    def _download_audio(self, url: str) -> bytes:
        """Download audio from URL and return bytes."""
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            logging.error("Failed to download ModelsLab audio from %s: %s", url, exc)
            return b""

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None
    ) -> Generator[bytes, None, None]:
        """
        Synthesise text and yield audio in chunks.

        ModelsLab does not offer a native streaming API, so audio is fetched
        in full then yielded in 4 KB chunks.

        Args:
            text: Text to synthesise.
            voice_id: Optional voice override.

        Yields:
            Byte chunks of audio data.
        """
        audio = self.synth_to_bytes(text, voice_id=voice_id)
        if not audio:
            yield b""
            return
        chunk_size = 4096
        for i in range(0, len(audio), chunk_size):
            yield audio[i : i + chunk_size]

    def synth(
        self,
        text: str | AbstractSSMLNode,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
        format: str | None = None,
    ) -> None:
        """Synthesise text and save to a file."""
        super().synth(text, output_file, output_format, voice_id, format)

    def set_property(self, property_name: str, value: float | str) -> None:
        """Set a synthesis property (rate/volume/pitch)."""
        super().set_property(property_name, value)
