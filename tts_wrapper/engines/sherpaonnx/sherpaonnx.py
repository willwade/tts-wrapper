# engine.py

from typing import Any, List, Optional, Dict
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import SherpaOnnxClient, SherpaOnnxSSML
from ...engines.utils import estimate_word_timings  # Import the timing estimation function
import logging

class SherpaOnnxTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: SherpaOnnxClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        if voice:
            self.set_voice(voice, lang)
        self.audio_rate = None

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        super().set_voice(voice_id, lang_id)
        self._client.set_voice(voice_id)

    def synth_to_bytes(self, text: str, format: Optional[FileFormat] = "wav") -> bytes:
        logging.info(f"Synthesizing text: {text}")
        audio_bytes, sample_rate = self._client.synth(text)
        # I think we need to get length of audio.. 
#         word_timings = estimate_word_timings(str(text))
#         self.set_timings(word_timings)
        logging.info(f"Audio bytes length: {len(audio_bytes)}, Sample rate: {sample_rate}")
        self.audio_rate = sample_rate
        return audio_bytes

    def construct_prosody_tag(self, text: str) -> str:
        # Implement SSML prosody tag construction if needed
        return text
