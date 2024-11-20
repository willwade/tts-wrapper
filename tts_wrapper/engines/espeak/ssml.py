from tts_wrapper.ssml import BaseSSMLRoot
from tts_wrapper.ssml import SSMLNode


class eSpeakSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()

    def add(self, text: str, clear: bool = False) -> str:
        """
        Wraps input text with SSML tags and ensures it's usable by the TTS engine.

        :param text: The text to wrap with SSML tags.
        :param clear: If True, clears existing SSML structure before adding.
        :return: The complete SSML string.
        """
        if clear:
            self.clear_ssml()

        if isinstance(text, str) and "<prosody" in text:
            self._inner.add(SSMLNode("raw", children=[text]))
        else:
            self._inner.add(text)

        return str(self)

    def clear_ssml(self) -> None:
        """Clears all child nodes from the SSML root."""
        self._inner.clear_ssml()