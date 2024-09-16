from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union, Dict, Callable, Tuple
import sounddevice as sd  # type: ignore
import numpy as np  # type: ignore
import threading
from threading import Event
import logging
import time
import re
from io import BytesIO

FileFormat = Union[str, None]
WordTiming = Union[Tuple[float, str], Tuple[float, float, str]]


class AbstractTTS(ABC):
    """Abstract class (ABC) for text-to-speech functionalities,
    including synthesis and playback."""

    def __init__(self):
        self.voice_id = None
        self.stream = None
        self.audio_rate = 22050
        self.audio_bytes = None
        self.playing = Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []
        self.properties = {"volume": "", "rate": "", "pitch": ""}
        self.callbacks = {"onStart": None, "onEnd": None, "started-word": None}
        self.stream_lock = threading.Lock()

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def set_voice(self, voice_id: str, lang: str = "en-US"):
        self.voice_id = voice_id
        self.lang = lang

    def _convert_mp3_to_pcm(self, mp3_data: bytes) -> bytes:
        """
        Convert MP3 data to raw PCM data.
        :param mp3_data: MP3 audio data as bytes.
        :return: Raw PCM data as bytes (int16).
        """
        from soundfile import read  # type: ignore
        from io import BytesIO

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
        elif pcm_data.ndim == 2:
            return pcm_data.shape[1]  # Stereo or multi-channel
        else:
            raise ValueError("Unsupported PCM data format")

    def _convert_audio(
        self, pcm_data: np.ndarray, target_format: str, sample_rate: int
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
            raise ValueError(f"Unsupported format: {target_format}")
        from io import BytesIO

        # Create an in-memory file object
        output = BytesIO()
        if target_format == "flac" or target_format == "wav":
            from soundfile import write  # Lazy import

            write(
                output, pcm_data, samplerate=sample_rate, format=target_format.upper()
            )
            output.seek(0)
            return output.read()
        elif target_format == "mp3":
            # Infer number of channels from the shape of the PCM data
            import mp3  # type: ignore

            nchannels = self._infer_channels_from_pcm(pcm_data)
            # Ensure sample size is 16-bit PCM
            sample_size = pcm_data.dtype.itemsize
            if sample_size != 2:
                raise ValueError(
                    f"Only PCM 16-bit sample size is supported "
                    f"(input audio: {sample_size * 8}-bit)"
                )
            # Convert to bytes
            pcm_bytes = pcm_data.tobytes()

            # Create an in-memory file object for MP3 output
            output = BytesIO()

            # Initialize the MP3 encoder
            encoder = mp3.Encoder(output)
            encoder.set_bit_rate(64)  # Example bit rate in kbps
            encoder.set_sample_rate(sample_rate)
            encoder.set_channels(nchannels)
            encoder.set_quality(5)  # Adjust quality: 2 = highest, 7 = fastest
            # encoder.set_mod(mp3.MODE_STEREO if nchannels == 2 else mp3.MODE_SINGLE_CHANNEL)   # noqa: E501

            # Write PCM data in chunks
            chunk_size = 8000 * nchannels * sample_size
            for i in range(0, len(pcm_bytes), chunk_size):
                encoder.write(pcm_bytes[i : i + chunk_size])

            # Finalize the MP3 encoding
            encoder.flush()

            # Return the MP3-encoded data
            output.seek(0)
            return output.read()
        else:
            raise ValueError(f"Unsupported format: {target_format}")

    @abstractmethod
    def synth_to_bytes(self, text: Any) -> bytes:
        """
        Transforms written text to audio bytes on supported formats.
        This method should return raw PCM data with
          no headers for sounddevice playback.
        """
        pass

    def synth_to_bytestream(self, text: Any, format: Optional[str] = "wav") -> BytesIO:
        """
        Synthesizes text to an in-memory bytestream in the specified audio format.

        :param text: The text to synthesize.
        :param format: The audio format (e.g., 'wav', 'mp3', 'flac'). Default: 'wav'.
        :return: A BytesIO object containing the audio data.
        """
        try:
            # Synthesize text to raw PCM bytes
            audio_bytes = self.synth_to_bytes(text)
            pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)

            # Convert PCM data to the desired audio format
            format = format if format else "wav"
            converted_audio = self._convert_audio(pcm_data, format, self.audio_rate)

            # Wrap the converted audio bytes in a BytesIO bytestream
            bytestream = BytesIO(converted_audio)
            bytestream.seek(0)  # Reset stream position to the beginning

            return bytestream
        except Exception as e:
            logging.error(f"Error in synth_to_bytestream: {e}")
            raise

    def synth_to_file(
        self, text: Any, filename: str, format: Optional[str] = "wav"
    ) -> None:
        """
        Synthesizes text to audio and saves it to a file.
        :param text: The text to synthesize.
        :param filename: The file where the audio will be saved.
        :param format: The format to save the file in (e.g., 'wav', 'mp3').
        """
        # Ensure format is not None
        format_to_use = format if format is not None else "wav"
        audio_bytes = self.synth_to_bytes(text)  # Always request raw PCM data
        pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
        converted_audio = self._convert_audio(pcm_data, format_to_use, self.audio_rate)

        with open(filename, "wb") as file:
            file.write(converted_audio)

    def synth(self, text: str, filename: str, format: Optional[str] = "wav"):
        """
        Alias for synth_to_file method.
        """
        self.synth_to_file(text, filename, format)

    def speak(self, text: Any) -> None:
        """
        Synthesize text and play it back using sounddevice.
        :param text: The text to synthesize and play.
        """
        try:
            audio_bytes = self.synth_to_bytes(text)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            sd.play(audio_data, samplerate=self.audio_rate)
            sd.wait()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def speak_streamed(
        self,
        text: Any,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
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
                    pcm_data, audio_format, self.audio_rate
                )
                with open(save_to_file_path, "wb") as f:
                    f.write(converted_audio)
                logging.info(
                    f"Audio saved to {save_to_file_path} in {audio_format} format."
                )

        except Exception as e:
            logging.error(f"Error streaming or saving audio: {e}")

    def setup_stream(self, samplerate=22050, channels=1, dtype="int16"):
        """
        Sets up the audio stream for playback.
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
        except Exception as e:
            logging.error(f"Failed to setup audio stream: {e}")
            raise

    def callback(self, outdata, frames, time, status):
        """
        Callback for streamed audio playback.
        """
        if status:
            logging.warning(f"Sounddevice status: {status}")
        if self.playing:
            # Each frame is 2 bytes for int16,
            # so frames * 2 gives the number of bytes
            end_position = self.position + frames * 2
            data = self.audio_bytes[self.position : end_position]
            if len(data) < frames * 2:
                # Not enough data to fill outdata, zero-pad it
                outdata.fill(0)
                outdata[: len(data) // 2] = np.frombuffer(data, dtype="int16").reshape(
                    -1, 1
                )  # noqa: E501
            else:
                outdata[:] = np.frombuffer(data, dtype="int16").reshape(
                    outdata.shape
                )  # noqa: E501
            self.position = end_position

            if self.position >= len(self.audio_bytes):
                self._trigger_callback("onEnd")
                self.playing.clear()
        else:
            outdata.fill(0)

    def _start_stream(self):
        """
        Starts the audio stream.
        """
        with self.stream_lock:
            if self.stream:
                self.stream.start()
            while self.stream.active and self.playing.is_set():
                time.sleep(0.1)
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

    def pause_audio(self):
        self.playing.clear()

    def resume_audio(self):
        self.playing.set()
        if not self.stream:
            self.setup_stream()
        if self.stream and not self.stream.active:
            self.stream.start()

    def stop_audio(self):
        self.playing.clear()
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()
        with self.stream_lock:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()

    def set_timings(self, timings: List[WordTiming]):
        self.timings = []
        total_duration = self.get_audio_duration()

        for i, timing in enumerate(timings):
            if len(timing) == 2:
                start_time, word = timing
                if i < len(timings) - 1:
                    end_time = (
                        timings[i + 1][0]
                        if len(timings[i + 1]) == 2
                        else timings[i + 1][1]
                    )  # noqa: E501
                else:
                    end_time = total_duration
                self.timings.append((start_time, end_time, word))
            elif len(timing) == 3:
                self.timings.append(timing)
            else:
                raise ValueError(f"Invalid timing format: {timing}")

    def get_timings(self) -> List[Tuple[float, float, str]]:
        return self.timings

    def get_audio_duration(self) -> float:
        if self.timings:
            return self.timings[-1][1]
        return 0.0

    def on_word_callback(self, word: str, start_time: float, end_time: float):
        logging.info(
            f"Word spoken: {word}, Start: {start_time:.3f}s, End: {end_time:.3f}s"
        )  # noqa: E501

    def connect(self, event_name: str, callback: Callable):
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback

    def _trigger_callback(self, event_name: str, *args):
        if event_name in self.callbacks and self.callbacks[event_name] is not None:
            self.callbacks[event_name](*args)

    def start_playback_with_callbacks(self, text: str, callback=None):
        if callback is None:
            callback = self.on_word_callback

        self.speak_streamed(text)
        start_time = time.time()

        for start, end, word in self.timings:
            try:
                delay = max(0, start - (time.time() - start_time))
                timer = threading.Timer(delay, callback, args=(word, start, end))
                timer.start()
                self.timers.append(timer)
            except Exception as e:
                logging.error(f"Error in start_playback_with_callbacks: {e}")

    def finish(self):
        try:
            with self.stream_lock:
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
        except Exception as e:
            logging.error(f"Failed to clean up audio resources: {e}")
        finally:
            self.stream = None

    def __del__(self):
        self.finish()

    def get_property(self, property_name):
        return self.properties.get(property_name, None)

    def set_property(self, property_name, value):
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
