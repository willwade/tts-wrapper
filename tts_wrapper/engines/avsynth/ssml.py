import logging
from xml.etree import ElementTree as ET

class AVSpeechSSML:
    """SSML parser and generator for AVSpeech."""

    def __init__(self):
        logging.debug("AVSpeechSSML initialized")

    def parse(self, ssml: str) -> str:
        """Parse SSML to plain text, preserving basic semantics."""
        try:
            root = ET.fromstring(ssml)
            return self._parse_element(root)
        except ET.ParseError:
            logging.warning("Invalid SSML. Returning plain text.")
            return ssml

    def _parse_element(self, element) -> str:
        """Recursively parse an XML element into plain text."""
        if element.tag in {"speak", "voice", "prosody"}:
            return " ".join(self._parse_element(child) for child in element)
        if element.tag == "break":
            return "\n"  # Add a pause
        return element.text or ""

    def add(self, text: str, voice_id: str | None = None) -> str:
        """Generate SSML with optional voice settings."""
        ssml = f"<speak>{text}</speak>"
        if voice_id:
            ssml = f'<speak><voice name="{voice_id}">{text}</voice></speak>'
        return ssml