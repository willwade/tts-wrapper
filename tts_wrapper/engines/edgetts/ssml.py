from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class EdgeSSML(BaseSSMLRoot):
    """SSML handler for Microsoft Edge TTS."""

    def add_break(self, time: str = "500ms") -> None:
        """Add a break tag to the SSML."""
        self.root.add(SSMLNode("break", attrs={"time": time}))

    def add_voice(self, text: str, voice: str) -> None:
        """Add a voice tag to the SSML."""
        self.root.add(SSMLNode("voice", attrs={"name": voice}, children=[text]))

    def set_prosody(self, text: str, rate: str = "+0%", pitch: str = "+0Hz", volume: str = "+0%") -> str:
        """Add a prosody tag around the given text."""
        return str(
            self.root.add(
                SSMLNode(
                    "prosody",
                    attrs={"rate": rate, "pitch": pitch, "volume": volume},
                    children=[text],
                )
            )
        )