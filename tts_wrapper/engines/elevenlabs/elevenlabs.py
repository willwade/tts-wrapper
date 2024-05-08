from typing import Any, List,Dict, Optional
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import ElevenLabsClient, ElevenLabsSSMLRoot


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
        
        # Get the audio from the ElevenLabs API
        return self._client.synth(str(text), self._voice, format)

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

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
 
