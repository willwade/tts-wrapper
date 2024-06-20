from ...ssml import BaseSSMLRoot, SSMLNode

class GoogleSSML(BaseSSMLRoot):
    def add(self, text: str) -> str:
        #get original text inside prosody tag
        if ("prosody" in text):
            first_split = text.split(">")
            opening_tag = first_split[0] + ">"
            second_split = first_split[1].split("<")
            original_text = second_split[0]
            closing_tag = "<" + second_split[1] + ">"
        else:
            original_text = text

        words = original_text.split()
        ssml_parts = []
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="{word}"/>{word}')

        if ("prosody" in text):
        #add back prosody tag to text with mark tag
            ssml_parts.insert(0,opening_tag)
            ssml_parts.append(closing_tag)

        #add speak tag to complete ssml
        ssml_parts.insert(0, "<speak>")
        ssml_parts.append("</speak>")
        return "".join(ssml_parts)

    def clean_children(self):
        self._inner.clean_children()