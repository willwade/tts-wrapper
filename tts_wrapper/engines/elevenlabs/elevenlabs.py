from typing import Any, List, Dict
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import ElevenLabsClient

class ElevenLabsTTS(AbstractTTS):
    def __init__(self, client: ElevenLabsClient):
        super().__init__()
        self.client = client

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(f"Format {format} is not supported")
        return self.client.synth(text, self.voice_id, format)  # Ensure `voice_id` is properly managed

    def get_voices(self) -> List[Dict[str, Any]]:
        return self.client.get_voices()

    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["mp3"]  # Assuming only MP3 is supported based on your setup

    def set_voice(self, voice_id: str):
        """Updates the currently set voice ID."""
        self.voice_id = voice_id
