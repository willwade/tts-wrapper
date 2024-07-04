from typing import Any, List, Optional, Dict, Tuple
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
        self.generated_audio = None
        self.audio_format = None

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        if not self._is_ssml(str(text)):
            text = self.ssml.add(str(text))
        
        try:
            self.generated_audio = self._client.synth_with_timings(str(text), self._voice, format)
            self.audio_format = format
            
            processed_timings = self._process_word_timings(self._client.word_timings)
            self.set_timings(processed_timings)
            
            return self.generated_audio
        except Exception as e:
            logging.error(f"Error in synth_to_bytes: {e}")
            raise

    def _process_word_timings(self, word_timings: List[Tuple[float, str]]) -> List[Tuple[float, float, str]]:
        processed_timings = []
        audio_duration = self.get_audio_duration()
        
        for i, (start_time, word) in enumerate(word_timings):
            if i < len(word_timings) - 1:
                end_time = word_timings[i+1][0]
            else:
                end_time = min(start_time + 0.5, audio_duration)  # Use the lesser of 0.5s or remaining audio duration
            
            processed_timings.append((start_time, end_time, word))
        
        return processed_timings

    def get_audio_duration(self) -> float:
        if self.generated_audio and self.audio_format:
            return self._client.get_audio_duration(self.generated_audio, self.audio_format)
        return 0.0

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

    def construct_prosody_tag(self, text:str ) -> str:
        pass