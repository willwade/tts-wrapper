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

        n = 0
        while n < frames and not self.audio_buffer.empty():
            remaining = frames - n
            k = self.audio_buffer.queue[0].shape[0]

            if remaining <= k:
                outdata[n:, 0] = self.audio_buffer.queue[0][:remaining]
                self.audio_buffer.queue[0] = self.audio_buffer.queue[0][remaining:]
                n = frames
                if self.audio_buffer.queue[0].shape[0] == 0:
                    self.audio_buffer.get()

                break

            outdata[n : n + k, 0] = self.audio_buffer.get()
            n += k

        if n < frames:
            outdata[n:, 0] = 0        

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
            self._client.set_voice(voice_id)
            self.audio_rate = self._client.sample_rate  # Update the audio_rate based on the selected voice

    def synth_to_bytes(self, text: str) -> bytes:
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)
        logging.info(f"Synthesizing text: {text}")
        audio_bytes, sample_rate = self._client.synth(text)
        logging.info(f"Audio bytes length: {len(audio_bytes)}, Sample rate: {sample_rate}")
        self.audio_rate = sample_rate
        
        if audio_bytes[:4] == b'RIFF':
           audio_bytes = self._strip_wav_header(audio_bytes)

        return audio_bytes

    def play_audio(self):
        try:
            logging.info("STARTING PLAY AUDIO")
            with sd.OutputStream(
                samplerate=self.audio_rate,
                channels=1,
                callback=self.play_audio_callback,
                blocksize=4096,
                #blocksize=16384,
                dtype="float32"
            ):
                self.playback_finished.wait()

        except Exception as e:
            logging.error(f"Error during audio playback: {e}")
            self.audio_killed = True

    # Main function to generate audio and stream it while playing
    def speak_streamed(self, text: str, save_to_file_path: Optional[str] = None, audio_format: Optional[str] = "wav") -> None:
        logging.info("[SherpaOnnxTTS.speak_streamed] Starting speech synthesis...")

        # Reset flags
        self.audio_started = False
        self.audio_stopped = False
        self.playback_finished.clear()

        # Start audio playback in a separate thread
        playback_thread = threading.Thread(target=self.play_audio)
        playback_thread.start()

        # Buffer to store all audio chunks for later saving
        all_audio_chunks = []

        # Simulate audio generation in chunks from the text
        for chunk_idx, (progress, samples) in enumerate(self.generate_audio_chunks(text)):
            logging.info(f"Generated audio chunk with progress {progress}, samples shape: {samples.shape}")
            
            # Add audio samples to the buffer for streaming
            self.audio_buffer.put(samples)
            logging.info("Finished with 1 audio chunk, put into queue")

            # Collect audio chunks for saving later
            all_audio_chunks.append(samples)

            if not self.audio_started:
                logging.info("Starting audio playback...")
                self.audio_started = True

        # Signal that audio generation is complete
        self.audio_stopped = True

        # Wait for playback to finish
        playback_thread.join()

        logging.info("Playback finished.")

        # Save the audio after playback finishes if save_to_file_path is provided
        if save_to_file_path:
            logging.info(f"Saving audio to file: {save_to_file_path} in format: {audio_format}")
            # Combine all chunks into one audio array
            full_audio = np.concatenate(all_audio_chunks, axis=0)

            # Convert audio and save to the specified file format
            converted_audio = self._convert_audio(full_audio, audio_format, self.audio_rate)
            with open(save_to_file_path, "wb") as f:
                f.write(converted_audio)

            logging.info(f"Audio successfully saved to {save_to_file_path} in {audio_format} format.")


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
    