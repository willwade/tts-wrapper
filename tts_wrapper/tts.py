from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Union, Dict, Callable
import pyaudio
import threading
from threading import Event
import logging
import time

FileFormat = Union[Literal["wav"], Literal["mp3"]]

class AbstractTTS(ABC):
    """Abstract class (ABC) for text-to-speech functionalities, including synthesis and playback."""

    def __init__(self):
        self.voice_id = None
        self.audio_object = None
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.audio_rate = 22050
        self.audio_bytes = None
        self.playing = Event()
        self.playing.clear()  # Not playing by default
        self.position = 0  # Position in the byte stream
        self.timings = []
        self.timers = []
        self.properties = {}
        self.callbacks = {
            'started-utterance': None,
            'finished-utterance': None,
            'started-word': None
        }

    @abstractmethod
    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the TTS service."""
        pass

    def set_voice(self, voice_id: str, lang: str = "en-US"):
        self.voice_id = voice_id
        self.lang = lang

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
        with open(filename, "wb") as file:
            file.write(audio_content)

    def synth(self, text: str, filename: str, format: Optional[FileFormat] = "wav"):
        self.synth_to_file(text, filename, format)

    def speak(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        try:
            audio_bytes = self.synth_to_bytes(text, format)
            audio_bytes = self.apply_fade_in(audio_bytes)
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.audio_rate, output=True)
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            
    def setup_stream(self, format=pyaudio.paInt16, channels=1):
        try:
            if self.p is None:
                self.p = pyaudio.PyAudio()
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.stream = self.p.open(format=format,
                                      channels=channels,
                                      rate=self.audio_rate,
                                      output=True,
                                      stream_callback=self.callback)
        except Exception as e:
            logging.error(f"Failed to setup audio stream: {e}")
            raise

    def callback(self, in_data, frame_count, time_info, status):
        if self.playing:
            end_position = self.position + frame_count * 2
            data = self.audio_bytes[self.position:end_position]
            self.position = end_position
            if self.position >= len(self.audio_bytes):
                self._trigger_callback('finished-utterance', 'utterance', True)
                return (data, pyaudio.paComplete)
            return (data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paContinue)

    def speak_streamed(self, text: Any, format: Optional[FileFormat] = "wav"):
        try:
            audio_bytes = self.synth_to_bytes(text, format)
        except Exception as e:
            logging.error(f"Error synthesizing speech: {e}")
        self.audio_bytes = self.apply_fade_in(audio_bytes)
        self.position = 0
        self.playing.set()
        self._trigger_callback('started-utterance', 'utterance')
        if not self.stream:
            self.setup_stream()
        try:
            self.play_thread = threading.Thread(target=self._start_stream)
            self.play_thread.start()
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
            raise

    def apply_fade_in(self, audio_bytes, fade_duration_ms=50, sample_rate=22050):
        num_fade_samples = int(fade_duration_ms * sample_rate / 1000)
        fade_in = [i / num_fade_samples for i in range(num_fade_samples)]
    
        audio_samples = list(int.from_bytes(audio_bytes[2 * i:2 * i + 2], 'little', signed=True)
                             for i in range(len(audio_bytes) // 2))
    
        for i in range(min(len(audio_samples), num_fade_samples)):
            audio_samples[i] = int(audio_samples[i] * fade_in[i])
    
        faded_audio_bytes = b''.join((sample.to_bytes(2, 'little', signed=True) for sample in audio_samples))
        return faded_audio_bytes
        
    def _start_stream(self):
        if self.stream:
            self.stream.start_stream()
        while self.stream.is_active() and self.playing.is_set():
            time.sleep(0.1)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def pause_audio(self):
        self.playing.clear()

    def resume_audio(self):
        self.playing.set()
        if not self.stream:
            self.setup_stream()
        if self.stream and not self.stream.is_active():
            self.stream.start_stream()

    def stop_audio(self):
        self.playing.clear()
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()

    def set_timings(self, timing_data):
        self.timings = timing_data

    def on_word_callback(self, word):
        print(f"Word spoken: {word}")

    def connect(self, event_name: str, callback: Callable):
        if event_name in self.callbacks:
            self.callbacks[event_name] = callback

    def _trigger_callback(self, event_name: str, *args):
        if event_name in self.callbacks and self.callbacks[event_name] is not None:
            self.callbacks[event_name](*args)

    def start_playback_with_callbacks(self, ssml_text: bytes, callback=None):
        if callback is None:
            callback = self.on_word_callback

        self.speak_streamed(ssml_text)
        start_time = time.time()
        for timing, word in self.timings:
            delay = timing - (time.time() - start_time)
            if delay > 0:
                timer = threading.Timer(delay, callback, args=(word, timing))
                timer.start()
                self.timers.append(timer)
                
    def finish(self):
        try:
            if self.stream and not self.stream.is_stopped():
                self.stream.stop_stream()
            if self.stream:
                self.stream.close()
            if self.p:
                self.p.terminate()
        except Exception as e:
            logging.error(f"Failed to clean up audio resources: {e}")
        finally:
            self.stream = None
            self.p = None

    def __del__(self):
        self.finish()
    
    def get_property(self, property_name):
        return self.properties.get(property_name, None)

    def set_property(self, property_name, value):
        self.properties[property_name] = value

        # Custom handling for specific properties if needed
        if property_name == "rate":
            self.audio_rate = value
        elif property_name == "volume":
            self._volume = value
        elif property_name == "pitch":
            self._pitch = value
        # Add more custom handling if needed