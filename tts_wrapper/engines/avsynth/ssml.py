import logging
from xml.etree import ElementTree as ET
from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class AVSynthSSMLNode(SSMLNode):
    """SSML node implementation for AVSynth."""

    def __str__(self) -> str:
        """Convert SSML to text with embedded commands for AVSpeechSynthesizer."""
        if self._tag == "speak":
            return "".join(str(c) for c in self._children)
        elif self._tag == "break":
            # Convert SSML break to a pause
            time_str = self._attrs.get("time", "500ms")
            try:
                if time_str.endswith("ms"):
                    time_ms = int(time_str[:-2])
                elif time_str.endswith("s"):
                    time_ms = int(float(time_str[:-1]) * 1000)
                else:
                    time_ms = 500
                return f"[[slnc {time_ms}]]"
            except ValueError:
                return "[[slnc 500]]"
        elif self._tag == "prosody":
            # Handle rate, pitch, and volume
            text = "".join(str(c) for c in self._children)
            commands = []
            
            if "rate" in self._attrs:
                rate = self._attrs["rate"]
                if rate in ["x-slow", "slow", "medium", "fast", "x-fast"]:
                    commands.append(f"[[rate {rate}]]")
            
            if "pitch" in self._attrs:
                pitch = self._attrs["pitch"]
                if pitch in ["x-low", "low", "medium", "high", "x-high"]:
                    commands.append(f"[[pitch {pitch}]]")
            
            if "volume" in self._attrs:
                vol = self._attrs["volume"]
                if vol in ["silent", "x-soft", "soft", "medium", "loud", "x-loud"]:
                    commands.append(f"[[volm {vol}]]")
            
            return "".join(commands) + text
        else:
            # For unsupported tags, just return the text content
            return "".join(str(c) for c in self._children)


class AVSynthSSML(BaseSSMLRoot):
    """SSML root implementation for AVSynth."""

    def __init__(self) -> None:
        super().__init__()
        self._inner = AVSynthSSMLNode("speak")
        logging.debug("AVSynthSSML initialized")

    def __str__(self) -> str:
        return str(self._inner)

    def clear_ssml(self) -> None:
        """Clear all SSML content."""
        self._inner = AVSynthSSMLNode("speak")

    def construct_prosody_tag(
        self, 
        text: str, 
        rate: str = None, 
        volume: str = None, 
        pitch: str = None
    ) -> str:
        """Construct a prosody tag with the given attributes."""
        attrs = {}
        if rate is not None:
            attrs["rate"] = rate
        if volume is not None:
            attrs["volume"] = volume
        if pitch is not None:
            attrs["pitch"] = pitch
            
        node = AVSynthSSMLNode("prosody", attrs)
        node.add_text(text)
        return str(node)

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