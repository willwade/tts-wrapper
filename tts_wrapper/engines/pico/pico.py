from typing import Any, List, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import PicoClient


class PicoTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: PicoClient, voice: Optional[str] = None) -> None:
        self._client = client
        self._voice = voice or "en-US"

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), self._voice)

    def construct_prosody_tag(self, text:str ) -> str:
        pass