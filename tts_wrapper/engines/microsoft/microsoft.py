from typing import Any, List,Dict, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MicrosoftClient, MicrosoftSSML


class MicrosoftTTS(AbstractTTS):
    def __init__(self, client: MicrosoftClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This is crucial
        self._client = client
        self.set_voice(voice or "en-US-JessaNeural", lang or "en-US")

    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:    
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), format)

    @property
    def ssml(self) -> MicrosoftSSML:
        return MicrosoftSSML(self._lang, self._voice)

    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service."""
        return self._client.get_available_voices()
        
    def set_voice(self, voice_id: str, lang_id: str):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)  # Optionally manage voice at the AbstractTTS level if needed
        self._voice = voice_id
        self._lang = lang_id
        self.ssml.set_voice(voice_id, lang_id) 