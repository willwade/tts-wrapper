from ...ssml import BaseSSMLRoot, SSMLNode


# Microsoft/ssml.py

class MicrosoftSSML(BaseSSMLRoot):
    def __init__(self, lang: str, voice: str) -> None:
        self.lang = lang
        self.voice = voice
        self._inner = SSMLNode("voice", {"name": self.voice})
        self._root = SSMLNode(
            "speak",
            {
                "version": "1.0",
                "xml:lang": self.lang,
                "xmlns": "https://www.w3.org/2001/10/synthesis",
                "xmlns:mstts": "https://www.w3.org/2001/mstts",
            }
        ).add(self._inner)
        self._prosody = None

    def set_voice(self, new_voice: str, new_lang: str):
        """Updates the voice and language for the SSML without reconstructing the SSML nodes."""
        self.voice = new_voice
        self.lang = new_lang
        self._inner.update_attributes({"name": new_voice})
        self._root.update_attributes({"xml:lang": new_lang})

