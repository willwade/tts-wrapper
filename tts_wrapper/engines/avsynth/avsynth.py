import logging
from typing import Any, Optional, List

from tts_wrapper.tts import AbstractTTS, WordTiming

from .client import AVSynthClient
from .ssml import AVSynthSSML


class AVSynthTTS(AbstractTTS):
    """High-level TTS interface for AVSynth (macOS AVSpeechSynthesizer)."""

    def __init__(self, client: AVSynthClient, voice: Optional[str] = None) -> None:
        """Initialize the AVSynth TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self.audio_rate = 22050  # Lower audio rate for more natural speech
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.chunk_size = 1024
        self.timings: List[WordTiming] = []
        # Initialize properties with default string values
        self.properties = {
            "volume": "100",
            "rate": "medium",
            "pitch": "medium"
        }
        # Initialize SSML support
        self.ssml = AVSynthSSML()

    def _is_ssml(self, text: str) -> bool:
        """Check if the text contains SSML markup."""
        text = text.strip()
        return text.startswith("<speak>") and text.endswith("</speak>")

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to speech."""
        text = str(text)
        options = {}

        # Add voice if set and text is not SSML
        if self._voice and not self._is_ssml(text):
            options["voice"] = self._voice

        # Add any set properties (only for non-SSML text)
        if not self._is_ssml(text):
            for prop in ["rate", "volume", "pitch"]:
                value = self.get_property(prop)
                if value is not None:
                    options[prop] = str(value)

        # Call the client for synthesis
        audio_data, word_timings = self._client.synth(text, options)
        timings = self._process_word_timings(word_timings)
        self.set_timings(timings)
        return audio_data

    def speak_streamed(
        self,
        text: str,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
    ) -> None:
        """Synthesize text and stream it for playback."""
        try:
            # Get synthesis options
            options = {}
            if self._voice:
                options["voice"] = self._voice
            
            # Add properties
            for prop in ["rate", "volume", "pitch"]:
                value = self.get_property(prop)
                if value is not None:
                    options[prop] = str(value)

            # Get audio stream and word timings
            audio_stream, word_timings = self._client.synth_streaming(text, options)
            timings = self._process_word_timings(word_timings)
            self.set_timings(timings)

            # Load audio into player
            audio_bytes = b"".join(list(audio_stream))
            self.load_audio(audio_bytes)
            
            # Start playback
            self.play()

            # Save to file if requested
            if save_to_file_path:
                with open(save_to_file_path, "wb") as f:
                    f.write(audio_bytes)

        except Exception as e:
            logging.exception("Error in speak_streamed: %s", e)
            raise

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """Set the voice for synthesis."""
        self._voice = voice_id
        self._lang = lang

    def _process_word_timings(
        self, word_timings: list[dict]
    ) -> List[WordTiming]:
        """Convert word timings into the format (start_time, end_time, word)."""
        return [
            (timing["start"], timing["end"], timing["word"])
            for timing in word_timings
        ]