from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.engines.espeak.ssml import eSpeakSSML
from tts_wrapper.tts import AbstractTTS

from ._espeak import EspeakLib

if TYPE_CHECKING:
    import queue
    from pathlib import Path


class eSpeakClient(AbstractTTS):
    """Client interface for the eSpeak TTS engine."""

    def __init__(self) -> None:
        """Initialize the eSpeak library client."""
        super().__init__()
        self._espeak = EspeakLib()
        self.audio_rate = 22050  # Default sample rate for eSpeak
        self.ssml = eSpeakSSML()
        logging.debug("eSpeak client initialized")

        # Set default voice
        self.voice_id = "en"  # Default to English
        self._espeak.set_voice(self.voice_id)

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in eSpeak)
        """
        self.voice_id = voice_id
        self._espeak.set_voice(voice_id)

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        # Use provided voice_id or the one set with set_voice
        if voice_id:
            self._espeak.set_voice(voice_id)
        elif hasattr(self, "voice_id") and self.voice_id:
            self._espeak.set_voice(self.voice_id)

        # Convert text to string safely
        try:
            text_str = str(text)
            logging.debug(
                f"Text to synthesize: {text_str[:100]}{'...' if len(text_str) > 100 else ''}"
            )
        except Exception as e:
            logging.error(f"Failed to convert text to string: {e}")
            # Return empty audio as fallback
            return b""

        # Check if the text is SSML
        try:
            is_ssml = self._is_ssml(text_str)
            logging.debug(f"Is SSML: {is_ssml}")
        except Exception as e:
            logging.error(f"Failed to check if text is SSML: {e}")
            is_ssml = False

        # Try synthesis with appropriate flags
        try:
            # Get audio data with word timings
            logging.debug(f"Synthesizing with SSML={is_ssml}")
            audio_bytes, _ = self._espeak.synth(text_str, ssml=is_ssml)
            logging.debug(f"Synthesis successful, audio size: {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logging.error(f"Synthesis failed: {e}")
            # If SSML processing fails, try again with plain text
            if is_ssml:
                try:
                    logging.warning(
                        "SSML processing failed, falling back to plain text"
                    )
                    audio_bytes, _ = self._espeak.synth(text_str, ssml=False)
                    logging.debug(
                        f"Plain text synthesis successful, audio size: {len(audio_bytes)} bytes"
                    )
                    return audio_bytes
                except Exception as e2:
                    logging.error(f"Plain text synthesis also failed: {e2}")
                    # Return empty audio as fallback
                    return b""
            # If it's not SSML, return empty audio as fallback
            logging.error("Returning empty audio due to synthesis failure")
            return b""

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    def synth_raw(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech using EspeakLib and return raw audio and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth(ssml, ssml=True)

    def synth_streaming(self, ssml: str, voice: str) -> tuple[queue.Queue, list[dict]]:
        """Stream synthesis using EspeakLib and return a queue and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth_streaming(ssml, ssml=True)

    def _is_ssml(self, text: str) -> bool:
        """Check if the text is SSML.

        Args:
            text: The text to check

        Returns:
            True if the text is SSML, False otherwise
        """
        # Simple check for SSML tags
        return text.strip().startswith("<speak") and text.strip().endswith("</speak>")

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable[[], None]]] = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Trigger onStart callbacks
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Use provided voice_id or the one set with set_voice
        if voice_id:
            self._espeak.set_voice(voice_id)
        elif hasattr(self, "voice_id") and self.voice_id:
            self._espeak.set_voice(self.voice_id)

        # Check if the text is SSML
        is_ssml = self._is_ssml(str(text))

        # Convert text to string safely
        text_str = str(text)

        # Synthesize with word timings
        try:
            audio_bytes, word_timings = self._espeak.synth(text_str, ssml=is_ssml)
            self._audio_bytes = audio_bytes

            # Call the callback for each word timing if provided
            if callback is not None:
                # For eSpeak, we need to convert the word timings to the expected format
                # eSpeak returns a list of dicts with 'start_time', 'text_position', 'length', 'word'
                # We need to convert this to (word, start_time, end_time) format
                if word_timings:
                    for timing in word_timings:
                        if "start_time" in timing and "word" in timing:
                            # Convert start_time to seconds (it's in milliseconds)
                            start_time = float(timing["start_time"]) / 1000.0
                            # Estimate end_time (eSpeak doesn't provide it directly)
                            # Assume 0.1 seconds per word as a rough estimate
                            end_time = start_time + 0.1
                            callback(timing["word"], start_time, end_time)
                else:
                    # If no word timings, estimate based on text length
                    words = str(text).split()
                    total_duration = 2.0  # Estimate 2 seconds for the audio
                    time_per_word = total_duration / len(words) if words else 0

                    current_time = 0.0
                    for word in words:
                        end_time = current_time + time_per_word
                        callback(word, current_time, end_time)
                        current_time = end_time
        except Exception as e:
            # If SSML processing fails, try again with plain text
            if is_ssml:
                logging.warning(
                    f"SSML processing failed, falling back to plain text: {e}"
                )
                try:
                    audio_bytes, word_timings = self._espeak.synth(text_str, ssml=False)
                    self._audio_bytes = audio_bytes
                except Exception as e2:
                    logging.error(f"Plain text synthesis also failed: {e2}")
                    # Fallback to regular synthesis without timings
                    self._audio_bytes = self.synth_to_bytes(text_str, voice_id)
            else:
                logging.error(f"Synthesis failed: {e}")
                # Fallback to regular synthesis without timings
                self._audio_bytes = self.synth_to_bytes(text_str, voice_id)

            # Estimate word timings based on text length
            if callback is not None:
                words = str(text).split()
                total_duration = 0.0  # We don't know the duration

                # Try to get duration from the audio bytes
                try:
                    # Estimate 10 words per second as a fallback
                    total_duration = len(words) / 10.0
                except Exception:
                    pass

                time_per_word = total_duration / len(words) if words else 0

                current_time = 0.0
                for word in words:
                    end_time = current_time + time_per_word
                    callback(word, current_time, end_time)
                    current_time = end_time

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from eSpeak.

        Returns:
            List of voice dictionaries with raw language information
        """
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
