"""Google SSML implementation."""

from __future__ import annotations

from .ssml_root import BaseSSMLRoot


class GoogleSSML(BaseSSMLRoot):
    """Google SSML implementation.

    This class provides SSML functionality for Google TTS.
    """

    def __init__(self) -> None:
        """Initialize the GoogleSSML class."""
        super().__init__()
        self.ssml_version = "1.0"
        self.ssml_namespace = "http://www.w3.org/2001/10/synthesis"
        self.ssml_lang = "en-US"
