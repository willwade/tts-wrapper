from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Union, Dict, Callable
import sounddevice as sd
import threading
import logging
import time
import re
import wave
import numpy as np

FileFormat = Union[Literal["wav"], Literal["mp3"]]

class AbstractTTS(ABC):
    """Abstract class (ABC) for text-to-speech functionalities, including synthesis and playback."""

    def __init__(self):
        self.voice_id = None
        self.audio_object = None
        self.audio_rate = 22050
        self.audio_bytes = None
        self.playing = threading.Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []
        self.properties = {
            'volume': "",
            'rate': "",
            'pitch': ""
        }
        self.callbacks = {
            'onStart': None,
            'onEnd': None,
            'started-word': None
        }
        self.stream_lock = threading.Lock()
        self.stream = None
        self.exit_event = threading.Event()

        logging.basicConfig(level=logging.DEBUG)
        logging.debug("AbstractTTS initialized")

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def set_voice(self, voice_id: str, lang: str = "en-US"):
        self.voice_id = voice_id
        self.lang = lang
        logging.debug(f"Voice set to {voice_id} with language {lang}")

    @classmethod
    @abstractmethod
    def supported_formats(cls) -> List[FileFormat]:
        """Returns list of supported audio types in concrete text-to-speech classes."""
        pass

    @abstractmethod
    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        """Transforms written text to audio bytes on supported formats."""
        pass

    def synth_to_file(self, text: Any, filename: str, format: Optional[FileFormat] = None) -> None:
        audio_content = self.synth_to_bytes(text, format=format or "wav")

        # Ensure proper format and sample width
        with wave.open(filename, "wb") as file:
            file.setnchannels(1)
            file.setsampwidth(2)  # 16-bit audio
            file.setframerate(self.audio_rate)
            file.writeframes(audio_content)
        logging.debug(f"Audio saved to {filename}")

    def synth(self, text: str, filename: str, format: Optional[FileFormat] = "wav"):
        self.synth_to_file(text, filename, format)

    def speak(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        try:
            audio_bytes = self.synth_to_bytes(text, format)
            audio_bytes = self.apply_fade_in(audio_bytes)

            audio_data = self.bytes_to_samples(audio_bytes)
            sd.play(audio_data, samplerate=self.audio_rate)
            sd.wait()
            logging.debug("Audio playback completed")
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def apply_fade_in(self, audio_bytes, fade_duration_ms=50, sample_rate=22050):
        num_fade_samples = int(fade_duration_ms * sample_rate / 1000)
        fade_in = np.linspace(0, 1, num_fade_samples)

        audio_samples = self.bytes_to_samples(audio_bytes).copy()

        for i in range(min(len(audio_samples), num_fade_samples)):
            audio_samples[i] *= fade_in[i]

        faded_audio_bytes = self.samples_to_bytes(audio_samples)
        return faded_audio_bytes

    def speak_streamed(self, text: Any, format: Optional[FileFormat] = "wav"):
        try:
            audio_bytes = self.synth_to_bytes(text, format)
            if not isinstance(audio_bytes, (bytes, bytearray)):
                raise ValueError("Synthesized speech is not in bytes format")
        except Exception as e:
            logging.error(f"Error synthesizing speech: {e}")
            return

        self.audio_bytes = self.apply_fade_in(audio_bytes)
        self.position = 0
        self.playing.set()
        self.exit_event.clear()
        self._trigger_callback('onStart')
        logging.debug("Starting streamed playback")

        try:
            self.play_thread = threading.Thread(target=self._start_stream)
            self.play_thread.start()
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
            raise

    def _start_stream(self):
        try:
            with self.stream_lock:
                if self.stream is not None:
                    self.stream.close()
                audio_data = self.bytes_to_samples(self.audio_bytes)
                self.stream = sd.OutputStream(
                    samplerate=self.audio_rate,
                    channels=1,
                    dtype='int16',
                    callback=self.callback
                )
                self.stream.start()
                logging.info("Stream started")
                while self.playing.is_set() and not self.exit_event.is_set():
                    time.sleep(0.1)
                self.stream.stop()
                logging.info("Stream stopped")
        except Exception as e:
            logging.error(f"Failed to start stream: {e}")
        finally:
            self.exit_event.set()  # Ensure the exit event is set
            logging.info("Stream thread exiting")
            with self.stream_lock:
                self.stream = None  # Ensure stream is set to None
            logging.info("Stream lock released in _start_stream")

    def callback(self, outdata, frames, time, status):
        try:
            with self.stream_lock:
                if self.exit_event.is_set():
                    outdata.fill(0)
                    return
                if self.playing.is_set():
                    end_position = self.position + frames * 2
                    chunk = self.bytes_to_samples(self.audio_bytes[self.position:end_position])
                    if len(chunk) < frames:
                        chunk = np.pad(chunk, (0, frames - len(chunk)), 'constant')
                        self._trigger_callback('onEnd')
                        self.playing.clear()
                    outdata[:len(chunk)] = chunk.reshape(-1, 1)
                    self.position = end_position
                    logging.debug(f"Audio chunk played, position: {self.position}")
                else:
                    outdata.fill(0)
                    logging.debug(f"Audio paused at position: {self.position}")
        except Exception as e:
            logging.error(f"Error in callback: {e}")
        finally:
            logging.info("Stream lock released in callback")

    def pause_audio(self):
        logging.info("Pausing audio")
        self.playing.clear()
        logging.info(f"Paused at position {self.position}")

    def resume_audio(self):
        logging.info("Resuming audio")
        self.playing.set()
        logging.info("Stream resumed")

    def stop_audio(self):
        logging.info("Stopping audio")
        self.playing.clear()
        self.exit_event.set()
        logging.info("Cleared playing event")
    
        logging.info("Attempting to acquire stream lock in stop_audio")
        lock_acquired = self.stream_lock.acquire(timeout=5)
        if not lock_acquired:
            logging.error("Failed to acquire stream lock in stop_audio")
            # Clean up without the lock
            if self.play_thread and self.play_thread.is_alive():
                logging.info("Joining play thread")
                self.play_thread.join(timeout=5)  # Add a timeout to join
                if self.play_thread.is_alive():
                    logging.warning("Play thread did not terminate within timeout")
                else:
                    logging.info("Play thread terminated")

            for timer in self.timers:
                timer.cancel()
                logging.info("Cancelled timer")
            self.timers.clear()
            logging.info("Timers cleared")
            return
        
        try:
            logging.info("Acquired stream lock in stop_audio")
            if self.stream:
                logging.info("Stream exists, attempting to stop")
                try:
                    self.stream.abort()
                    logging.info("Stream aborted")
                    self.stream.close()
                    logging.info("Stream closed")
                except Exception as e:
                    logging.error(f"Error stopping stream: {e}")
                finally:
                    self.stream = None
            else:
                logging.info("No active stream to stop")
        finally:
            self.stream_lock.release()
            logging.info("Released stream lock in stop_audio")

        if self.play_thread and self.play_thread.is_alive():
            logging.info("Joining play thread")
            self.play_thread.join(timeout=5)  # Add a timeout to join
            if self.play_thread.is_alive():
                logging.warning("Play thread did not terminate within timeout")
            else:
                logging.info("Play thread terminated")

        for timer in self.timers:
            timer.cancel()
            logging.info("Cancelled timer")
        self.timers.clear()
        logging.info("Timers cleared")

        logging.info("Audio stopped")

    def connect(self, event_name: str, callback: Callable):
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback
        logging.debug(f"Connected callback for {event_name}")

    def _trigger_callback(self, event_name: str, *args):
        if event_name in self.callbacks and self.callbacks[event_name] is not None:
            self.callbacks[event_name](*args)
        logging.debug(f"Triggered callback for {event_name}")

    def bytes_to_samples(self, audio_bytes):
        """Convert bytes to a numpy array of samples (int16)."""
        return np.frombuffer(audio_bytes, dtype=np.int16)

    def samples_to_bytes(self, samples):
        """Convert a numpy array of samples (int16) to bytes."""
        return samples.tobytes()

    def start_playback_with_callbacks(self, ssml_text: bytes, callback=None):
        if callback is None:
            callback = self.on_word_callback

        self.speak_streamed(ssml_text)
        start_time = time.time()
        for timing, word in self.timings:
            try:
                delay = timing - (time.time() - start_time)
                if delay > 0:
                    timer = threading.Timer(delay, callback, args=(word, timing))
                    timer.start()
                    self.timers.append(timer)
            except Exception as e:
                logging.error(f"Error in start_playback_with_callbacks: {e}")

                logging.error(f"Error in start_playback_with_callbacks: {e}")

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
        """Determine if the input text is SSML."""
        return bool(re.match(r'^\s*<speak>', text, re.IGNORECASE))

    def _convert_to_ssml(self, text: str) -> str:
        """Convert plain text to SSML with word markers."""
        words = text.split()
        ssml_parts = ["<speak>"]

        ssml_parts.append(ssml_volume)
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="word{i}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)

    def mapped_to_predefined_word(self, volume: str) -> str:
        pass

    def set_timings(self, timing_data):
        self.timings = timing_data

