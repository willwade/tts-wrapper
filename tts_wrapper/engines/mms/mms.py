from typing import Any, List, Dict, Optional
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MMSClient, MMSSSML

class MMSTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]  # MMS only supports WAV format

    def __init__(self, client: MMSClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self._lang = lang or "eng"  # Default to English
        self._voice = voice or self._lang  # Use lang as voice ID for MMS
        self.audio_rate = 16000

    def construct_prosody_tag(self, text:str ) -> str:
        pass

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        if not self._is_ssml(text):
            text = self.ssml.add(text)
        
        result = self._client.synth(str(text), self._voice, self._lang, format)
        self.audio_bytes = result["audio_content"]
        return self.audio_bytes

    def synth(self, text: Any, output_file: str, format: Optional[FileFormat] = "wav") -> None:
        if format.lower() != "wav":
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        audio_bytes = self.synth_to_bytes(text, format)
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    @property
    def ssml(self) -> MMSSSML:
        return MMSSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()