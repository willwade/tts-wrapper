from typing import Any, List, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import WatsonClient, WatsonSSML


class WatsonTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(
        self,
        client: WatsonClient,
        voice: Optional[str] = None,
    ) -> None:
        self._client = client
        self._voice = voice or "en-US_LisaV3Voice"

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), self._voice, format)

    @property
    def ssml(self) -> WatsonSSML:
        return WatsonSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Watson TTS service."""
        return self._client.get_voices()