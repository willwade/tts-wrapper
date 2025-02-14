import logging
from xml.etree import ElementTree as ET
from tts_wrapper.ssml import BaseSSMLRoot
from tts_wrapper.ssml import SSMLNode


class AVSynthSSML(BaseSSMLRoot):
    """SSML parser and generator tailored for AVSynth."""

    def __init__(self) -> None:
        super().__init__()
        logging.debug("AVSynthSSML initialized")

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

    def add_text(self, text: str) -> None:
        """Add plain text to the SSML."""
        self._root.add(SSMLNode("text", children=[text]))

    def add_voice(self, text: str, voice_id: str) -> None:
        """Add text wrapped with a voice tag."""
        voice_node = SSMLNode("voice", attrs={"name": voice_id}, children=[text])
        self._root.add(voice_node)

    def add_break(self, time: str = "500ms") -> None:
        """Add a break tag to the SSML."""
        break_node = SSMLNode("break", attrs={"time": time})
        self._root.add(break_node)

    def add_prosody(
        self, text: str, rate: str = "medium", pitch: str = "medium", volume: str = "medium"
    ) -> None:
        """Add a prosody tag with custom attributes."""
        prosody_node = SSMLNode(
            "prosody", attrs={"rate": rate, "pitch": pitch, "volume": volume}, children=[text]
        )
        self._root.add(prosody_node)