from typing import Any, Optional
from collections.abc import Generator

from tts_wrapper.tts import AbstractTTS

from . import eSpeakClient
from .ssml import eSpeakSSML
import logging

class eSpeakTTS(AbstractTTS):
    """High-level TTS interface for eSpeak."""

    def __init__(self, client: eSpeakClient, lang: Optional[str] = None, voice: Optional[str] = None) -> None:
        """Initialize the eSpeak TTS interface."""
        super().__init__()
        self._client = client
        self.set_voice(voice or "gmw/en")
        self._ssml = eSpeakSSML()
        self.audio_rate = 22050
        self.generated_audio = bytearray()
        self.word_timings = []

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to audio bytes."""
        logging.debug("Synthesizing text to audio")
        self.generated_audio = bytearray()  # Clear audio buffer before synthesis
        self.word_timings = []  # Clear word timings

        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))

        # Perform synthesis and retrieve the audio stream and timings
        audio_stream, word_timings = self._client._espeak.speak_streamed(str(text), ssml=self._is_ssml(str(text)))

        # Read the audio stream from the queue
        while True:
            audio_chunk = audio_stream.get()
            if audio_chunk is None:  # End of stream
                break
            self.generated_audio.extend(audio_chunk)

        # Process word timings
        self.word_timings = self._process_word_timings(word_timings, str(text))
        self.set_timings(self.word_timings)

        # Check and remove WAV header if necessary
        if self.generated_audio[:4] == b"RIFF":
            self.generated_audio = self._strip_wav_header(self.generated_audio)

        return bytes(self.generated_audio)


    def _process_word_timings(self, word_timings: list[dict], input_text: str) -> list[tuple[float, float, str]]:
        """Process raw word timings into start-end intervals."""
        processed_timings = []
        audio_duration = self.get_audio_duration()

        for i, word_info in enumerate(word_timings):
            start_time = word_info["start_time"]
            text_position = word_info["text_position"]
            length = word_info["length"]

            # Extract the word text using text_position and length
            word_text = input_text[text_position : text_position + length]

            # Determine the end time
            end_time = (
                word_timings[i + 1]["start_time"] if i + 1 < len(word_timings) else audio_duration
            )
            processed_timings.append((start_time, end_time, word_text))

        return processed_timings

    def get_audio_duration(self) -> float:
        """Get the duration of the generated audio."""
        return len(self.generated_audio) / (2 * self.audio_rate)

    def synth_to_bytestream(
        self, text: Any, format: Optional[str] = "wav"
    ) -> Generator[bytes, None, None]:
        """
        Synthesizes text to an in-memory bytestream in the specified audio format.
        Yields audio data chunks as they are generated.

        :param text: The text to synthesize.
        :param format: The desired audio format (e.g., 'wav'). Defaults to 'wav'.
        :return: A generator yielding bytes objects containing audio data.
        """
        try:
            logging.debug("Starting synth_to_bytestream...")
            self.generated_audio = bytearray()  # Clear previous audio
            self.word_timings = []  # Clear previous timings

            # Prepare the text for synthesis
            if not self._is_ssml(str(text)):
                text = self.ssml.add(str(text))

            # Use eSpeak's streaming functionality
            audio_stream, word_timings = self._client._espeak.speak_streamed(str(text), ssml=self._is_ssml(str(text)))

            # Store word timings for later use
            self.word_timings = self._process_word_timings(word_timings, str(text))
            self.set_timings(self.word_timings)

            # Process audio chunks from the stream
            for audio_chunk in iter(audio_stream.get, None):
                if format == "wav":
                    yield self._format_as_wav(audio_chunk)
                else:
                    # Handle other formats if necessary (e.g., mp3, flac)
                    raise NotImplementedError(f"Format {format} not supported yet.")

        except Exception as e:
            logging.exception("Error in synth_to_bytestream: %s", e)
            raise

    @property
    def ssml(self) -> eSpeakSSML:
        """Return the SSML handler."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Return available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Set the voice and language."""
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or "en"
