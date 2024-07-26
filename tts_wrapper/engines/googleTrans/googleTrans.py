# engine.py

from typing import Any, List, Optional, Dict
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import googleTransClient, googleTransSSML
import logging

class googleTransTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["mp3"]

    def __init__(self, client: googleTransClient):
        super().__init__()
        self.client = client
        self.audio_rate = 24000

    def get_voices(self):
        return self.client.get_voices()

    def synth_to_bytes(self, text, format='mp3'):
        return self.client.synth(text, format)

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        super().set_voice(voice_id, lang_id)
        self.client.set_voice(voice_id)

    def construct_prosody_tag(self, text: str) -> str:
        # Implement SSML prosody tag construction if needed
        return text
