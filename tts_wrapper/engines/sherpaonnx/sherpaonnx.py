# engine.py

import logging
import queue
import threading
from collections.abc import Generator
from typing import Any, Optional

import numpy as np
import sounddevice as sd

from tts_wrapper.engines.utils import (
    estimate_word_timings,  # Import the timing estimation function
)
from tts_wrapper.tts import AbstractTTS

from .client import SherpaOnnxClient
from .ssml import SherpaOnnxSSML


class SherpaOnnxTTS(AbstractTTS):
    def __init__(
        self,
        client: SherpaOnnxClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._client = client
        if voice:
            self.set_voice(voice_id=voice, lang_id=lang)
        self.audio_rate = self._client.sample_rate
        self.audio_buffer = queue.Queue()
        self.playback_finished = threading.Event()
        self.audio_started = False
        self.audio_stopped = False
        self.audio_killed = False

    # Audio playback callback, called continuously to stream audio from the buffer
    def play_audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time,
        status: sd.CallbackFlags,
    ) -> None:

        if self.audio_killed or (
            self.audio_started and self.audio_buffer.empty() and self.audio_stopped
        ):
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

    def get_voices(self) -> list[dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(
        self, voice_id: Optional[str] = None, lang_id: Optional[str] = None
    ) -> None:
        """
        Set the voice for synthesis.

        Parameters
        ----------
        voice_id : Optional[str], optional
            The ID of the voice to use for synthesis.
            Note: SherpaOnnx may not support all voice selection methods.
        lang_id : Optional[str], optional
            The language ID to use for synthesis.

        Note
        ----
        SherpaOnnx has limited voice selection capabilities compared to other TTS engines.
        This method attempts to set the voice if possible, but may not have the same
        flexibility as other TTS engines.
        """
        # Call the client's set_voice method with the provided parameters
        self._client.set_voice(voice_id=voice_id, lang_id=lang_id)
        # Update the audio_rate based on the selected voice
        self.audio_rate = self._client.sample_rate

    def synth_to_bytes(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """
        Transform written text to audio bytes.

        Parameters
        ----------
        text : str
            The text to synthesize.
        voice_id : Optional[str], optional
            The ID of the voice to use for synthesis.
            Note: SherpaOnnx doesn't support dynamic voice switching, so this parameter is ignored.

        Returns
        -------
        bytes
            Raw PCM data with no headers for sounddevice playback.
        """
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)
        logging.info("Synthesizing text: %s", text)
        audio_bytes, sample_rate = self._client.synth(text)
        logging.info(
            f"Audio bytes length: {len(audio_bytes)}, Sample rate: {sample_rate}",
        )
        self.audio_rate = sample_rate

        if audio_bytes[:4] == b"RIFF":
            audio_bytes = self._strip_wav_header(audio_bytes)

        # Generate word timings
        words = text.split()
        audio_duration = len(audio_bytes) / (2 * self.audio_rate)  # Duration in seconds
        word_duration = audio_duration / len(words)

        # Create evenly spaced word timings
        word_timings = []
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration
            word_timings.append((start_time, end_time, word))
        self.set_timings(word_timings)

        return audio_bytes

    def play_audio(self) -> None:
        try:
            logging.info("STARTING PLAY AUDIO")
            with sd.OutputStream(
                samplerate=self.audio_rate,
                channels=1,
                callback=self.play_audio_callback,
                blocksize=4096,
                # blocksize=16384,
                dtype="float32",
            ):
                self.playback_finished.wait()

        except Exception as e:
            logging.exception("Error during audio playback: %s", e)
            self.audio_killed = True

    # Main function to generate audio and stream it while playing
    def speak_streamed(
        self,
        text: str,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
    ) -> None:
        """
        Synthesize text to speech and stream it for playback.

        Args:
            text: The text to synthesize
            save_to_file_path: Optional path to save the audio file
            audio_format: Optional format for the audio file (wav, mp3, etc.)
        """
        try:
            # Generate audio data
            audio_data = self.synth_to_bytes(text)

            # Save to file if requested
            if save_to_file_path:
                with open(save_to_file_path, "wb") as f:
                    f.write(audio_data)

            # Start playback using base class's system
            self.load_audio(audio_data)
            self.play()

        except Exception as e:
            logging.exception("Error in speak_streamed: %s", e)

    def synth_to_bytestream(
        self,
        text: Any,
        format: Optional[str] = "wav",
    ) -> Generator[bytes, None, None]:
        """Synthesizes text to an in-memory bytestream in the specified audio format.
        Yields audio data chunks as they are generated.

        :param text: The text to synthesize.
        :param format: The desired audio format (e.g., 'wav', 'mp3', 'flac'). Defaults to 'wav'.
        :return: A generator yielding bytes objects containing audio data.
        """
        try:
            logging.info(
                f"[SherpaOnnxTTS.synth_to_bytestream] Synthesizing text: {text}",
            )

            # Generate estimated word timings using the abstract method
            self.timings = estimate_word_timings(text)

            # Buffer to store all audio chunks for conversion
            audio_chunks = []

            # Iterate over generated audio chunks
            for chunk_idx, (progress, samples) in enumerate(
                self.generate_audio_chunks(text),
            ):
                logging.info(
                    f"Processing audio chunk {chunk_idx} with progress {progress}",
                )

                # Collect audio chunks for conversion
                audio_chunks.append(samples)

                # Concatenate current chunks for conversion
                current_audio = np.concatenate(audio_chunks, axis=0)

                # Convert PCM data to the desired audio format
                converted_audio = self._convert_audio(
                    current_audio,
                    format,
                    self.audio_rate,
                )
                logging.info(
                    f"Converted audio chunk {chunk_idx} length: {len(converted_audio)} bytes in format: {format}",
                )

                if converted_audio[:4] == b"RIFF":
                    logging.info("Stripping wav header from bytestream")
                    converted_audio = self._strip_wav_header(converted_audio)

                # Yield the converted audio chunk
                yield converted_audio

                # Reset the buffer after yielding
                audio_chunks = []

            # After all chunks are processed, perform any necessary finalization
            if audio_chunks:
                current_audio = np.concatenate(audio_chunks, axis=0)
                converted_audio = self._convert_audio(
                    current_audio,
                    format,
                    self.audio_rate,
                )
                logging.info(
                    f"Final converted audio length: {len(converted_audio)} bytes in format: {format}",
                )
                if format == "wav" and converted_audio[:4] == b"RIFF":
                    logging.info("Stripping wav header from bytestream")
                    converted_audio = self._strip_wav_header(converted_audio)

                yield converted_audio

        except Exception as e:
            logging.exception("Error in synth_to_bytestream: %s", e)
            raise

    def generate_audio_chunks(self, text):
        total_samples = 0
        for samples in self._client.generate_stream(text):
            # Ensure the samples are in float32 format
            if samples.dtype != np.float32:
                samples = samples.astype(np.float32)

            logging.info(
                f"Audio chunk max value: {np.max(samples)}, min value: {np.min(samples)}",
            )
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
