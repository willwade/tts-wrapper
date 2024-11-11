# engine.py

from typing import Any, Optional

from tts_wrapper.tts import AbstractTTS

from . import GoogleTransClient


class GoogleTransTTS(AbstractTTS):
    def __init__(self, client: GoogleTransClient) -> None:
        super().__init__()
        self.client = client
        self.audio_rate = 24000

    def get_voices(self):
        return self.client.get_voices()

    def synth_to_bytes(self, text: Any) -> bytes:
        """Transforms text to raw PCM audio bytes.

        The output is always raw PCM data (int16) with no headers.
        """

        # Get the MP3 data from GoogleTransClient
        mp3_data = self.client.synth(text)

        # Convert the MP3 data to raw PCM using the utility method
        return self._convert_mp3_to_pcm(mp3_data)


    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        super().set_voice(voice_id, lang_id)
        self.client.set_voice(voice_id)

    def construct_prosody_tag(self, text: str) -> str:
        # Implement SSML prosody tag construction if needed
        return text
