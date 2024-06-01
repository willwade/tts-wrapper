from typing import Any, List, Optional, Dict

from tts_wrapper.exceptions import UnsupportedFileFormat

from ...tts import AbstractTTS, FileFormat
from . import PiperClient, PiperSSML
import threading
import time

class PiperTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: PiperClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self._voices = self.get_voices()
        self.set_voice(voice or "Joanna", lang or "en-US")
        self.audio_rate = 16000

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        return self._client.synth(str(text), format)

    @property
    def ssml(self) -> PiperSSML:
        return PiperSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str):
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id
