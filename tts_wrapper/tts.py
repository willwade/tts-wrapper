from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Union, Dict, Callable
import pyaudio
import threading
from threading import Event
import logging
import time
import re
import wave

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
        self.properties = {
            'volume' :"",
            'rate': "",
            'pitch':""
        }
        self.callbacks = {
            'onStart': None,
            'onEnd': None,
            'started-word': None
        }
        self.stream_lock = threading.Lock()


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
        print ("text synth to file: ", text)
        audio_content = self.synth_to_bytes(text, format=format or "wav")
        #audio_content = self.apply_fade_in(audio_content)
        
        #open file and add wav header before write in the audio content
        channels = 1
        sample_width = 2 #8 bit audio      
        with wave.open(filename, "wb") as file:
            file.setnchannels(channels)
            file.setsampwidth(sample_width)
            file.setframerate(self.audio_rate)
            file.writeframes(audio_content)

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
    
    @abstractmethod
    def construct_prosody_tag(self, text:str) -> str:
        pass

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
                self._trigger_callback('onEnd')
                return (data, pyaudio.paComplete)
            return (data, pyaudio.paContinue)
        else:
            return (None, pyaudio.paContinue)


    def speak_streamed(self, text: Any, format: Optional[FileFormat] = "wav"):
        try:
            logging.info("[TTS.speak_streamed] Starting speech synthesis...")
            audio_bytes = self.synth_to_bytes(text, format)
            if not isinstance(audio_bytes, (bytes, bytearray)):
                raise ValueError("[TTS.speak_streamed] Synthesized speech is not in bytes format")
            logging.info(f"[TTS.speak_streamed] Synthesized speech length: {len(audio_bytes)} bytes")
        except Exception as e:
            logging.error(f"[TTS.speak_streamed] Error synthesizing speech: {e}")
            return
        self.audio_bytes = self.apply_fade_in(audio_bytes)
        self.position = 0
        self.playing.set()
        self._trigger_callback('onStart')

        with self.stream_lock:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.setup_stream()        
        try:
            self.play_thread = threading.Thread(target=self._start_stream)
            self.play_thread.start()
        except Exception as e:
            logging.error(f"[TTS.speak_streamed] Failed to play audio: {e}")
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
        with self.stream_lock:
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
        with self.stream_lock:
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
            try:
                delay = timing - (time.time() - start_time)
                if delay > 0:
                    timer = threading.Timer(delay, callback, args=(word, timing))
                    timer.start()
                    self.timers.append(timer)
            except Exception as e:
                logging.error(f"Error in start_playback_with_callbacks: {e}")
                
    def finish(self):
        try:
            with self.stream_lock:
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