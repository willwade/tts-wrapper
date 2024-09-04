# engine.py

from typing import Any, List, Optional, Dict
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from .client import SherpaOnnxClient  
from . ssml import SherpaOnnxSSML
from ...engines.utils import estimate_word_timings  # Import the timing estimation function
import logging
import numpy as np
import threading
import queue
import sounddevice as sd
import time

class SherpaOnnxTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: SherpaOnnxClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        if voice:
            self.set_voice(voice, lang)
        self.audio_rate = self._client.sample_rate
        self.audio_buffer = queue.Queue()
        self.playback_finished = threading.Event()
        self.audio_started = False
        self.audio_stopped = False
        self.audio_killed = False

    # Audio playback callback, called continuously to stream audio from the buffer
    def play_audio_callback(self, outdata, frames, time, status):
        if self.audio_killed or (self.audio_started and self.audio_buffer.empty() and self.audio_stopped):
            self.playback_finished.set()
            return

        if self.audio_buffer.empty():
            outdata.fill(0)
            return

        data = self.audio_buffer.get()
        if len(data) < frames:
            outdata[:len(data)] = data[:, None]
            outdata[len(data):] = 0
        else:
            outdata[:] = data[:frames, None]

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
            self._client.set_voice(voice_id)
            self.audio_rate = self._client.sample_rate  # Update the audio_rate based on the selected voice

    def synth_to_bytes(self, text: str, format: Optional[FileFormat] = "wav") -> bytes:
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)
        logging.info(f"Synthesizing text: {text}")
        audio_bytes, sample_rate = self._client.synth(text)
        logging.info(f"Audio bytes length: {len(audio_bytes)}, Sample rate: {sample_rate}")
        self.audio_rate = sample_rate
        return audio_bytes

    def play_audio(self):
        try:
            with sd.OutputStream(
                samplerate=self.audio_rate,
                channels=1,
                callback=self.play_audio_callback,
                blocksize=4096,
                dtype="float32"
            ):
                self.playback_finished.wait()

        except Exception as e:
            logging.error(f"Error during audio playback: {e}")
            self.audio_killed = True

    # Main function to generate audio and stream it while playing
    def speak_streamed(self, text):
        logging.info("[SherpaOnnxTTS.speak_streamed] Starting speech synthesis...")
        
        # Reset flags
        self.audio_started = False
        self.audio_stopped = False
        self.playback_finished.clear()

        # Start audio playback in a separate thread
        playback_thread = threading.Thread(target=self.play_audio)
        playback_thread.start()

        # Simulate audio generation in chunks from the text
        for chunk_idx, (progress, samples) in enumerate(self.generate_audio_chunks(text)):
            logging.info(f"Generated audio chunk with progress {progress}, samples shape: {samples.shape}")
            
            # Add audio samples to the buffer
            self.audio_buffer.put(samples)

            if not self.audio_started:
                logging.info("Starting audio playback...")
                self.audio_started = True

        # Signal that audio generation is complete
        self.audio_stopped = True

        # Wait for playback to finish
        playback_thread.join()
        logging.info("Playback finished.")


    def generate_audio_chunks(self, text):
        total_samples = 0
        for samples in self._client.generate_stream(text):
            # Ensure the samples are in float32 format
            if samples.dtype != np.float32:
                samples = samples.astype(np.float32)

            logging.info(f"Audio chunk max value: {np.max(samples)}, min value: {np.min(samples)}")
            total_samples += len(samples)
            progress = total_samples / (self.audio_rate * 3)  # Simulate progress
            yield progress, samples

    def _start_stream(self):
        self.setup_stream(output_file='output.wav') 
        logging.info("Stream started, entering active loop.")
        self.playing.set()

        while self.stream.active:
            logging.info("Stream is active, waiting for audio data...")
            time.sleep(0.1)  # This should allow the stream to process callbacks

        self.stop_audio()
        logging.info("Stream playback completed.")

    def setup_stream(self, channels=1, output_file=None):
        if self.audio_rate is None:
            raise ValueError("Audio rate is not set. Cannot set up the stream.")
        
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.output_file = output_file

        logging.info(f"Setting up stream with channels={channels}, rate={self.audio_rate}")

        # Initialize sounddevice OutputStream
        self.stream = sd.OutputStream(
            samplerate=self.audio_rate,
            channels=channels,
            blocksize=1024,  # Corresponds to frames_per_buffer
            callback=self.callback
        )
        
        if self.output_file:
            try:
                import wave
            except ImportError:
                logging.error("Wave module not available. Cannot write audio to file.")
                self.output_file = None
            else:
                self.wave_file = wave.open(self.output_file, 'wb')
                self.wave_file.setnchannels(channels)
                self.wave_file.setsampwidth(2)  # 16-bit PCM corresponds to 2 bytes
                self.wave_file.setframerate(self.audio_rate)

    def stop_audio(self):
        self.playing.clear()
        
        # Check if we are trying to join the current thread
        if threading.current_thread() is not self.play_thread:
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

    def callback(self, outdata, frames, time, status):
        try:
            samples = self._client.audio_queue.get_nowait()
        except queue.Empty:
            logging.info("Queue empty, returning silence.")
            return (b'\x00' * frame_count * 2, pyaudio.paContinue)

        if samples is None:
            logging.info("No more samples, completing stream.")
            return (None, pyaudio.paComplete)

        audio_bytes = self._convert_samples_to_bytes(samples)
        logging.info(f"Providing {len(audio_bytes)} bytes to stream.")
        if self.output_file:
            logging.info(f"Writing {len(audio_bytes)} bytes to file.")
            self.wave_file.writeframes(audio_bytes)
        outdata[:] = samples
        return

    def _convert_samples_to_bytes(self, samples: np.ndarray) -> bytes:
        # Convert numpy float32 array to 16-bit PCM bytes
        return (samples * 32767).astype(np.int16).tobytes()

    @property
    def ssml(self) -> SherpaOnnxSSML:
        return SherpaOnnxSSML()

    def construct_prosody_tag(self, text: str) -> str:
        # Implement SSML prosody tag construction if needed
        return text
    