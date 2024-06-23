from typing import Any, List,Dict, Optional
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import ElevenLabsClient, ElevenLabsSSMLRoot
from ...engines.utils import estimate_word_timings  

class ElevenLabsTTS(AbstractTTS):
    def __init__(self, client: ElevenLabsClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This is crucial
        self._client = client
        self.audio_rate = 22050
        self.set_voice(voice or "yoZ06aMxZJJ28mfd3POQ", lang or "en-US")

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, "ElevenLabs API")
        if not self._voice:
            raise ValueError("Voice ID must be set before synthesizing speech.")
        word_timings = estimate_word_timings(str(text))
        self.set_timings(word_timings)
        # Get the audio from the ElevenLabs API
        return self._client.synth(str(text), self._voice, format)

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def construct_prosody_tag(self, property: str, text:str ) -> str:
        volume_in_number = self.get_property(property)
        volume_in_words = self.mapped_to_predefined_word(volume_in_number)
        text_with_tag = f'<prosody {property}="{volume_in_words}">{text}</prosody>'        
        return text_with_tag

    @property
    def ssml(self) -> ElevenLabsSSMLRoot:
        return ElevenLabsSSMLRoot()
        
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]
        
    def set_voice(self, voice_id: str, lang_id: str=None):
        """Updates the currently set voice ID."""
        super().set_voice(voice_id)
        self._voice = voice_id
        #NB: Lang doesnt do much for ElevenLabs
        self._lang = lang_id
 
    def mapped_to_predefined_word(self, volume: str) -> str:
        volume_in_float = float(volume)
        if volume_in_float == 0:
            return "silent"
        if 1 <= volume_in_float <= 20:
            return "x-soft"
        if 21 <= volume_in_float <= 40:
            return "soft"
        if 41 <= volume_in_float <= 60:
            return "medium"
        if 61 <= volume_in_float <= 80:
            return "loud"
        if 81 <= volume_in_float <= 100:
            return "x-loud"