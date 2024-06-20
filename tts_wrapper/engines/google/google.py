from typing import Any, List, Dict, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import GoogleClient, GoogleSSML


class GoogleTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: GoogleClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This ensures that all initialization in AbstractTTS is done
        self._client = client
        self._lang = lang or "en-US"
        self._voice = voice or "en-US-Wavenet-C"

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
        result = self._client.synth(str(text), self._voice, self._lang, format, include_timepoints=True)
        timings = [(float(tp['timeSeconds']), tp['markName']) for tp in result.get("timepoints", [])]
        self.set_timings(timings)
        return result["audio_content"]

        
    @property
    def ssml(self) -> GoogleSSML:
        return GoogleSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Google TTS service."""
        return self._client.get_voices()

    def construct_prosody_tag(self, property: str, text:str ) -> str:
        volume = self.get_property(property)
        text_with_tag = f'<prosody {property}="{volume}">{text}</prosody>'        
        return text_with_tag