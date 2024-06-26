from typing import Any, List

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import SAPIClient


class SAPITTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: SAPIClient) -> None:
        self._client = client

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text))

    def construct_prosody_tag(self, text:str ) -> str:
        pass