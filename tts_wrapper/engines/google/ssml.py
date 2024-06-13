from ...ssml import BaseSSMLRoot, SSMLNode

class GoogleSSML:
    def add(self, text: str) -> str:
        words = text.split()
        ssml_parts = ["<speak>"]
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="{word}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)
