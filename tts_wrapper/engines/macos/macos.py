from typing import Any, List, Optional, Literal
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from .client import MacOSClient
from .ssml import MacOSSSML
from ..utils import process_wav
import io

class MacOSTTS(AbstractTTS):
    def __init__(self, client: MacOSClient):
        super().__init__()
        self.client = client
        self._voice = None

    def supported_formats(cls) -> List[FileFormat]:
        return ["aiff"]
    
    def get_voices(self):
        return self.client.get_voices()

    def set_voice(self, voice_id):
        self._voice = voice_id
        self.client.set_voice(voice_id)

    @property
    def ssml(self) -> MacOSSSML:
        return MacOSSSML()
    
    def _is_ssml(self, text):
        return text.startswith("<speak>") and text.endswith("</speak>")

    def synth_to_bytes(self, text, format='wav'):
        # if format not in self.supported_formats():
        #     raise UnsupportedFileFormat(format, self.__class__.__name__)
        result = self.client.synth_with_timings(text, self._voice, format)

        if isinstance(result, tuple) and len(result) == 2:
            self.generated_audio, word_timings = result
            print("Word timings: ", word_timings)
        else:
            self.generated_audio = result
            word_timings = []

        processed_timings = self._process_word_timings(word_timings)
        self.set_timings(processed_timings)
        return self.generated_audio

    def _process_word_timings(self, word_timings):
        processed_timings = []
        for timing in word_timings:
            start_time, length = timing
            end_time = start_time + length / 1000.0
            word = ""  # Placeholder for actual word, if retrievable
            processed_timings.append((start_time, end_time, word))
        return processed_timings

    def set_property(self, name, value):
        if name == 'rate':
            self.client.set_rate(value)
        elif name == 'volume':
            self.client.set_volume(value)

    def construct_prosody_tag(self, text, rate="medium"):
        # This method can be expanded to construct proper SSML with prosody tags
        # If rate affects how it should be synthesized, adjust accordingly
        return f'<prosody rate="{rate}">{text}</prosody>'
    
