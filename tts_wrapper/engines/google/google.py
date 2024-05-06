from typing import Any, List, Dict, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import GoogleClient, GoogleSSML


class GoogleTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(
        self,
        client: GoogleClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        """
        @param credentials: The path to the json file that contains the credentials.
        """
        self._client = client
        self._lang = lang or "en-US"
        self._voice = voice or "en-US-Wavenet-C"

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), self._voice, self._lang, format)

    @property
    def ssml(self) -> GoogleSSML:
        return GoogleSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Google TTS service."""
        return self._client.get_voices()