from typing import Any, List, Optional, Dict, Tuple
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import PollyClient, PollySSML

class PollyTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(self, client: PollyClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self.set_voice(voice or "Joanna", lang or "en-US")
        self.audio_rate = 16000

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))
        
        self.generated_audio, word_timings = self._client.synth_with_marks(str(text), self._voice, format)
        
        # Process word timings to include end times
        processed_timings = self._process_word_timings(word_timings)
        self.set_timings(processed_timings)
        return self.generated_audio

    def _process_word_timings(self, word_timings: List[Tuple[float, str]]) -> List[Tuple[float, float, str]]:
        processed_timings = []
        audio_duration = self.get_audio_duration()
        
        for i, (start, word) in enumerate(word_timings):
            if i < len(word_timings) - 1:
                end = word_timings[i+1][0]
            else:
                end = min(start + 0.5, audio_duration)  # Use the lesser of 0.5s or remaining audio duration
            processed_timings.append((start, end, word))
        
        return processed_timings

    def get_audio_duration(self) -> float:
        if hasattr(self, 'generated_audio'):
            return len(self.generated_audio) / 2 / self.audio_rate
        return 0.0

    @property
    def ssml(self) -> PollySSML:
        return PollySSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()
                
    def set_voice(self, voice_id: str, lang_id: str):
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id

    def construct_prosody_tag(self, text:str ) -> str:
        properties = []
        
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