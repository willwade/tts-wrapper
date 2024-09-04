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
    def play_audio_callback(self, outdata: np.ndarray, frames: int, time, status: sd.CallbackFlags):
        
        if self.audio_killed or (self.audio_started and self.audio_buffer.empty() and self.audio_stopped):
            logging.error("AUDIO KILLED OR STOPPED OR BUFFER EMPTY")
            self.playback_finished.set()
            return

        if self.audio_buffer.empty():
            outdata.fill(0)
            return

        data = self.audio_buffer.get()
        logging.info(f"Get audio data to play : {data}")
        if len(data) < frames:
            logging.info(f"Audio chunk {len(data)} is shorter than frame: {frames}")
            outdata[:len(data)] = data[:, None]
            outdata[len(data):] = 0
        elif len(data) == frames:
            outdata = data
        else:
            outdata[:] = data[:frames, None]
            # Insert leftover into the queue at the beginning
            leftover = data[frames:]
            self.audio_buffer.put(leftover)

        #else:
        #    outdata[:] = data[:frames, None]
        

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
            logging.info("STARTING PLAY AUDIO")
            with sd.OutputStream(
                samplerate=self.audio_rate,
                channels=1,
                callback=self.play_audio_callback,
                blocksize=1024,
                #blocksize=16384,
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
            logging.info("Finished with 1 audio chunk, put into queue")


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

    def _convert_samples_to_bytes(self, samples: np.ndarray) -> bytes:
        # Convert numpy float32 array to 16-bit PCM bytes
        return (samples * 32767).astype(np.int16).tobytes()

    @property
    def ssml(self) -> SherpaOnnxSSML:
        return SherpaOnnxSSML()

    def construct_prosody_tag(self, text: str) -> str:
        # Implement SSML prosody tag construction if needed
        return text
    