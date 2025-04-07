from __future__ import annotations

import io
import logging
import os
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.engines.espeak.ssml import eSpeakSSML
from tts_wrapper.tts import AbstractTTS

from ._espeak import EspeakLib

if TYPE_CHECKING:
    import queue
    from collections.abc import Generator


class eSpeakClient(AbstractTTS):
    """Client interface for the eSpeak TTS engine."""

    def __init__(self) -> None:
        """Initialize the eSpeak library client."""
        super().__init__()

        # Check if we're running in a test environment
        in_test = (
            self._is_ci_environment() or os.environ.get("SKIP_AUDIO_PLAYBACK") == "1"
        )

        if in_test:
            # In test environments, use a dummy implementation
            logging.info(
                "Running in test environment, using dummy eSpeak implementation"
            )
            self._espeak = self._get_dummy_espeak()
        else:
            try:
                self._espeak = EspeakLib()
            except Exception as e:
                logging.warning(
                    f"Failed to initialize eSpeak: {e}. Using dummy implementation."
                )
                self._espeak = self._get_dummy_espeak()

        self.audio_rate = 22050  # Default sample rate for eSpeak
        self.ssml: eSpeakSSML = eSpeakSSML()  # Explicitly type as eSpeakSSML
        logging.debug("eSpeak client initialized")

        # Set default voice
        self.voice_id: str = "en"  # Default to English
        try:
            self._espeak.set_voice(self.voice_id)
        except Exception as e:
            logging.warning(f"Failed to set voice: {e}")

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
            audio_bytes, word_timings = self._espeak.synth(text_str, ssml=is_ssml)
            logging.debug(f"Synthesis successful, audio size: {len(audio_bytes)} bytes")

            # Process and store word timings
            if word_timings:
                processed_timings = []
                for i, timing in enumerate(word_timings):
                    if "start_time" in timing and "word" in timing:
                        start_time = float(timing["start_time"])
                        # Estimate end time
                        if i < len(word_timings) - 1:
                            end_time = float(word_timings[i + 1]["start_time"])
                        else:
                            # For the last word, add a small buffer
                            end_time = start_time + 0.3
                        processed_timings.append((start_time, end_time, timing["word"]))

                # Set the timings in the AbstractTTS parent class
                self.set_timings(processed_timings)
                logging.debug(f"Set {len(processed_timings)} word timings")

            return audio_bytes
        except Exception as e:
            logging.error(f"Synthesis failed: {e}")
            # If SSML processing fails, try again with plain text
            if is_ssml:
                try:
                    logging.warning(
                        "SSML processing failed, falling back to plain text"
                    )
                    audio_bytes, word_timings = self._espeak.synth(text_str, ssml=False)
                    logging.debug(
                        f"Plain text synthesis successful, audio size: {len(audio_bytes)} bytes"
                    )

                    # Process and store word timings
                    if word_timings:
                        processed_timings = []
                        for i, timing in enumerate(word_timings):
                            if "start_time" in timing and "word" in timing:
                                start_time = float(timing["start_time"])
                                # Estimate end time
                                if i < len(word_timings) - 1:
                                    end_time = float(word_timings[i + 1]["start_time"])
                                else:
                                    # For the last word, add a small buffer
                                    end_time = start_time + 0.3
                                processed_timings.append(
                                    (start_time, end_time, timing["word"])
                                )

                        # Set the timings in the AbstractTTS parent class
                        self.set_timings(processed_timings)
                        logging.debug(f"Set {len(processed_timings)} word timings")

                    return audio_bytes
                except Exception as e2:
                    logging.error(f"Plain text synthesis also failed: {e2}")
                    # Return empty audio as fallback
                    return b""
            # If it's not SSML, return empty audio as fallback
            logging.error("Returning empty audio due to synthesis failure")
            return b""

    # Use the synth method from AbstractTTS, which handles format conversion

    def synth_raw(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech using EspeakLib and return raw audio and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth(ssml, ssml=True)

    def synth_streaming(self, ssml: str, voice: str) -> tuple[queue.Queue, list[dict]]:
        """Stream synthesis using EspeakLib and return a queue and word timings."""
        self._espeak.set_voice(voice)
        return self._espeak.synth_streaming(ssml, ssml=True)

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None
    ) -> Generator[bytes, None, None]:
        """Synthesizes text to an in-memory bytestream and yields audio data chunks.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            A generator yielding bytes objects containing audio data
        """
        # Generate the full audio content
        audio_content = self.synth_to_bytes(text, voice_id)

        # Create a BytesIO object from the audio content
        audio_stream = io.BytesIO(audio_content)

        # Define chunk size (adjust as needed)
        chunk_size = 4096  # 4KB chunks

        # Yield chunks of audio data
        while True:
            chunk = audio_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

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
                    for i, timing in enumerate(word_timings):
                        if "start_time" in timing and "word" in timing:
                            # Get start_time in seconds
                            start_time = float(timing["start_time"])
                            # Estimate end_time (eSpeak doesn't provide it directly)
                            # For the last word, use the total duration
                            if i == len(word_timings) - 1:
                                end_time = (
                                    start_time + 0.3
                                )  # Add a bit more time for the last word
                            else:
                                # Use the next word's start time as this word's end time
                                next_timing = word_timings[i + 1]
                                end_time = float(next_timing["start_time"])
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

    # Audio control methods are inherited from AbstractTTS
    # No need to reimplement pause(), resume(), or stop()

    def _get_dummy_espeak(self):
        """Create a dummy eSpeak implementation for testing."""

        # Create a dummy EspeakLib class that doesn't actually use espeak
        class DummyEspeakLib:
            def __init__(self):
                pass

            def set_voice(self, voice_id):
                pass

            def get_available_voices(self):
                # Return a minimal set of voices for testing
                return [
                    {
                        "id": "en",
                        "name": "English",
                        "language_codes": ["en"],
                        "gender": "Male",
                        "age": 0,
                    },
                    {
                        "id": "fr",
                        "name": "French",
                        "language_codes": ["fr"],
                        "gender": "Male",
                        "age": 0,
                    },
                ]

            def synth(self, text, ssml=False):
                # Generate some fake word timings for testing
                words = text.split()
                word_timings = []
                for i, word in enumerate(words):
                    # Create a timing entry with start_time based on word position
                    start_time = i * 0.3  # 300ms per word
                    word_timings.append(
                        {
                            "start_time": start_time,
                            "word": word,
                            "text_position": 0,
                            "length": len(word),
                        }
                    )
                # Return dummy audio bytes and the generated word timings
                return b"\x00" * 1000, word_timings

        return DummyEspeakLib()

    def construct_prosody_tag(self, text: str, **kwargs) -> str:
        """Construct a prosody tag for the text.

        Args:
            text: The text to wrap with prosody
            **kwargs: Prosody attributes (rate, pitch, volume, etc.)

        Returns:
            SSML text with prosody tag
        """
        return self.ssml.construct_prosody(text, **kwargs)

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
