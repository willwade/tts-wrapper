from typing import Any, List

from tts_wrapper.tts import AbstractTTS, FileFormat

from .client import UWPClient


class UWPTTS(AbstractTTS):
    def __init__(self, client: UWPClient) -> None:
        super().__init__()
        self._client = client

    def synth_to_bytes(self, text: Any, format: FileFormat) -> bytes:
        ssml = UWPSsml(str(text)).to_ssml()
        audio_bytes = self._client.synth(ssml)

        if audio_bytes[:4] == b"RIFF":
            audio_bytes = self._strip_wav_header(audio_bytes)

        return audio_bytes

    def get_voices(self) -> List[str]:
        return self._client.get_voices()

    def construct_prosody_tag(self, text: str) -> str:
        pass
