"""
Provides an abstract text-to-speech (TTS) class.

with methods for synthesis, playback, and property management.
Designed to be extended by specific TTS engine implementations.
"""

from __future__ import annotations

# Standard Library Imports
import logging
import re
import threading
import time
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from threading import Event
from typing import Any, Callable, NoReturn, Union

# Third-Party Imports
import numpy as np  # type: ignore[attr-defined]
import sounddevice as sd  # type: ignore[attr-defined]

# Local Imports
from .ssml import AbstractSSMLNode

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
    Abstract class (ABC) for text-to-speech functionalities,.

    including synthesis and playback.
    """

    def __init__(self) -> None:
        """Initialize the TTS engine with default values."""
        self.voice_id = None
        self.stream = None
        self.audio_rate = 44100
        self.audio_bytes = None
        self.playing = Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []
        self.properties = {"volume": "", "rate": "", "pitch": ""}
        self.callbacks = {"onStart": None, "onEnd": None, "started-word": None}
        self.stream_lock = threading.Lock()

        # addition for pause resume
        #self.sample_rate is audio_rate
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

    @abstractmethod
    def get_voices(self) -> list[dict[str, Any]]:
        """Retrieve a list of available voices from the TTS service."""

    def check_credentials(self) -> bool:
        """
        Verify that the provided credentials are valid by calling get_voices.

        This method should be implemented by the child classes to handle the
          specific credential checks.
        Also try not to use get_voices. It can be wasteful in credits/bandwidth.
        """
        try:
            voices = self.get_voices()
            return bool(voices)
        except (ConnectionError, ValueError):
            return False

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """
        Set the voice for the TTS engine.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to be used for synthesis.

        lang : str
            The language code for the voice to be used for synthesis.

        """
        self.voice_id = voice_id
        self.lang = lang

    def _convert_mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 data to raw PCM data.

        :param mp3_data: MP3 audio data as bytes.
        :return: Raw PCM data as bytes (int16).
        """
        from soundfile import read  # type: ignore[attr-defined]

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
        self, pcm_data: np.ndarray, target_format: str, sample_rate: int,
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
            from soundfile import write as sf_write  # type: ignore[attr-defined]
            sf_write(
                output, pcm_data, samplerate=sample_rate, format=target_format.upper(),
            )
            output.seek(0)
            return output.read()
        if target_format == "mp3":
            # Infer number of channels from the shape of the PCM data
            import mp3  # type: ignore[attr-defined]

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
    def synth_to_bytes(self, text: str | SSML) -> bytes:
        """
        Transform written text to audio bytes on supported formats.

        This method should return raw PCM data with
          no headers for sounddevice playback.
        """

    def load_audio(self, audio_bytes: bytes) -> None:
        """
        Load audio bytes into the player.

        Parameters
        ----------
        audio_bytes : bytes
            The audio data to be loaded into the player.

        """
        import pyaudio
        self.pyaudio = pyaudio.PyAudio()
        if not audio_bytes:
            msg = "Audio bytes cannot be empty"
            raise ValueError(msg)
        self.audio_bytes = audio_bytes
        self.position = 0

    def _create_stream(self) -> None:
        """Create a new audio stream."""
        if self.stream_pyaudio is not None and not self.stream_pyaudio.is_stopped():
            self.stream_pyaudio.stop_stream()
            self.stream_pyaudio.close()

        self.isplaying = True
        try:
            self.stream_pyaudio = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(self.sample_width),
                channels=self.channels,
                rate=self.audio_rate,
                output=True,
            )
        except Exception:
            logging.exception("Failed to create stream")
            self.isplaying = False
            raise

    def _playback_loop(self) -> None:
        """Run main playback loop in a separate thread."""
        try:
            self._create_stream()
            self._on_end_triggered = False  # Reset the guard flag at the start of playback

            while self.isplaying and self.position < len(self.audio_bytes):
                if not self.paused:
                    chunk = self.audio_bytes[
                        self.position : self.position + self.chunk_size
                    ]
                    if chunk:
                        self.stream_pyaudio.write(chunk)
                        self.position += len(chunk)
                    else:
                        break
                else:
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
        if self.audio_bytes is None:
            msg = "No audio loaded"
            raise ValueError(msg)

        if not self.isplaying:
            self.isplaying = True
            self.paused = False
            self.position = 0
            self._on_end_triggered = False  # Reset the guard flag at the start of playback
            self.playback_thread = threading.Thread(target=self._playback_loop)
            self.playback_thread.start()
            time.sleep(float(duration or 0))
        elif self.paused:
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
            except OSError as e:  # Use specific exceptions if available
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
        except OSError as e:  # Specify more likely exceptions if possible
            logging.warning("Error during cleanup: %s", e)

    def synth_to_file(
        self, text: str | SSML, filename: str, audio_format: str | None = "wav",
    ) -> None:
        """
        Synthesizes text to audio and saves it to a file.

        :param text: The text to synthesize.
        :param filename: The file where the audio will be saved.
        :param format: The format to save the file in (e.g., 'wav', 'mp3').
        """
        # Ensure format is not None
        format_to_use = audio_format if audio_format is not None else "wav"
        audio_bytes = self.synth_to_bytes(text)  # Always request raw PCM data
        pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
        converted_audio = self._convert_audio(pcm_data, format_to_use, self.audio_rate)

        with Path(filename).open("wb") as file:
            file.write(converted_audio)

    def synth(self, text: str, filename: str, audio_format: str | None = "wav") -> None:
        """Alias for synth_to_file method."""
        self.synth_to_file(text, filename, audio_format)

    def speak(self, text: str | SSML) -> None:
        """
        Synthesize text and play it back using sounddevice.

        :param text: The text to synthesize and play.
        """
        try:
            audio_bytes = self.synth_to_bytes(text)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)

            logging.debug(f"Audio buffer size: {len(audio_bytes)} bytes")
            logging.debug(f"First 20 bytes of audio: {audio_bytes[:20]}")

            sd.play(audio_data, samplerate=self.audio_rate)
            sd.wait()
        except Exception:
            logging.exception("Error playing audio")

    def speak_streamed(
        self,
        text: str,
        save_to_file_path: str | None = None,
        audio_format: str | None = "wav",
    ) -> None:
        """
        Synthesize text and stream it for playback using sounddevice.

        Optionally save the audio to a file after playback completes.

        :param text: The text to synthesize and stream.
        :param save_to_file_path: Path to save the audio file (optional).
        :param audio_format: Audio format to save (e.g., 'wav', 'mp3', 'flac').
        """
        try:
            # Synthesize audio to bytes for playback
            audio_bytes = self.synth_to_bytes(text)
            if audio_bytes[:4] == b"RIFF":
                audio_bytes = self._strip_wav_header(audio_bytes)
                logging.info("Stripping wav header from streamed audio")
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            self.audio_bytes = audio_data.tobytes()
            self.position = 0
            self.playing.set()
            self._trigger_callback("onStart")

            # Setup the audio stream
            with self.stream_lock:
                if self.stream:
                    self.stream.close()
                self.setup_stream()

            # Start playback in a separate thread
            self.play_thread = threading.Thread(target=self._start_stream)
            self.play_thread.start()

            # Wait for the playback thread to complete
            self.play_thread.join()

            # After streaming is finished, save the file if requested
            if save_to_file_path:
                pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
                audio_format = audio_format if audio_format else "wav"
                converted_audio = self._convert_audio(
                    pcm_data, audio_format, self.audio_rate,
                )

                with Path(save_to_file_path).open("wb") as f:
                    f.write(converted_audio)
                logging.info(
                    "Audio saved to %s in %s format.",
                    save_to_file_path,
                    audio_format,
                )

        except Exception:
            logging.exception("Error streaming or saving audio")


    def setup_stream(self, samplerate: int = 22050,
                     channels: int = 1, dtype: str | int = "int16") -> None:
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
            self, outdata: np.ndarray, frames: int, time: sd.CallbackTime,  # noqa: ARG002
            status: sd.CallbackFlags) -> None:
        """Handle streamed audio playback as a callback."""
        if status:
            logging.warning("Sounddevice status: %s", status)
        if self.playing:
            # Each frame is 2 bytes for int16, so frames * 2 gives the number of bytes
            end_position = self.position + frames * 2
            data = self.audio_bytes[self.position: end_position]
            if len(data) < frames * 2:
                # Not enough data to fill outdata, zero-pad it
                outdata.fill(0)
                outdata[: len(data) // 2] = (
                            np.frombuffer(data, dtype="int16")
                            .reshape(-1, 1)
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

    def set_timings(self, timings: list[WordTiming]) -> None:
        """Set the word timings for the spoken text."""
        self.timings = []
        total_duration = self.get_audio_duration()

        for i, timing in enumerate(timings):
            if len(timing) == TIMING_TUPLE_LENGTH_TWO:
                start_time, word = timing
                if i < len(timings) - 1:
                    end_time = (
                        timings[i + 1][0]
                        if len(timings[i + 1]) == TIMING_TUPLE_LENGTH_TWO
                        else timings[i + 1][1]
                    )
                else:
                    end_time = total_duration
                self.timings.append((start_time, end_time, word))
            elif len(timing) == TIMING_TUPLE_LENGTH_THREE:
                self.timings.append(timing)
            else:
                msg = f"Invalid timing format: {timing}"
                raise ValueError(msg)

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
            "Word spoken: %s, Start: %.3fs, End: %.3fs", word, start_time, end_time,
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
            self, text: str, callback: Callable | None = None) -> None:
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

        """
        if callback is None:
            callback = self.on_word_callback

        self.speak_streamed(text)
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
        words = text.split()
        ssml_parts = ["<speak>"]
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="word{i}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)

    def set_output_device(self, device_id: int) -> None:
        """
        Set the default output sound device by its ID.

        :param device_id: The ID of the device to be set as the default output.
        """

        def raise_invalid_device_error(device_id: int) -> NoReturn:
            """Raise a ValueError with a message about the invalid device ID."""
            msg = f"Invalid device ID: {device_id}"
            raise ValueError(msg)

        try:
            # Validate the device_id
            if device_id not in [device["index"] for device in sd.query_devices()]:
                raise_invalid_device_error(device_id)

            sd.default.device = device_id
            logging.info("Output device set to %s", sd.query_devices(device_id)["name"])
        except ValueError:
            logging.exception("Invalid device ID")
        except Exception:
            logging.exception("Failed to set output device")

