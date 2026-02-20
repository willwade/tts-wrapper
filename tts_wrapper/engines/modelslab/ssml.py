"""SSML handling for ModelsLab TTS engine."""

from __future__ import annotations

from typing import Any

from tts_wrapper.ssml import AbstractSSMLNode, BaseSSMLRoot


class ModelsLabSSML(BaseSSMLRoot):
    """
    SSML implementation for ModelsLab TTS.

    ModelsLab doesn't support SSML, so this class strips SSML tags
    and returns plain text.
    """

    def __init__(self) -> None:
        """Initialize the ModelsLab SSML handler."""
        super().__init__()

    def add(self, node: AbstractSSMLNode | str) -> AbstractSSMLNode:
        """Add a node to the SSML tree."""
        return super().add(node)

    def add_text(self, text: str) -> AbstractSSMLNode:
        """Add a text node to the SSML tree."""
        return self.add(text)

    def to_string(self) -> str:
        """Convert SSML to plain text by stripping all tags."""
        return str(self)

    def clear_ssml(self) -> None:
        """Clear all SSML nodes."""
        self.children: list[AbstractSSMLNode] = []

    def construct_prosody(
        self,
        text: str,
        rate: Any = None,
        volume: Any = None,
        pitch: Any = None,
        range: Any = None,
    ) -> str:
        """
        Construct a prosody element.

        ModelsLab uses the speed parameter instead of SSML prosody.
        Returns plain text; rate is handled via the speed parameter in the client.
        """
        _ = rate, volume, pitch, range
        return text
