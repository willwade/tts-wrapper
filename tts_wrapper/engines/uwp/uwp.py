from typing import Any, List
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from .client import UWPClient

class UWPTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: UWPClient) -> None:
        self._client = client

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text))

    def get_available_voices(self) -> List[str]:
        return self._client.get_voices()