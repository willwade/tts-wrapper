from typing import Any, List, Dict, Optional, Tuple, Generator
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import ElevenLabsClient, ElevenLabsSSMLRoot
import re
import numpy as np
import pathlib
import logging
import threading
import queue
import sounddevice as sd
import time
from io import BytesIO


class ElevenLabsTTS(AbstractTTS):
    def __init__(
        self,
        client: ElevenLabsClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ):
        super().__init__()
        self._client = client
        self.audio_rate = 22050  # Kept at 22050
        self.set_voice(voice or "yoZ06aMxZJJ28mfd3POQ", lang or "en-US")
        self.audio_buffer = queue.Queue()
        self.playback_finished = threading.Event()
        self.audio_started = False
        self.audio_stopped = False
        self.audio_killed = False       
        self.audio_format = "wav"  # Default format         

    def synth_to_bytes(self, text: Any) -> bytes:
        if not self._voice:
            raise ValueError("Voice ID must be set before synthesizing speech.")

        # Get the audio and word timings from the ElevenLabs API
        self.generated_audio, word_timings = self._client.synth(str(text), self._voice)
        self.set_timings(word_timings)

        prosody_text = str(text)
        if "volume=" in prosody_text:
            volume = self.get_volume_value(prosody_text)
            self.generated_audio = self.adjust_volume_value(
                self.generated_audio, volume
            )

        # check if wav file has header. Strip header to make it raw
        if self.generated_audio[:4] == b"RIFF":
            self.generated_audio = tts._strip_wav_header(self.generated_audio)

        return self.generated_audio

    def get_audio_duration(self) -> float:
        """
        Calculate the duration of the audio based on the number of samples and sample rate.
        """
        if self.generated_audio is not None:
            num_samples = len(self.generated_audio) // 2  # Assuming 16-bit audio
            return num_samples / self.audio_rate
        return 0.0

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

    def adjust_volume_value(self, generated_audio: bytes, volume: float) -> bytes:
        # check if generated audio length is odd. If it is, add an empty byte since np.frombuffer is expecting
        # an even length

        try:
            import numpy as np
        except ImportError:
            raise ModuleNotInstalled("numpy")

        if len(generated_audio) % 2 != 0:
            generated_audio += b"\x00"

        generated_audio = np.frombuffer(generated_audio, dtype=np.int16)

        # Convert to float32 for processing
        samples_float = (
            generated_audio.astype(np.float32) / 32768.0
        )  # Normalize to [-1.0, 1.0]

        # Scale the samples with the volume
        scaled_volume = volume / 100
        scaled_audio = scaled_volume * samples_float

        # Clip the values to make sure they're in the valid range for paFloat32
        clipped_audio = np.clip(scaled_audio, -1.0, 1.0)
        # Convert back to int16
        output_samples = (clipped_audio * 32768).astype(np.int16)
        output_bytes = output_samples.tobytes()

        return output_bytes

    def get_volume_value(self, text: str) -> float:
        pattern = r'volume="(\d+)"'
        match = re.search(pattern, text)

        return float(match.group(1))

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def construct_prosody_tag(self, text: str) -> str:
        properties = []

        # commenting this for now as we don't have ways to control rate and pitch without ssml
        rate = self.get_property("rate")
        if rate != "":
            properties.append(f'rate="{rate}"')
        #
        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')

        volume = self.get_property("volume")
        if volume != "":
            properties.append(f'volume="{volume}"')

        prosody_content = " ".join(properties)

        # text_with_tag = f'<prosody {property}="{volume_in_words}">{text}</prosody>'
        text_with_tag = f"<prosody {prosody_content}>{text}</prosody>"

        return text_with_tag

    @property
    def ssml(self) -> ElevenLabsSSMLRoot:
        return ElevenLabsSSMLRoot()

    def set_voice(self, voice_id: str, lang_id: str = None):
        """Updates the currently set voice ID."""
        super().set_voice(voice_id)
        self._voice = voice_id
        # NB: Lang doesnt do much for ElevenLabs
        self._lang = lang_id


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
            logging.info(f"[ElevenLabs.synth_to_bytestream] Synthesizing text: {text}")

            # Split the text into smaller segments (e.g., sentences) for incremental synthesis

            text_segments = self._split_text(str(text))
                
            for segment_idx, segment in enumerate(text_segments):             
                logging.info(f"Synthesizing segment {segment_idx}: {segment}")
                self.generated_audio, word_timings = self._client.synth(str(text), self._voice)
                self.set_timings(word_timings)
                
                audio_bytes = self.generated_audio

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
            "[ElevenLabs.speak_streamed] Starting speech synthesis and playback..."
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
                self.synth_to_bytestream(text, format=audio_format)
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
