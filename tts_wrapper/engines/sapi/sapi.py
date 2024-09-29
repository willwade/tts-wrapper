from typing import Any, List, Optional, Literal, Tuple, Generator
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import SAPIClient
from .ssml import SAPISSML
import re
import numpy as np
import pathlib
import logging
import threading
import queue
import sounddevice as sd
import time
from io import BytesIO


class SAPITTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: SAPIClient) -> None:
        super().__init__()
        self._client = client
        self.audio_buffer = queue.Queue()
        self.playback_finished = threading.Event()
        self.audio_started = False
        self.audio_stopped = False
        self.audio_killed = False       
        self.audio_format = "wav"  # Default format   

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        """Set the TTS voice by ID and optionally set the language ID."""
        self._client.set_voice(voice_id)

    def synth_to_bytes(self, text: Any) -> bytes:
        return self._client.synth(str(text))

    @property
    def ssml(self) -> SAPISSML:
        return SAPISSML()

    def get_voices(self):
        return self._client.get_voices()

    def get_property(self, property_name):
        """Get the value of a TTS property."""
        return self._client.get_property(property_name)

    def set_property(self, property_name, value):
        """Set the value of a TTS property."""
        return self._client.set_property(property_name, value)

    def construct_prosody_tag(self, text: str) -> str:
        """Constructs a prosody tag for consistency."""
        properties = []

        volume_in_number = self.get_property("volume")
        if volume_in_number is not None:
            volume_in_words = self._map_volume_to_predefined_word(volume_in_number)
            properties.append(f'volume="{volume_in_words}"')

        rate = self.get_property("rate")
        if rate is not None:
            properties.append(f'rate="{rate}"')

        # Since pyttsx3 does not support pitch, we just append the pitch for consistency
        pitch = self.get_property("pitch")
        if pitch is not None:
            properties.append(f'pitch="{pitch}"')

        prosody_content = " ".join(properties)
        text_with_tag = f"<prosody {prosody_content}>{text}</prosody>"

        return text_with_tag

    def _map_volume_to_predefined_word(self, volume: str) -> str:
        """Maps volume to predefined descriptive terms."""
        volume_in_float = float(volume)
        if volume_in_float == 0:
            return "silent"
        elif 1 <= volume_in_float <= 20:
            return "x-soft"
        elif 21 <= volume_in_float <= 40:
            return "soft"
        elif 41 <= volume_in_float <= 60:
            return "medium"
        elif 61 <= volume_in_float <= 80:
            return "loud"
        elif 81 <= volume_in_float <= 100:
            return "x-loud"
        else:
            return "medium"

    def speak_streamed(
        self,
        text: str,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
    ) -> None:
        """
        Synthesizes text and plays it back using sounddevice in a streaming fashion.
        Optionally saves the audio to a file after playback completes.

        :param text: The text to synthesize and play.
        :param save_to_file_path: Path to save the audio file (optional).
        :param audio_format: Audio format to save (e.g., 'wav', 'mp3', 'flac').
        """
        logging.info(
            "[SAPITTS.speak_streamed] Starting speech synthesis and playback..."
        )

        # Reset flags
        self.audio_started = False
        self.audio_stopped = False
        self.playback_finished.clear()

        # Open the output file if saving is required
        output_file = None
        if save_to_file_path:
            output_file = open(save_to_file_path, "wb")
            logging.info(
                f"Saving audio to {save_to_file_path} in {audio_format} format."
            )

        try:
            # Start audio playback in a separate thread
            playback_thread = threading.Thread(target=self.play_audio)
            playback_thread.start()

            # Iterate over the generator returned by synth_to_bytestream
            for chunk_idx, audio_chunk in enumerate(
                self.synth_to_bytestream(str(text), format=audio_format)
            ):
                logging.info(
                    f"Processing audio chunk {chunk_idx} with size {len(audio_chunk)} bytes"
                )
                if audio_format.lower() == "wav":
                    # Convert bytes back to numpy float32 array for playback
                    # Assuming audio_chunk is raw PCM data (LINEAR16)
                    samples = (
                        np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        / 32767.0
                    )
                elif audio_format.lower() in ["mp3", "flac"]:
                    # For formats like MP3 or FLAC, you need to decode them back to PCM
                    # This requires additional processing which is not implemented here
                    # For simplicity, we'll skip playback for non-WAV formats
                    samples = None
                    logging.warning(
                        f"Playback for format '{audio_format}' is not implemented."
                    )
                else:
                    raise UnsupportedFileFormat(f"Unsupported format: {audio_format}")

                if samples is not None:
                    # Add audio samples to the buffer for streaming playback
                    self.audio_buffer.put(samples)
                    logging.info(f"Audio chunk {chunk_idx} added to buffer")

                # Write the chunk to the file if saving
                if save_to_file_path:
                    output_file.write(
                        audio_chunk
                    )  # Corrected from f.write to output_file.write

                if not self.audio_started and samples is not None:
                    logging.info("Starting audio playback...")
                    self.audio_started = True

            # Signal that audio generation is complete
            self.audio_stopped = True

            # Wait for playback to finish
            playback_thread.join()
            logging.info("Playback finished.")

        except Exception as e:
            logging.error(f"Error during speak_streamed: {e}")
            self.audio_killed = True

        finally:
            if output_file:
                output_file.close()
                logging.info(
                    f"Audio successfully saved to {save_to_file_path} in {audio_format} format."
                )

    def synth_to_bytestream(
        self, text: Any, format: Optional[str] = "wav"
    ) -> Generator[bytes, None, None]:
        """
        Synthesizes text to an in-memory bytestream in the specified audio format.
        Yields audio data chunks as they are generated.

        :param text: The text to synthesize.
        :param format: The desired audio format (e.g., 'wav', 'mp3', 'flac'). Defaults to 'wav'.
        :return: A generator yielding bytes objects containing audio data.
        """
        try:
            logging.info(f"[SAPITTS.synth_to_bytestream] Synthesizing text: {text}")

            # Split the text into smaller segments (e.g., sentences) for incremental synthesis
            text_segments = self._split_text(text)

            for segment_idx, segment in enumerate(text_segments):
                logging.info(f"Synthesizing segment {segment_idx}: {segment}")
                #result = self._client.synth(
                #    str(segment), self._voice, self._lang, include_timepoints=True
                #)
                #audio_bytes = result["audio_content"]
                audio_bytes =  self._client.synth(str(segment))

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

    def _split_text(self, text: str) -> List[str]:
        # Simple sentence splitter based on punctuation.
        sentences = re.split(r"(?<=[.!?]) +", text)
        return sentences

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
