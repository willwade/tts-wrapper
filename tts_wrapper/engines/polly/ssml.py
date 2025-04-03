from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class PollySSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()

    def add(self, text: str, clear: bool = False) -> "BaseSSMLRoot":
        """Add text to the SSML structure.

        Args:
            text: The text to add
            clear: Whether to clear existing content first

        Returns:
            self: Returns self for method chaining
        """
        if clear:
            self.clear_ssml()

        # Add the text as a simple text node without any special markup
        self._inner.add(text)

        return self

    def add_pause(self, duration_ms: int) -> "BaseSSMLRoot":
        """Add a pause of the specified duration.

        Args:
            duration_ms: Duration of the pause in milliseconds

        Returns:
            self: Returns self for method chaining
        """
        # Convert milliseconds to seconds for SSML
        duration_s = duration_ms / 1000.0
        break_tag = f'<break time="{duration_s}s"/>'
        self._inner.add(SSMLNode("raw", children=[break_tag]))
        return self

    def clear_ssml(self) -> None:
        """Clear all SSML content."""
        self._inner.clear_ssml()
