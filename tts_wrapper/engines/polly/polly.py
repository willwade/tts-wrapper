from typing import Any, List, Optional, Dict

from tts_wrapper.exceptions import UnsupportedFileFormat

from ...tts import AbstractTTS, FileFormat
from . import PollyClient, PollySSML
import threading
import time

class PollyTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: PollyClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This is crucial
        self._client = client
        self.set_voice(voice or "Joanna", lang or "en-US")
        self.audio_rate = 16000

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))
        word_timings = self._client.get_speech_marks(str(text), self._voice)
        self.set_timings(word_timings)
        return self._client.synth(str(text), self._voice, format)


    @property
    def ssml(self) -> PollySSML:
        return PollySSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Polly service."""
        return self._client.get_voices()
                
    def set_voice(self, voice_id: str, lang_id: str):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)  # Optionally manage voice at the AbstractTTS level if needed
        self._voice = voice_id
        self._lang = lang_id

    def construct_prosody_tag(self, text:str ) -> str:
        properties = []
        
        #commenting this for now as currently we don't have ways to control rate and pitch without ssml
        #rate = self.get_property("rate")
        #if rate != "":            
        #    properties.append(f'rate="{rate}"')
        #
        #pitch = self.get_property("pitch")
        #if pitch != "":
        #    properties.append(f'pitch="{pitch}"')
    
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