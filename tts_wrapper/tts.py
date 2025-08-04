"""
Provides an abstract text-to-speech (TTS) class.

with methods for synthesis, playback, and property management.
Designed to be extended by specific TTS engine implementations.
"""

from __future__ import annotations

import io
import logging
import os
import re
import threading
import time
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from threading import Event
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Union,
)

import numpy as np
import sounddevice as sd
import soundfile as sf

from .ssml import AbstractSSMLNode

if TYPE_CHECKING:
    from collections.abc import Generator

# Type Definitions and Constants
FileFormat = Union[str, None]
WordTiming = Union[tuple[float, str], tuple[float, float, str]]
SSML = Union[str, AbstractSSMLNode]
PropertyType = Union[None, float, str]

TIMING_TUPLE_LENGTH_TWO = 2
TIMING_TUPLE_LENGTH_THREE = 3
STEREO_CHANNELS = 2
SIXTEEN_BIT_PCM_SIZE = 2


class AbstractTTS(ABC):
    """
    Abstract class (ABC) for text-to-speech functionalities,
    including synthesis and playback.
    """

    def __init__(self) -> None:
        """Initialize the TTS engine with default values."""
        self.voice_id = None
        self.lang = "en-US"  # Default language

        # Initialize SSML support
        try:
            # Try to import from the new location
            from .engines.google.ssml import GoogleSSML

            self.ssml = GoogleSSML()  # Default SSML implementation
        except ImportError:
            # Fallback to a basic SSML implementation
            from .ssml import BaseSSMLRoot

            self.ssml = BaseSSMLRoot()

        self.stream = None
        self.audio_rate = 44100
        self.audio_bytes = None
        self.playing = Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings: list[tuple[float, float, str]] = []
        self.timers: list[threading.Timer] = []
        self.properties = {"volume": "", "rate": "", "pitch": ""}
        self.callbacks = {"onStart": None, "onEnd": None, "started-word": None}
        self.stream_lock = threading.Lock()

        # addition for pause resume
        # self.sample_rate is audio_rate
        self.channels = 1
        self.sample_width = 2
        self.chunk_size = 1024

        self.isplaying = False
        self.paused = False
        self.position = 0

        self.stream_pyaudio = None
        self.playback_thread = None
        self.pause_timer = None
        self.pyaudio = None
        self._audio_array = None
        self._on_end_triggered = False
        self.on_word_callback = None

    def _is_ci_environment(self) -> bool:
        """Check if we're running in a CI environment."""
        return (
            os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"
        )

    def _get_dummy_pyaudio(self):
        """Create a dummy PyAudio implementation for CI environments."""

        # Create a dummy PyAudio class that doesn't actually play audio
        class DummyPyAudio:
            def __init__(self):
                pass

            def get_format_from_width(self, width):
                return 8  # Dummy format

            def open(self, format=None, channels=None, rate=None, output=None):
                return DummyStream()

            def terminate(self):
                pass

        # Create a dummy Stream class
        class DummyStream:
            def __init__(self):
                self.closed = False

            def write(self, audio_data):
                # Just consume the data without playing it
                pass

            def stop_stream(self):
                pass

            def close(self):
                self.closed = True

            def is_stopped(self):
                return True

        return DummyPyAudio()

    @abstractmethod
    def _get_voices(self) -> list[dict[str, Any]]:
        """Retrieve a list of available voices from the TTS service.

        This is an internal method that should be implemented by each engine.
        It should return a list of dictionaries with at least the following keys:
        - id: The unique identifier for the voice
        - name: The display name of the voice
        - language_codes: A list of language codes supported by the voice
        - gender: The gender of the voice (if available)
        """

    def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """Retrieve a list of available voices from the TTS service with normalized language codes.

        Args:
            langcodes: Format of language codes to return. Options:
                - "bcp47": BCP-47 format (e.g., "en-US", "fr-FR")
                - "iso639_3": ISO 639-3 format (e.g., "eng", "fra")
                - "display": Human-readable display names
                  (e.g., "English (United States)", "French (France)")
                - "all": Return all formats as a dictionary

        Returns:
            List of voice dictionaries with standardized language information
        """
        from .language_utils import LanguageNormalizer

        # Get the raw voices from the engine-specific implementation
        raw_voices = self._get_voices()
        standardized_voices = []

        for voice in raw_voices:
            # Process each language code for this voice
            normalized_lang_codes = []
            normalized_lang_codes_dict = {}

            for lang_code in voice["language_codes"]:
                # Normalize the language code
                normalized_lang = LanguageNormalizer.normalize(lang_code)

                # Store based on requested format
                if langcodes.lower() == "bcp47":
                    normalized_lang_codes.append(normalized_lang.bcp47)
                elif langcodes.lower() == "iso639_3":
                    normalized_lang_codes.append(normalized_lang.iso639_3)
                elif langcodes.lower() == "display":
                    normalized_lang_codes.append(normalized_lang.display_name)
                elif langcodes.lower() == "all":
                    normalized_lang_codes_dict[lang_code] = {
                        "bcp47": normalized_lang.bcp47,
                        "iso639_3": normalized_lang.iso639_3,
                        "display": normalized_lang.display_name,
                    }
                else:
                    # Default to BCP-47 if invalid format is specified
                    normalized_lang_codes.append(normalized_lang.bcp47)

            # Create the voice data dictionary
            voice_data = voice.copy()  # Copy all original fields

            # Update the language_codes field with normalized codes
            if langcodes.lower() == "all":
                voice_data["language_codes"] = normalized_lang_codes_dict
            else:
                voice_data["language_codes"] = normalized_lang_codes

            standardized_voices.append(voice_data)

        return standardized_voices

    def check_credentials(self) -> bool:
        """
        Verify that the provided credentials are valid by calling _get_voices.

        This method should be implemented by the child classes to handle the
          specific credential checks.
        Also try not to use _get_voices. It can be wasteful in credits/bandwidth.
        """
        try:
            voices = self._get_voices()
            return bool(voices)
        except (ConnectionError, ValueError):
            return False

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """
        Set the voice for the TTS engine.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to be used for synthesis.

        lang : str | None, optional
            The language code for the voice to be used for synthesis.
            Defaults to None, which will use "en-US".
        """
        self.voice_id = voice_id
        self.lang = lang or "en-US"

    def _convert_mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 data to raw PCM data.

        :param mp3_data: MP3 audio data as bytes.
        :return: Raw PCM data as bytes (int16).
        """
        from soundfile import read

        # Use soundfile to read MP3 data
        mp3_fp = BytesIO(mp3_data)
        pcm_data, _ = read(mp3_fp, dtype="int16", always_2d=False)
        return pcm_data.tobytes()

    def _strip_wav_header(self, wav_data: bytes) -> bytes:
        """
        Strip the WAV header from the audio data to return raw PCM.

        WAV headers are typically 44 bytes,
        so we slice the data after the header.
        """
        return wav_data[44:]

    def _infer_channels_from_pcm(self, pcm_data: np.ndarray) -> int:
        """
        Infer the number of channels from the PCM data.

        :param pcm_data: PCM data as a numpy array.
        :return: Number of channels (1 for mono, 2 for stereo).
        """
        if pcm_data.ndim == 1:
            return 1  # Mono audio
        if pcm_data.ndim == STEREO_CHANNELS:
            return pcm_data.shape[1]  # Stereo or multi-channel
        msg = "Unsupported PCM data format"
        raise ValueError(msg)

    def _convert_audio(
        self,
        pcm_data: np.ndarray,
        target_format: str,
        sample_rate: int,
    ) -> bytes:
        """
        Convert raw PCM data to a specified audio format.

        :param pcm_data: Raw PCM audio data (assumed to be in int16 format).
        :param target_format: Target format (e.g., 'mp3', 'flac').
        :param sample_rate: Sample rate of the audio data.
        :return: Converted audio data as bytes.
        """
        # Set default format if target_format is None
        if target_format is None:
            target_format = "wav"
        if target_format not in ["mp3", "flac", "wav"]:
            msg = f"Unsupported format: {target_format}"
            raise ValueError(msg)

        # Create an in-memory file object
        output = BytesIO()
        if target_format in ("flac", "wav"):
            from soundfile import write as sf_write

            sf_write(
                output,
                pcm_data,
                samplerate=sample_rate,
                format=target_format.upper(),
            )
            output.seek(0)
            return output.read()
        if target_format == "mp3":
            # Infer number of channels from the shape of the PCM data
            import mp3

            nchannels = self._infer_channels_from_pcm(pcm_data)
            # Ensure sample size is 16-bit PCM
            sample_size = pcm_data.dtype.itemsize
            if sample_size != SIXTEEN_BIT_PCM_SIZE:
                msg = "Only PCM 16-bit sample size is supported"
                raise ValueError(msg)

            pcm_bytes = pcm_data.tobytes()

            # Create an in-memory file object for MP3 output
            output = BytesIO()

            # Initialize the MP3 encoder
            encoder = mp3.Encoder(output)
            encoder.set_bit_rate(64)  # Example bit rate in kbps
            encoder.set_sample_rate(sample_rate)
            encoder.set_channels(nchannels)
            encoder.set_quality(5)  # Adjust quality: 2 = highest, 7 = fastest

            # Write PCM data in chunks
            chunk_size = 8000 * nchannels * sample_size
            for i in range(0, len(pcm_bytes), chunk_size):
                encoder.write(pcm_bytes[i : i + chunk_size])

            # Finalize the MP3 encoding
            encoder.flush()

            # Return the MP3-encoded data
            output.seek(0)
            return output.read()
        msg = f"Unsupported format: {target_format}"
        raise ValueError(msg)

    @abstractmethod
    def synth_to_bytes(self, text: str | SSML, voice_id: str | None = None) -> bytes:
        """
        Transform written text to audio bytes on supported formats.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize, can be plain text or SSML.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.

        Returns
        -------
        bytes
            Raw PCM data with no headers for sounddevice playback.
        """

    def load_audio(self, audio_bytes: bytes) -> None:
        """
        Load audio bytes into the player.

        Parameters
        ----------
        audio_bytes : bytes
            The raw audio data to be loaded into the player.
            Must be PCM data in int16 format.
        """
        if not audio_bytes:
            msg = "Audio bytes cannot be empty"
            raise ValueError(msg)

        # Check if we're running in a CI environment or if SKIP_AUDIO_PLAYBACK is set
        in_ci = (
            self._is_ci_environment() or os.environ.get("SKIP_AUDIO_PLAYBACK") == "1"
        )

        if in_ci:
            # Use a dummy PyAudio implementation in CI environments
            logging.info(
                "Running in CI environment or SKIP_AUDIO_PLAYBACK is set, using dummy audio output"
            )
            self.pyaudio = self._get_dummy_pyaudio()
        else:
            # Use real PyAudio in normal environments
            try:
                import pyaudio

                self.pyaudio = pyaudio.PyAudio()
            except Exception as e:
                logging.warning(
                    "Failed to initialize PyAudio: %s. Using dummy audio output.", e
                )
                self.pyaudio = self._get_dummy_pyaudio()

        # Convert to numpy array for internal processing
        self._audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        self.audio_bytes = audio_bytes
        self.position = 0

    def _create_stream(self) -> None:
        """Create a new audio stream."""
        logging.debug("_create_stream called")
        if self.stream_pyaudio is not None and not self.stream_pyaudio.is_stopped():
            logging.debug("Stopping and closing existing stream")
            self.stream_pyaudio.stop_stream()
            self.stream_pyaudio.close()

        self.isplaying = True
        try:
            logging.debug(
                "Opening new audio stream with rate=%s, channels=%s",
                self.audio_rate,
                self.channels,
            )
            self.stream_pyaudio = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(self.sample_width),
                channels=self.channels,
                rate=self.audio_rate,
                output=True,
            )
            logging.debug("Audio stream created successfully")
        except Exception as e:
            logging.exception("Failed to create stream: %s", e)
            self.isplaying = False
            raise

    def _playback_loop(self) -> None:
        """Run main playback loop in a separate thread."""
        logging.debug("_playback_loop started")
        try:
            logging.debug("Creating audio stream")
            self._create_stream()
            logging.debug("Audio stream created")
            self._trigger_callback(
                "onStart"
            )  # Trigger onStart when playback actually starts
            self._on_end_triggered = (
                False  # Reset the guard flag at the start of playback
            )

            logging.debug(
                "Starting playback loop with audio_bytes size: %s",
                len(self.audio_bytes),
            )
            logging.debug("isplaying: %s, paused: %s", self.isplaying, self.paused)

            while self.isplaying and self.position < len(self.audio_bytes):
                if not self.paused:
                    chunk = self.audio_bytes[
                        self.position : self.position + self.chunk_size
                    ]
                    if chunk:
                        logging.debug(
                            "Writing chunk of size %s at position %s",
                            len(chunk),
                            self.position,
                        )
                        self.stream_pyaudio.write(chunk)
                        self.position += len(chunk)
                    else:
                        logging.debug("Empty chunk, breaking loop")
                        break
                else:
                    logging.debug("Paused, sleeping")
                    time.sleep(0.1)  # Reduce CPU usage while paused

            # Trigger "onEnd" only once when playback ends
            if not self._on_end_triggered:
                if self.position >= len(self.audio_bytes):
                    self._trigger_callback("onEnd")
                    self._on_end_triggered = True
                self.playing.clear()

            # Cleanup after playback ends
            if self.stream_pyaudio and not self.stream_pyaudio.is_stopped():
                self.stream_pyaudio.stop_stream()
                self.stream_pyaudio.close()
                self.stream_pyaudio = None

            # Clean up PyAudio instance
            if self.pyaudio:
                self.pyaudio.terminate()
                self.pyaudio = None

            self.isplaying = False
        except OSError:
            # Handle stream-related exceptions gracefully
            self.isplaying = False

    def _auto_resume(self) -> None:
        """Resume audio after timed pause."""
        self.paused = False
        logging.info("Resuming playback after pause")

    def play(self, duration: float | None = None) -> None:
        """Start or resume playback."""
        logging.debug("play() called with duration=%s", duration)
        if self.audio_bytes is None:
            msg = "No audio loaded"
            logging.error("No audio loaded")
            raise ValueError(msg)

        logging.debug("Audio bytes size: %s", len(self.audio_bytes))
        logging.debug("isplaying: %s, paused: %s", self.isplaying, self.paused)

        if not self.isplaying:
            logging.debug("Starting new playback")
            self.isplaying = True
            self.paused = False
            self.position = 0
            self._on_end_triggered = (
                False  # Reset the guard flag at the start of playback
            )
            self.playback_thread = threading.Thread(target=self._playback_loop)
            self.playback_thread.daemon = (
                True  # Make thread daemon so it doesn't block program exit
            )
            logging.debug("Starting playback thread")
            self.playback_thread.start()
            logging.debug("Playback thread started")
            time.sleep(float(duration or 0))
        elif self.paused:
            logging.debug("Resuming from paused state")
            self.paused = False

    def pause(self, duration: float | None = None) -> None:
        """
        Pause playback with optional duration.

        Parameters
        ----------
        duration: (Optional[float])
            Number of seconds to pause. If None, pause indefinitely

        """
        self.paused = True

        # Cancel any existing pause timer
        if self.pause_timer:
            self.pause_timer.cancel()
            self.pause_timer = None

        # If duration specified, create timer for auto-resume
        if duration is not None:
            self.pause_timer = threading.Timer(duration, self._auto_resume)
            self.pause_timer.start()
            time.sleep(float(duration or 0))

    def resume(self) -> None:
        """Resume playback."""
        if self.isplaying:
            # Cancel any existing pause timer
            if self.pause_timer:
                self.pause_timer.cancel()
                self.pause_timer = None
            self.paused = False

    def stop(self) -> None:
        """Stop playback."""
        self.isplaying = False
        self.paused = False
        if self.pause_timer:
            self.pause_timer.cancel()
            self.pause_timer = None

        # Stop and close the stream if it exists
        if self.stream_pyaudio:
            try:
                if not self.stream_pyaudio.is_stopped():
                    self.stream_pyaudio.stop_stream()
                self.stream_pyaudio.close()
            except OSError as e:
                logging.info("Stream already closed or encountered an error: %s", e)

            self.stream_pyaudio = None

        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
        self.position = 0

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.stop()

            if self.pyaudio:
                self.pyaudio.terminate()
        except OSError as e:
            logging.warning("Error during cleanup: %s", e)

    def synth_to_file(
        self,
        text: str | SSML,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """
        Synthesizes text to audio and saves it to a file.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize.
        output_file : str | Path
            The path to save the audio file to.
        output_format : str
            The format to save the audio file as. Default is "wav".
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        """
        # Convert text to audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Convert to the desired format if needed
        if output_format != "raw":
            # Convert the raw PCM data to the target format
            audio_bytes = self._convert_pcm_to_format(
                np.frombuffer(audio_bytes, dtype=np.int16),
                output_format,
                self.audio_rate,
                self.channels,
            )

        # Save to file
        if isinstance(output_file, str):
            output_file = Path(output_file)

        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("wb") as f:
            f.write(audio_bytes)

    def speak(
        self,
        text: str | SSML,
        voice_id: str | None = None,
        wait_for_completion: bool = True,
        return_bytes: bool = False,
    ) -> bytes | None:
        """
        Synthesize text and play it back using sounddevice.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        wait_for_completion : bool, optional
            Whether to wait for playback to complete before returning. Default is True.
        return_bytes : bool, optional
            Whether to return the audio bytes. Default is False.

        Returns
        -------
        bytes | None
            Raw PCM audio bytes if return_bytes=True, otherwise None.
        """
        logging.debug("speak() called with wait_for_completion=%s, return_bytes=%s", wait_for_completion, return_bytes)
        # Convert text to audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Load the audio into the player and play it
        self.load_audio(audio_bytes)
        self.play()

        # Wait for playback to complete if requested
        if wait_for_completion and self.playback_thread:
            logging.debug("Waiting for playback to complete")
            self.playback_thread.join()
            logging.debug("Playback completed")

        # Return bytes if requested
        return audio_bytes if return_bytes else None

    def synth(
        self,
        text: str | SSML,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
        format: str | None = None,  # Added for compatibility
    ) -> None:
        """
        Alias for synth_to_file for backward compatibility.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize.
        output_file : str | Path
            The path to save the audio file to.
        output_format : str
            The format to save the audio file as. Default is "wav".
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        format : str | None, optional
            Alias for output_format for compatibility with older code.
        """
        # Use format parameter if provided (for compatibility)
        if format is not None:
            output_format = format

        self.synth_to_file(text, output_file, output_format, voice_id)

    def _process_streaming_synthesis(
        self, text: str | SSML, voice_id: str | None, trigger_callbacks: bool
    ) -> bytes:
        """Process streaming synthesis for engines that support it."""
        # Trigger onStart callback if requested
        if trigger_callbacks:
            self._trigger_callback("onStart")

        # Get streaming generator
        generator = self.synth_to_bytestream(text, voice_id)

        # Collect all chunks for audio playback
        audio_chunks = []
        for chunk in generator:
            # Check if we should stop playback
            if hasattr(self, "stop_flag") and self.stop_flag.is_set():
                break
            audio_chunks.append(chunk)

        # Combine all chunks into a single audio buffer
        audio_data = b"".join(audio_chunks)

        # For streaming engines, get word timings if available
        if hasattr(self, "get_word_timings") and callable(self.get_word_timings):
            word_timings = self.get_word_timings()
            if word_timings:
                self.set_timings(word_timings)

        # Play the audio (similar to _process_non_streaming_synthesis)
        self.load_audio(audio_data)
        self.play()

        # Trigger onEnd callback after all chunks are processed if requested
        if trigger_callbacks:
            self._trigger_callback("onEnd")

        return audio_data

    def _process_non_streaming_synthesis(
        self, text: str | SSML, voice_id: str | None, trigger_callbacks: bool
    ) -> bytes:
        """Process non-streaming synthesis for engines that don't support streaming."""
        # Trigger onStart callback if requested
        if trigger_callbacks:
            self._trigger_callback("onStart")

        # Fall back to non-streaming synthesis
        audio_data = self.synth_to_bytes(text, voice_id)

        # For non-streaming engines, create simple word timings
        self._create_estimated_word_timings(text)

        # Play the audio
        self.load_audio(audio_data)
        self.play()

        return audio_data

    def _create_estimated_word_timings(self, text: str | SSML) -> None:
        """Create estimated word timings for non-streaming engines."""
        # Extract plain text from SSML if needed
        plain_text = (
            re.sub(r"<[^>]+>", "", str(text)) if self._is_ssml(str(text)) else str(text)
        )

        words = plain_text.split()
        if not words:
            return

        # Calculate approximate duration
        duration = self.get_audio_duration()
        word_duration = duration / len(words)

        # Create simple evenly-spaced word timings
        word_timings = []
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration if i < len(words) - 1 else duration
            word_timings.append((start_time, end_time, word))
        self.set_timings(word_timings)

    def synthesize(
        self,
        text: str | SSML,
        voice_id: str | None = None,
        streaming: bool = False,
    ) -> bytes | Generator[bytes, None, None]:
        """
        Synthesize text to audio data without playback.

        This method provides silent audio synthesis, perfect for SAPI bridges,
        audio processing pipelines, and applications that need audio data
        without immediate playback.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        streaming : bool, optional
            Controls data delivery method:
            - False (default): Return complete audio data as bytes
            - True: Return generator yielding audio chunks in real-time

        Returns
        -------
        bytes | Generator[bytes, None, None]
            - bytes: When streaming=False, complete audio data
            - Generator[bytes, None, None]: When streaming=True, audio chunks as they're generated

        Examples
        --------
        Complete audio data (perfect for SAPI bridges):
        >>> audio_bytes = tts.synthesize("Hello world", streaming=False)
        >>> # Returns complete WAV data, no audio playback

        Real-time streaming (perfect for live processing):
        >>> for chunk in tts.synthesize("Hello world", streaming=True):
        ...     process_audio_chunk(chunk)  # Process each chunk as generated
        """
        try:
            if streaming:
                # Return streaming generator
                if hasattr(self, "synth_to_bytestream") and callable(
                    self.synth_to_bytestream
                ):
                    return self._synthesize_streaming(text, voice_id)
                # For non-streaming engines, fall back to complete data
                return self._synthesize_complete(text, voice_id)
            # Return complete audio data
            return self._synthesize_complete(text, voice_id)
        except Exception:
            logging.exception("Error in synthesis")
            raise

    def _synthesize_streaming(
        self, text: str | SSML, voice_id: str | None
    ) -> Generator[bytes, None, None]:
        """Generate streaming audio chunks without playback."""
        if hasattr(self, "synth_to_bytestream") and callable(self.synth_to_bytestream):
            # True streaming for engines that support it
            generator = self.synth_to_bytestream(text, voice_id)

            # Set word timings if available
            if hasattr(self, "get_word_timings") and callable(self.get_word_timings):
                word_timings = self.get_word_timings()
                if word_timings:
                    self.set_timings(word_timings)

            # Yield chunks as they're generated
            for chunk in generator:
                if hasattr(self, "stop_flag") and self.stop_flag.is_set():
                    break
                yield chunk
        else:
            # Pretend to stream for engines that don't support true streaming
            # Get complete audio data and chunk it
            audio_data = self.synth_to_bytes(text, voice_id)

            # Set word timings
            self._create_estimated_word_timings(text)

            # Chunk the audio data to simulate streaming
            chunk_size = 4096  # 4KB chunks
            for i in range(0, len(audio_data), chunk_size):
                if hasattr(self, "stop_flag") and self.stop_flag.is_set():
                    break
                chunk = audio_data[i : i + chunk_size]
                if chunk:  # Only yield non-empty chunks
                    yield chunk

    def _synthesize_complete(self, text: str | SSML, voice_id: str | None) -> bytes:
        """Generate complete audio data without playback."""
        audio_data = self.synth_to_bytes(text, voice_id)

        # Create estimated word timings for non-streaming engines
        self._create_estimated_word_timings(text)

        return audio_data

    def speak_streamed(
        self,
        text: str | SSML,
        voice_id: str | None = None,
        trigger_callbacks: bool = True,
        save_to_file_path: str | None = None,
        audio_format: str = "wav",
        wait_for_completion: bool = True,
        return_bytes: bool = False,
    ) -> bytes | None:
        """
        Synthesize text to speech and stream it for playback.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize and stream.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        trigger_callbacks : bool, optional
            Whether to trigger onStart and onEnd callbacks. Default is True.
        save_to_file_path : str | None, optional
            Optional path to save the audio to a file while streaming.
        audio_format : str, optional
            Audio format for file saving. Default is "wav".
        wait_for_completion : bool, optional
            Whether to wait for playback to complete before returning. Default is True.
        return_bytes : bool, optional
            Whether to return the audio bytes. Default is False.

        Returns
        -------
        bytes | None
            Raw PCM audio bytes if return_bytes=True, otherwise None.
        """
        try:
            # Check if the engine supports streaming via synth_to_bytestream
            if hasattr(self, "synth_to_bytestream") and callable(
                self.synth_to_bytestream
            ):
                audio_data = self._process_streaming_synthesis(
                    text, voice_id, trigger_callbacks
                )
            else:
                audio_data = self._process_non_streaming_synthesis(
                    text, voice_id, trigger_callbacks
                )

            # Save to file if requested
            if save_to_file_path and audio_data:
                # Convert raw PCM data to the specified format before saving
                if audio_format.lower() != "raw":
                    # Convert bytes to numpy array for format conversion
                    pcm_array = np.frombuffer(audio_data, dtype=np.int16)
                    # Use the existing format conversion method
                    formatted_audio = self._convert_pcm_to_format(
                        pcm_array, audio_format, self.audio_rate, self.channels
                    )
                    with open(save_to_file_path, "wb") as f:
                        f.write(formatted_audio)
                else:
                    # Save raw PCM data as-is
                    with open(save_to_file_path, "wb") as f:
                        f.write(audio_data)
                logging.debug(
                    f"Audio saved to {save_to_file_path} in {audio_format} format"
                )

            # Wait for playback to complete if requested
            if wait_for_completion and self.playback_thread:
                logging.debug("Waiting for playback to complete")
                self.playback_thread.join()
                logging.debug("Playback completed")

            # Return bytes if requested
            return audio_data if return_bytes else None

        except Exception:
            logging.exception("Error in streaming synthesis")
            return None

    def setup_stream(
        self, samplerate: int = 44100, channels: int = 1, dtype: str | int = "int16"
    ) -> None:
        """
        Set up the audio stream for playback.

        Parameters
        ----------
        samplerate : int
            The sample rate for the audio stream. Defaults to 22050.
        channels : int
            The number of audio channels. Defaults to 1.
        dtype : Union[str, int]
            The data type for audio samples. Defaults to "int16".

        """
        try:
            if self.stream is not None:
                self.stream.close()
            self.stream = sd.OutputStream(
                samplerate=samplerate,
                channels=channels,
                dtype=dtype,
                callback=self.callback,
            )
            self.stream.start()
        except Exception:
            logging.exception("Failed to set up audio stream")
            raise

    def callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time: sd.CallbackTime,
        status: sd.CallbackFlags,
    ) -> None:
        """Handle streamed audio playback as a callback."""
        if status:
            logging.warning("Sounddevice status: %s", status)
        if self.playing:
            # Each frame is 2 bytes for int16, so frames * 2 gives the number of bytes
            end_position = self.position + frames * 2
            data = self.audio_bytes[self.position : end_position]
            if len(data) < frames * 2:
                # Not enough data to fill outdata, zero-pad it
                outdata.fill(0)
                outdata[: len(data) // 2] = np.frombuffer(data, dtype="int16").reshape(
                    -1, 1
                )
            else:
                outdata[:] = np.frombuffer(data, dtype="int16").reshape(outdata.shape)
            self.position = end_position

            if self.position >= len(self.audio_bytes):
                self._trigger_callback("onEnd")
                self.playing.clear()
        else:
            outdata.fill(0)

    def _start_stream(self) -> None:
        """Start the audio stream."""
        with self.stream_lock:
            if self.stream:
                self.stream.start()
            while self.stream.active and self.playing.is_set():
                time.sleep(0.1)
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

    def set_timings(
        self, timings: list[tuple[float, str] | tuple[float, float, str]]
    ) -> None:
        """
        Set the word timings for the synthesized speech.

        Parameters
        ----------
        timings : list[tuple[float, str] | tuple[float, float, str]]
            A list of tuples containing word timings.
            Each tuple can be either (start_time, word) or (start_time, end_time, word).
        """
        logging.debug("Setting timings: %s", timings)
        self.timings = []
        if not timings:
            logging.debug("No timings provided, returning empty list")
            return

        # Calculate total duration for estimating end times if needed
        total_duration = 0
        for timing in timings:
            if len(timing) > 2:  # If we have (start, end, word)
                # Unpack only what we need
                end_time = timing[1]
                total_duration = max(total_duration, end_time)

        # If we don't have end times, estimate the total duration
        if total_duration == 0 and timings:
            # Estimate based on the last start time plus a small buffer
            total_duration = timings[-1][0] + 0.5
            logging.debug("Estimated total duration: %s", total_duration)

        # Process the timings
        for i, timing in enumerate(timings):
            if len(timing) == TIMING_TUPLE_LENGTH_TWO:
                start_time, word = timing
                # Use ternary operator for cleaner code
                end_time = timings[i + 1][0] if i < len(timings) - 1 else total_duration
                self.timings.append((start_time, end_time, word))
                logging.debug("Processed 2-tuple timing: %s", timing)
                logging.debug("Converted to: (%s, %s, %s)", start_time, end_time, word)
            else:
                self.timings.append(timing)
                logging.debug("Added 3-tuple timing: %s", timing)

        logging.debug("Final timings: %s", self.timings)

    def get_timings(self) -> list[tuple[float, float, str]]:
        """Retrieve the word timings for the spoken text."""
        return self.timings

    def get_audio_duration(self) -> float:
        """
        Calculate the duration of the audio.

        Calculate the duration of the audio based
        on the number of samples and sample rate.
        """
        if self.timings:
            return self.timings[-1][1]
        return 0.0

    def on_word_callback(self, word: str, start_time: float, end_time: float) -> None:
        """
        Trigger a callback when a word is spoken during playback.

        :param word: The word being spoken.
        :param start_time: The start time of the word in seconds.
        :param end_time: The end time of the word in seconds.
        """
        logging.info(
            "Word spoken: %s, Start: %.3fs, End: %.3fs",
            word,
            start_time,
            end_time,
        )

    def connect(self, event_name: str, callback: Callable) -> None:
        """Connect a callback function to an event."""
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback

    def _trigger_callback(self, event_name: str, *args: tuple[Any, ...]) -> None:
        """Trigger the specified callback event with optional arguments."""
        if event_name in self.callbacks and self.callbacks[event_name] is not None:
            self.callbacks[event_name](*args)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """
        Start playback of the given text with callbacks triggered at each word.

        Parameters
        ----------
        text : str
            The text to be spoken.
        callback : Callable, optional
            A callback function to invoke at each word
            with arguments (word, start, end).
            If None, `self.on_word_callback` is used.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        """
        if callback is None:
            callback = self.on_word_callback

        # Call speak_streamed with trigger_callbacks=False to avoid duplicate callbacks
        # and wait_for_completion=False so we can set up word timing callbacks while audio plays
        self.speak_streamed(
            text, voice_id, trigger_callbacks=False, wait_for_completion=False
        )
        start_time = time.time()

        try:
            for start, end, word in self.timings:
                delay = max(0, start - (time.time() - start_time))
                timer = threading.Timer(delay, callback, args=(word, start, end))
                timer.start()
                self.timers.append(timer)
        except (ValueError, TypeError):
            logging.exception("Error in start_playback_with_callbacks")

    def finish(self) -> None:
        """Clean up resources and stop the audio stream."""
        try:
            with self.stream_lock:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
        except Exception:
            logging.exception("Failed to clean up audio resources")
        finally:
            self.stream = None

    def __del__(self) -> None:
        """Clean up resources when the object is deleted."""
        self.finish()

    def get_property(self, property_name: str) -> PropertyType:
        """
        Retrieve the value of a specified property for the TTS engine.

        Parameters
        ----------
        property_name : str
            The name of the property to retrieve.
            Expected values may include "rate", "volume", or "pitch".

        Returns
        -------
        Optional[Any]
            The value of the specified property if it exists; otherwise, returns None.

        """
        return self.properties.get(property_name, None)

    def set_property(self, property_name: str, value: float | str) -> None:
        """
        Set a property for the TTS engine and update its internal state.

        Parameters
        ----------
        property_name : str
            The name of the property to set.
            Expected values are "rate", "volume", or "pitch".
        value : float | str
            The value to assign to the specified property.

        Updates the corresponding internal variable (_rate, _volume, or _pitch)
        based on the property name.

        """
        self.properties[property_name] = value

        if property_name == "rate":
            self._rate = value
        elif property_name == "volume":
            self._volume = value
        elif property_name == "pitch":
            self._pitch = value

    def _is_ssml(self, text: str) -> bool:
        return bool(re.match(r"^\s*<speak>", text, re.IGNORECASE))

    def _convert_to_ssml(self, text: str) -> str:
        """Convert plain text to simple SSML."""
        ssml_parts = [
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">'
        ]
        words = text.split()
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="word{i}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)

    def set_output_device(self, device_id: int) -> None:
        """
        Set the default output sound device by its ID.

        :param device_id: The ID of the device to be set as the default output.
        """
        try:
            # Validate the device_id
            if device_id not in [device["index"] for device in sd.query_devices()]:
                msg = f"Invalid device ID: {device_id}"
                raise ValueError(msg)

            sd.default.device = device_id
            logging.info("Output device set to %s", sd.query_devices(device_id)["name"])
        except ValueError:
            logging.exception("Invalid device ID")
        except Exception:
            logging.exception("Failed to set output device")

    def _convert_pcm_to_format(
        self,
        pcm_data: np.ndarray,
        output_format: str,
        samplerate: int,
        channels: int = 1,
    ) -> bytes:
        """
        Convert PCM data to the specified audio format.

        Parameters
        ----------
        pcm_data : np.ndarray
            The PCM audio data to convert.
        output_format : str
            The target audio format (e.g., 'wav', 'mp3', etc.)
        samplerate : int
            The sample rate of the audio data.
        channels : int, optional
            The number of audio channels. Default is 1.

        Returns
        -------
        bytes
            The converted audio data in the specified format.
        """

        # Create a BytesIO object to hold the output
        output_buffer = io.BytesIO()

        # Convert to the desired format
        if output_format.lower() == "wav":
            sf.write(output_buffer, pcm_data, samplerate, format="WAV")
        elif output_format.lower() == "mp3":
            try:
                import mp3

                # Convert numpy array to bytes (16-bit PCM)
                pcm_bytes = pcm_data.astype(np.int16).tobytes()

                # Create a BytesIO object for the MP3 data
                mp3_buffer = io.BytesIO()

                # Create an MP3 encoder
                encoder = mp3.Encoder(mp3_buffer)
                encoder.set_bit_rate(128)  # 128 kbps is a good default
                encoder.set_sample_rate(samplerate)
                encoder.set_channels(channels)
                encoder.set_quality(5)  # 2-highest, 7-fastest
                encoder.set_mode(
                    mp3.MODE_STEREO if channels == 2 else mp3.MODE_SINGLE_CHANNEL
                )

                # Write PCM data to the encoder
                encoder.write(pcm_bytes)

                # Flush the encoder to ensure all data is written
                encoder.flush()

                # Get the MP3 data
                mp3_buffer.seek(0)
                output_buffer.write(mp3_buffer.read())
                output_buffer.seek(0)

            except ImportError:
                logging.error(
                    "pymp3 is required for MP3 conversion. Please install it with pip install pymp3"
                )
                raise
        elif output_format.lower() == "ogg":
            sf.write(output_buffer, pcm_data, samplerate, format="OGG")
        elif output_format.lower() == "flac":
            sf.write(output_buffer, pcm_data, samplerate, format="FLAC")
        else:
            # Default to WAV if format not recognized
            logging.warning("Unsupported format: %s. Using WAV instead.", output_format)
            sf.write(output_buffer, pcm_data, samplerate, format="WAV")

        # Get the bytes from the buffer
        output_buffer.seek(0)
        return output_buffer.read()
