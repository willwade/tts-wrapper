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

    def construct_prosody_tag(self, text:str ) -> str:
        properties = []
        rate = self.get_property("rate")
        if rate != "":            
            properties.append(f'rate="{rate}"')
        
        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')
    
        volume_in_number = self.get_property("volume")
        if volume_in_number != "":
            volume_in_words = self.mapped_to_predefined_word(volume_in_number)
            properties.append(f'volume="{volume_in_words}"')
        
        prosody_content = " ".join(properties)
        
        text_with_tag = f'<prosody {prosody_content}>{text}</prosody>'
        
        return text_with_tag

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

    