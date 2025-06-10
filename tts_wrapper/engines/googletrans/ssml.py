from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class GoogleTransSSMLNode(SSMLNode):
    def __str__(self) -> str:
        # Override to generate only the inner content without the actual SSML tags
        return "".join(str(c) for c in self._children)


class GoogleTransSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()
        self._inner = GoogleTransSSMLNode(
            "speak",
        )  # The tag is irrelevant but kept for compatibility

    def __str__(self) -> str:
        # Use the overridden __str__ method of GoogleTransSSMLNode
        return str(self._inner)

    def clear_ssml(self) -> None:
        self._inner.clear_ssml()
