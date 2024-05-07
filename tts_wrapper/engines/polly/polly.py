from typing import Any, List, Optional, Dict

from tts_wrapper.exceptions import UnsupportedFileFormat

from ...tts import AbstractTTS, FileFormat
from . import PollyClient, PollySSML


class PollyTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: PollyClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This is crucial
        self._client = client
        self.set_voice(voice or "Joanna", lang or "en-US")

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), self._voice, format)

    @property
    def ssml(self) -> PollySSML:
        return PollySSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Polly service."""
        return self._client.get_voices()
                
    def set_voice(self, voice_id: str, lang_id: str):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)  # Optionally manage voice at the AbstractTTS level if needed
        self._voice = voice_id
        self._lang = lang_id
