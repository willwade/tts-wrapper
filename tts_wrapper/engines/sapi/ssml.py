from typing import Optional

from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class SAPISSML(BaseSSMLRoot):
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

        if isinstance(text, str) and "<" in text:  # Treat as raw SSML
            self._inner.add(SSMLNode("raw", children=[text]))
        else:
            self._inner.add(SSMLNode("text", children=[text]))

        return str(self)

    def construct_prosody(self, text: str, **kwargs) -> str:
        """
        Constructs a <prosody> tag with specified attributes.
        :param text: The text to wrap with the prosody tag.
        :param kwargs: Attributes for the prosody tag (rate, pitch, volume, range).
        :return: The prosody-wrapped text.
        """
        attributes = [f'{key}="{value}"' for key, value in kwargs.items() if value]
        attr_str = " ".join(attributes)
        return f"<prosody {attr_str}>{text}</prosody>"

    def construct_say_as(
        self, text: str, interpret_as: str, format: Optional[str] = None
    ) -> str:
        """
        Constructs a <say-as> tag with interpret-as and optional format.
        :param text: The text to wrap.
        :param interpret_as: Interpretation type (e.g., characters, digits).
        :param format: Optional format for the interpretation.
        :return: The say-as wrapped text.
        """
        format_attr = f' format="{format}"' if format else ""
        return f'<say-as interpret-as="{interpret_as}"{format_attr}>{text}</say-as>'

    def construct_emphasis(self, text: str, level: str = "moderate") -> str:
        """
        Constructs an <emphasis> tag.
        :param text: The text to emphasize.
        :param level: Level of emphasis (e.g., none, moderate, strong).
        :return: The emphasis-wrapped text.
        """
        return f'<emphasis level="{level}">{text}</emphasis>'

    def construct_break(
        self, strength: Optional[str] = None, time: Optional[str] = None
    ) -> str:
        """
        Constructs a <break> tag.
        :param strength: Break strength (e.g., none, x-strong).
        :param time: Break time in milliseconds.
        :return: The break tag.
        """
        if strength:
            return f'<break strength="{strength}"/>'
        if time:
            return f'<break time="{time}ms"/>'
        return "<break/>"

    def clear_ssml(self) -> None:
        """Clears all child nodes from the SSML root."""
        self._inner.clear_ssml()
