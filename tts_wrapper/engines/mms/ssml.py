from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class MMSSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()
        self._inner = SSMLNode("speak")  # The tag is irrelevant but kept for compatibility

    def __str__(self) -> str:
        # MMS doesn't support SSML, so we just return the text content
        return "".join(str(c) for c in self._inner._children)

    def clear_ssml(self) -> None:
        pass
