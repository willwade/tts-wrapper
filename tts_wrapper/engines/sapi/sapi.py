from typing import Any, List, Optional, Literal
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import SAPIClient
from . ssml import SAPISSML

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
        

    def synth_to_bytes(self, text: Any, format: Optional[Literal['wav', 'mp3']] = None) -> bytes:
        # Default format to 'wav' if not specified
        if format is None:
            format = 'wav'
        
        # Ensure the requested format is supported
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)

        return self._client.synth(str(text))

        
    @property
    def ssml(self) -> SAPISSML:
        return SAPISSML()

    def get_voices(self):
        return self._client.get_voices()

    def get_property(self, property_name):
        """Get the value of a TTS property."""
        return self._client.get_property(property_name)

    def set_property(self, property_name, value):
        """Set the value of a TTS property."""
        return self._client.set_property(property_name,value)


    def construct_prosody_tag(self, text: str) -> str:
        """Constructs a prosody tag for consistency."""
        properties = []

        volume_in_number = self.get_property("volume")
        if volume_in_number is not None:
            volume_in_words = self._map_volume_to_predefined_word(volume_in_number)
            properties.append(f'volume="{volume_in_words}"')

        rate = self.get_property("rate")
        if rate is not None:
            properties.append(f'rate="{rate}"')

        # Since pyttsx3 does not support pitch, we just append the pitch for consistency
        pitch = self.get_property("pitch")
        if pitch is not None:
            properties.append(f'pitch="{pitch}"')

        prosody_content = " ".join(properties)
        text_with_tag = f'<prosody {prosody_content}>{text}</prosody>'

        return text_with_tag

    def _map_volume_to_predefined_word(self, volume: str) -> str:
        """Maps volume to predefined descriptive terms."""
        volume_in_float = float(volume)
        if volume_in_float == 0:
            return "silent"
        elif 1 <= volume_in_float <= 20:
            return "x-soft"
        elif 21 <= volume_in_float <= 40:
            return "soft"
        elif 41 <= volume_in_float <= 60:
            return "medium"
        elif 61 <= volume_in_float <= 80:
            return "loud"
        elif 81 <= volume_in_float <= 100:
            return "x-loud"
        else:
            return "medium"
