from typing import Any, List, Optional, Literal
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import SAPIClient
from . ssml import SAPISSML
from ..utils import process_wav
import io

class SAPITTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]

    def __init__(self, client: SAPIClient) -> None:
        super().__init__()
        self._client = client

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        """Set the TTS voice by ID and optionally set the language ID."""
        self._client.set_voice(voice_id)

    def synth_to_bytes(self, text, format='wav'):
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)

        if not self._is_ssml(str(text)):
            # Convert plain text to SSML
            text = f"<speak>{text}</speak>"

        result = self.client.synth_with_timings(str(text), self._voice, format)

        if isinstance(result, tuple) and len(result) == 2:
            self.generated_audio, word_timings = result
        else:
            self.generated_audio = result
            word_timings = []

        processed_timings = self._process_word_timings(word_timings)
        self.set_timings(processed_timings)
        return self.generated_audio

    def _process_word_timings(self, word_timings):
        # Implement logic to convert word timings to a suitable format
        processed_timings = []
        for timing in word_timings:
            # Process each timing to calculate end times, etc.
            start_time, length = timing
            end_time = start_time + length / 1000.0  # Convert length from ms to seconds
            word = ""  # Placeholder for the actual word (if retrievable)
            processed_timings.append((start_time, end_time, word))
        return processed_timings   
            
    @property
    def ssml(self) -> SAPISSML:
        return SAPISSML()

    def get_voices(self):
        return self._client.get_voices()
