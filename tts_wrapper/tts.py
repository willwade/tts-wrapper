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
    
        self.playing = False
        self.paused = False
        self.position = 0
        
        self.stream_pyaudio = None
        self.playback_thread = None
        self.pause_timer = None
        self.pyaudio = None

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def check_credentials(self) -> bool:
        """
        Verifies that the provided credentials are valid by calling get_voices.
        This method should be implemented by the child classes to handle the
          specific credential checks.
        Also try not to use get_voices. It can be wasteful in credits/bandwidth
        """
        try:
            # Attempt to retrieve voices to validate credentials
            voices = self.get_voices()
            if voices:
                print("Credentials successfully verified.")
                return True
            else:
                print("Failed to retrieve voices. Credentials may be invalid.")
                return False
        except Exception as e:
            print(f"Credentials check failed: {e}")
            return False

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

    def load_audio(self, audio_bytes):
        import pyaudio
        """Load audio bytes into the player"""
        self.pyaudio = pyaudio.PyAudio()
        if not audio_bytes:
            raise ValueError("Audio bytes cannot be empty")        
        self.audio_bytes = audio_bytes
        self.position = 0
    
    def _create_stream(self):
        """Create a new audio stream"""
        if self.stream_pyaudio is not None and not self.stream_pyaudio.is_stopped():
            self.stream_pyaudio.stop_stream()
            self.stream_pyaudio.close()

        self.playing = True 
        try:       
            self.stream_pyaudio = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(self.sample_width),
                channels=self.channels,
                rate=self.audio_rate,
                output=True
            )
        except Exception as e:
            logging.error(f"Failed to create stream: {e}")
            self.playing = False
            raise            
    
    def _playback_loop(self):
        """Main playback loop running in separate thread"""
        try:
            self._create_stream()
            while self.playing and self.position < len(self.audio_bytes):
                if not self.paused:
                    chunk = self.audio_bytes[self.position:self.position + self.chunk_size]
                    if chunk:
                        self.stream_pyaudio.write(chunk)
                        self.position += len(chunk)
                    else:
                        break
                else:
                    time.sleep(0.1)  # Reduce CPU usage while paused
            
            # Cleanup after playback ends
            if self.stream_pyaudio and not self.stream_pyaudio.is_stopped():
                self.stream_pyaudio.stop_stream()
                self.stream_pyaudio.close()
            self.playing = False
        except Exception as e:
            print(f"Error in playback loop: {e}")
            self.playing = False
    
    def _auto_resume(self):
        """Helper method to resume after timed pause"""
        self.paused = False
        logging.info("Resuming playback after pause")
    
    def play(self, duration=None):
        """Start or resume playback"""
        if self.audio_bytes is None:
            raise ValueError("No audio loaded")
        
        if not self.playing:            
            self.playing = True
            self.paused = False
            self.playback_thread = threading.Thread(target=self._playback_loop)
            self.playback_thread.start()
            time.sleep(float(duration or 0))
        elif self.paused:
            self.paused = False
        
    
    def pause(self, duration=None):
        """
        Pause playback with optional duration
        
        Parameters:
        duration (float): Number of seconds to pause. If None, pause indefinitely
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
            print(f"Pausing for {duration} seconds")
            time.sleep(float(duration or 0))
    
    def resume(self):
        """Resume playback"""
        print("Resume playback")
        if self.playing:
            # Cancel any existing pause timer
            if self.pause_timer:
                self.pause_timer.cancel()
                self.pause_timer = None
            self.paused = False

    def stop(self):
        """Stop playback"""
        self.playing = False
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
            except Exception as e:
                logging.info("Stream already closed")

            self.stream_pyaudio = None
            
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
        self.position = 0
        
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()

            if self.pyaudio:
                self.pyaudio.terminate()
        except Exception as e:
            print(f"Error during cleanup: {e}")

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

#    def pause_audio(self):
#        self.playing.clear()

#    def resume_audio(self):
#        self.playing.set()
#        if not self.stream:
#            self.setup_stream()
#        if self.stream and not self.stream.active:
#            self.stream.start()
#
#    def stop_audio(self):
#        self.playing.clear()
#        if self.play_thread and self.play_thread.is_alive():
#            self.play_thread.join()
#        with self.stream_lock:
#            if self.stream:
#                self.stream.stop()
#                self.stream.close()
#                self.stream = None
#        for timer in self.timers:
#            timer.cancel()
#        self.timers.clear()

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
