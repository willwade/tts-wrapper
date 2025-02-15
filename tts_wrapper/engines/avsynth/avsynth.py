from typing import Optional, Any, Generator

from tts_wrapper.tts import AbstractTTS
from tts_wrapper.engines.avsynth.ssml import AVSynthSSML


class AVSynthTTS(AbstractTTS):
    """High-level TTS interface for AVSynth (macOS AVSpeechSynthesizer)."""

    def __init__(self, client=None, voice: Optional[str] = None) -> None:
        """Initialize the AVSynth TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self._ssml = AVSynthSSML()
        self._properties: dict[str, str] = {
            "rate": "medium",
            "volume": "100",
            "pitch": "medium"
        }
        self.audio_rate = 22050  # Lower audio rate for more natural speech
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.chunk_size = 1024

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

        # Call the client for synthesis and get native word timings
        audio_data, word_timings = self._client.synth(text, options)
        
        # Set word timings directly from AVSpeechSynthesizer
        self.set_timings([
            (timing["start"], timing["end"], timing["word"])
            for timing in word_timings
        ])
        
        return audio_data

    def synth_to_bytestream(
        self, text: Any
    ) -> Generator[bytes, None, None]:
        """
        Synthesize text to a stream of audio bytes.
        
        This method uses the native streaming capabilities of AVSpeechSynthesizer
        for more efficient real-time audio generation.
        
        Args:
            text: The text to synthesize
            
        Yields:
            Audio data chunks as they are generated
        """
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

        # Get the streaming generator and native word timings
        generator, word_timings = self._client.synth_streaming(text, options)
        
        # Set word timings directly from AVSpeechSynthesizer
        self.set_timings([
            (timing["start"], timing["end"], timing["word"])
            for timing in word_timings
        ])
        
        # Yield audio chunks from the generator
        for chunk in generator:
            # Ensure chunk size is a multiple of 2 for int16 samples
            if len(chunk) % 2 != 0:
                chunk = chunk[:-1]
            yield chunk

    @property
    def ssml(self) -> AVSynthSSML:
        """Get the SSML handler."""
        return self._ssml

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """Set the voice for synthesis."""
        super().set_voice(voice_id, lang)
        self._voice = voice_id
        self._lang = lang

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_voices()