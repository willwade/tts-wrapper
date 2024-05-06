from typing import Any, List, Optional

from tts_wrapper.exceptions import UnsupportedFileFormat

from ...tts import AbstractTTS, FileFormat
from . import PollyClient, PollySSML


class PollyTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(
        self,
        client: PollyClient,
        voice: Optional[str] = None,
    ) -> None:
        self._client = client
        self._voice = voice or "Joanna"

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), self._voice, format)

    @property
    def ssml(self) -> PollySSML:
        return PollySSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Polly service."""
        return self._client.get_voices()