"""SSML handling for OpenAI TTS engine."""

from __future__ import annotations

import logging
from typing import Any

from tts_wrapper.ssml import AbstractSSMLNode, BaseSSMLRoot


class OpenAISSML(BaseSSMLRoot):
    """
    SSML implementation for OpenAI TTS.

    Since OpenAI doesn't support SSML, this class will strip SSML tags
    and return plain text.
    """

    def __init__(self) -> None:
        """Initialize the OpenAI SSML handler."""
        super().__init__()
        logging.debug("Initialized OpenAI SSML handler")

    def add(self, node: AbstractSSMLNode) -> AbstractSSMLNode:
        """Add a node to the SSML tree."""
        return super().add(node)

    def to_string(self) -> str:
        """
        Convert SSML to plain text by stripping all tags.

        OpenAI doesn't support SSML, so we convert to plain text.
        """
        # Use the __str__ method of AbstractSSMLNode to get plain text
        return str(self)

    def construct_prosody(
        self, text: str, rate: Any = None, volume: Any = None, pitch: Any = None, range: Any = None
    ) -> str:
        """
        Construct a prosody element.

        For OpenAI, we'll use the instructions parameter instead of SSML.
        This method returns plain text, but the client can use the parameters
        to construct appropriate instructions.

        Args:
            text: The text to apply prosody to
            rate: The speaking rate
            volume: The volume
            pitch: The pitch
            range: The pitch range

        Returns:
            Plain text without SSML tags
        """
        return text
