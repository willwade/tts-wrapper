from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class PlayHTSSMLNode(SSMLNode):
    """SSML node implementation for Play.HT."""

    def __str__(self) -> str:
        """
        Play.HT doesn't support SSML, so we just return the text content.
        """
        return "".join(str(c) for c in self._children)


class PlayHTSSML(BaseSSMLRoot):
    """SSML root implementation for Play.HT."""

    def __init__(self) -> None:
        super().__init__()
        self._inner = PlayHTSSMLNode("speak")

    def __str__(self) -> str:
        return str(self._inner)

    def clear_ssml(self) -> None:
        self._inner.clear_ssml() 