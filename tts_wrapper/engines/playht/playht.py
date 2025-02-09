from typing import Any, Optional

from tts_wrapper.engines.utils import estimate_word_timings
from tts_wrapper.tts import AbstractTTS

from .client import PlayHTClient
from .ssml import PlayHTSSML


class PlayHTTTS(AbstractTTS):
    """High-level TTS interface for Play.HT."""

    def __init__(
        self,
        client: PlayHTClient,
        voice: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> None:
        """Initialize the Play.HT TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self.audio_rate = 24000  # Play.HT uses 24kHz sample rate
        self._ssml = PlayHTSSML()

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to speech."""
        text = str(text)
        options = {}

        # Strip SSML tags if present - PlayHTSSML will return just the text content
        if text.startswith('<speak>') and text.endswith('</speak>'):
            text = str(text)  # PlayHTSSML.__str__ strips SSML tags

        # Add voice if set
        if self._voice:
            options["voice"] = self._voice

        # Add any set properties
        for prop in ["speed", "quality", "voice_engine"]:
            value = self.get_property(prop)
            if value is not None:
                options[prop] = str(value)

        # Estimate word timings since Play.HT doesn't provide them
        timings = estimate_word_timings(text)
        self.set_timings(timings)  # type: ignore

        # Call the client for synthesis
        return self._client.synth(text, options)

    @property
    def ssml(self) -> PlayHTSSML:
        """Returns an instance of the PlayHTSSML class for constructing SSML strings."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Retrieves a list of available voices from the Play.HT service."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Sets the voice for the TTS engine."""
        super().set_voice(voice_id, lang_id or "en-US")
        self._voice = voice_id

    def construct_prosody_tag(self, text: str) -> str:
        """
        Play.HT doesn't support SSML, so we just return the text as is.
        The properties are handled in synth_to_bytes via the options dict.
        """
        return text 