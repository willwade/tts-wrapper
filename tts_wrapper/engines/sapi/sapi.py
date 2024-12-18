from tts_wrapper.tts import AbstractTTS
from .client import SAPIClient
from collections.abc import Generator
from typing import Any, Callable, NoReturn, Union
from .ssml import SAPISSML
import sys

if sys.platform == "win32":
    try:
        import comtypes.client
    except ImportError:
        raise ImportError("comtypes is required for SAPI support. Install it with `pip install py3-tts-wrapper[sapi]`.")
else:
    raise ImportError("SAPI is only supported on Windows.")


class SAPIEngine(AbstractTTS):
    def __init__(self, sapi_version: int = 5, voice: str = None) -> None:
        super().__init__()
        self.client = SAPIClient(sapi_version=sapi_version)
        self.voice = voice or "default"

    def synth_to_bytes(self, text: str) -> bytes:
        audio, word_timings = self.client.synth(text)
        self.word_timings = word_timings
        self.set_timings(word_timings)

        return audio

    def synth_to_bytestream(self, text: str) -> Generator[bytes, None, None]:
        audio_queue, word_timings = self.client.synth_streaming(text)
        self.word_timings = word_timings
        while True:
            chunk = audio_queue.get()
            if chunk is None:
                break
            yield chunk

    def set_voice(self, voice_id: str) -> None:
        self.client.set_voice(voice_id)

    def get_voices(self) -> list[dict[str, Any]]:
        return self.client.get_voices()

    def set_property(self, property_name: str, value: Union[str, float]) -> None:
        self.client.set_property(property_name, value)