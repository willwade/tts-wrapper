from tts_wrapper.ssml import BaseSSMLRoot


class eSpeakSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()

    def add(self, text: str) -> str:
        """
        Wraps input text with SSML tags and ensures it's usable by the TTS engine.

        :param text: The text to wrap with SSML tags.
        :return: The complete SSML string.
        """
        # Clear existing SSML if necessary
        self.clear_ssml()

        # Add the text as a child node to the root SSMLNode
        super().add(text)

        # Return the complete SSML string
        return str(self)

    def clear_ssml(self) -> None:
        """Clears all child nodes from the SSML root."""
        self._inner.clear_ssml()