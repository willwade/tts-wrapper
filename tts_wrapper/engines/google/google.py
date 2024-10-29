from typing import Any, List, Dict, Optional, Tuple, Generator
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS
from .client import GoogleClient
from .ssml import GoogleSSML
from ...engines.utils import (
    estimate_word_timings,
) # Import the timing estimation function
import logging
import numpy as np
import threading
import queue
import itertools
import sounddevice as sd
from io import BytesIO
import re


class GoogleTTS(AbstractTTS):
    def __init__(
        self,
        client: GoogleClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ):
        super().__init__()
        self._client = client
        self._lang = lang or "en-US"
        self._voice = voice or "en-US-Wavenet-C"
        self.generated_audio = None
        self.audio_format = "wav"  # Default format
        self.audio_rate = 16000  # Default sample rate for LINEAR16; adjust as needed
        self.audio_buffer = queue.Queue()
        self.playback_finished = threading.Event()
        self.audio_started = False
        self.audio_stopped = False
        self.audio_killed = False

    # Audio playback callback, called continuously to stream audio from the buffer
    def play_audio_callback(
        self, outdata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags
    ):
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
            current_chunk = self.audio_buffer.queue[0]
            k = current_chunk.shape[0]

            if remaining <= k:
                outdata[n:, 0] = current_chunk[:remaining]
                self.audio_buffer.queue[0] = current_chunk[remaining:]
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
        self._client.set_voice(voice_id, lang_id or self._lang)
        self.audio_rate = (
            16000  # Adjust based on your audio format; LINEAR16 is typically 16000 Hz
        )

    def synth_to_bytes(self, text: str) -> bytes:
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)
        logging.info(f"Synthesizing text: {text}")
        result = self._client.synth(
            str(text), self._voice, self._lang, include_timepoints=True
        )
        self.generated_audio = result["audio_content"]
        # No need to set audio_format here; it's managed in synth_to_bytestream
        # Remove the incorrect reference to 'format'
        # self.audio_format = format

        # Process timepoints to extract word timings
        timings = self._process_word_timings(result.get("timepoints", []))
        self.set_timings(timings)

        return self.generated_audio

    def _process_word_timings(
        self, timepoints: List[Dict[str, Any]]
    ) -> List[Tuple[float, float, str]]:
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, tp in enumerate(timepoints):
            start_time = float(tp["timeSeconds"])
            word = tp["markName"]

            if i < len(timepoints) - 1:
                end_time = float(timepoints[i + 1]["timeSeconds"])
            else:
                end_time = min(
                    start_time + 0.5, audio_duration
                )  # Use the lesser of 0.5s or remaining audio duration

            processed_timings.append((start_time, end_time, word))

        return processed_timings

    def get_audio_duration(self) -> float:
        if self.generated_audio and self.audio_format:
            return self._client.get_audio_duration(self.generated_audio)
        return 0.0

    @property
    def ssml(self) -> GoogleSSML:
        return GoogleSSML()

    def construct_prosody_tag(self, text: str) -> str:
        properties = []
        rate = self.get_property("rate")
        if rate != "":
            properties.append(f'rate="{rate}"')

        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')

        volume_in_number = self.get_property("volume")
        if volume_in_number != "":
            volume_in_words = self.mapped_to_predefined_word(volume_in_number)
            properties.append(f'volume="{volume_in_words}"')

        prosody_content = " ".join(properties)

        text_with_tag = f"<prosody {prosody_content}>{text}</prosody>"

        return text_with_tag

    def mapped_to_predefined_word(self, volume: str) -> str:
        volume_in_float = float(volume)
        if volume_in_float == 0:
            return "silent"
        if 1 <= volume_in_float <= 20:
            return "x-soft"
        if 21 <= volume_in_float <= 40:
            return "soft"
        if 41 <= volume_in_float <= 60:
            return "medium"
        if 61 <= volume_in_float <= 80:
            return "loud"
        if 81 <= volume_in_float <= 100:
            return "x-loud"

    def _split_text(self, text: str) -> List[str]:
        # Simple sentence splitter based on punctuation.
        sentences = re.split(r"(?<=[.!?]) +", text)
        return sentences

    def synth_to_bytestream(
        self, text: Any, format: Optional[str] = "wav"
    ) -> Generator[bytes, None, None]:
        """
        Synthesizes text to an in-memory bytestream and retrieves word timings using
        AbstractTTS's estimate_word_timings method.
        
        :param text: The text to synthesize.
        :param format: The desired audio format (e.g., 'wav', 'mp3', 'flac').
        :return: A generator yielding bytes objects containing audio data.
        """
        try:
            logging.info(f"[GoogleTTS.synth_to_bytestream] Synthesizing text: {text}")
            # Generate estimated word timings using the abstract method
            self.timings = estimate_word_timings(text)
            
            ## Split the text into smaller segments (e.g., sentences) for incremental synthesis
            #text_segments = self._split_text(text)

            #for segment_idx, segment in enumerate(text_segments):
        # Generate audio stream data and yield as chunks
            for timing in self.timings:
                #logging.info(f"Synthesizing segment {segment_idx}: {segment}")
                word = timing[2]
                logging.info(f"Synthesizing segment {word}")
                print(f"Synthesizing segment {word}")
                word_time = round(timing[1] - timing[0], 4)
                #print(f"timing: {word_time} seconds")
                result = self._client.synth(
                    str(word), self._voice, self._lang, include_timepoints=True
                )
                audio_bytes = result["audio_content"]

                if format.lower() == "wav":
                    # Yield raw PCM data (skip WAV header if necessary)
                    # Google TTS returns LINEAR16 PCM in WAV format
                    audio_stream = BytesIO(audio_bytes)
                    audio_stream.seek(44)  # Skip the 44-byte WAV header
                    chunk_size = 1024  # Number of bytes per chunk

                    while True:
                        chunk = audio_stream.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

                elif format.lower() in ["mp3", "flac"]:
                    # Convert PCM to the desired format using _convert_audio
                    audio_bytes = audio_bytes[44:]
                    pcm_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    converted_audio = self._convert_audio(
                        pcm_data, format, self.audio_rate
                    )
                    chunk_size = 4096  # Number of bytes per chunk
                    audio_io = BytesIO(converted_audio)

                    while True:
                        chunk = audio_io.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

                else:
                    raise UnsupportedFileFormat(f"Unsupported format: {format}")

        except Exception as e:
            logging.error(f"Error in synth_to_bytestream: {e}")
            raise

    def speak_streamed(
        self,
        text: str,
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
        # Synthesize audio to bytes
        audio_generator = self.synth_to_bytestream(text, format=audio_format)
        audio_bytes = bytes(itertools.chain.from_iterable(audio_generator))

        if audio_format == "mp3":
            # Decode MP3 to PCM
            pcm_data = self._convert_mp3_to_pcm(audio_bytes)
            channels = 1  # Assuming mono output
        else:
            # Directly use PCM data for other formats
            pcm_data = audio_bytes
            channels = 1

        # Playback in a new thread for non-blocking audio
        threading.Thread(
            print("Playing audio"),
            target=self._play_pcm_stream, args=(pcm_data, channels)
        ).start()

        # Optionally save to file
        if save_to_file_path:
            with open(save_to_file_path, "wb") as f:
                f.write(audio_bytes)

    def _play_pcm_stream(self, pcm_data: bytes, channels: int):
        """Streams PCM data using sounddevice."""
        audio_data = np.frombuffer(pcm_data, dtype=np.int16).reshape(-1, channels)
        with sd.OutputStream(
            samplerate=self.audio_rate,
            channels=channels,
            dtype="int16",
        ) as stream:
            stream.write(audio_data)

    def play_audio(self):
        """
        Plays audio from the audio_buffer using sounddevice.
        """
        try:
            logging.info("Starting audio playback thread...")
            with sd.OutputStream(
                samplerate=self.audio_rate,
                channels=1,
                callback=self.play_audio_callback,
                blocksize=4096,
                dtype="float32",
            ):
                self.playback_finished.wait()
        except Exception as e:
            logging.error(f"Error during audio playback: {e}")
            self.audio_killed = True
