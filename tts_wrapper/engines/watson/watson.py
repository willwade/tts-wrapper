from typing import Any, List, Optional, Dict

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import WatsonClient, WatsonSSML


class WatsonTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: WatsonClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__() 
        self._client = client
        self._voice = voice or "en-US_LisaV3Voice"
        self.audio_rate = 22050
        self.word_timings = []


    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))
        self.word_timings.clear()
        audio_data = self._client.synth_with_timings(str(text), self._voice, format)
        self.set_timings(self._client.word_timings)
        return audio_data

    @property
    def ssml(self) -> WatsonSSML:
        return WatsonSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Watson TTS service."""
        return self._client.get_voices()    
            
    def set_voice(self, voice_id: str, lang_id: str):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)  # Optionally manage voice at the AbstractTTS level if needed
        self._voice = voice_id
        self._lang = lang_id
