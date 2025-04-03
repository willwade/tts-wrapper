from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class GoogleSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        """Initialize the GoogleSSML class."""
        super().__init__()
        self.ssml_version = "1.0"
        self.ssml_namespace = "http://www.w3.org/2001/10/synthesis"
        self.ssml_lang = "en-US"

    def add(self, text: str) -> "BaseSSMLRoot":
        """Add text to the SSML structure with word markers.

        Args:
            text: The text to add to the SSML

        Returns:
            self: Returns self for method chaining
        """
        # Clear existing content
        self.clear_ssml()

        # get original text inside prosody tag
        if "prosody" in text:
            first_split = text.split(">")
            opening_tag = first_split[0] + ">"
            second_split = first_split[1].split("<")
            original_text = second_split[0]
            closing_tag = "<" + second_split[1] + ">"
        else:
            original_text = text

        words = original_text.split()
        ssml_parts = []
        for _i, word in enumerate(words):
            ssml_parts.append(f'<mark name="{word}"/>{word}')

        ssml_content = " ".join(ssml_parts)

        if "prosody" in text:
            # add back prosody tag to text with mark tag
            ssml_content = f"{opening_tag}{ssml_content}{closing_tag}"

        # Add the content as a raw node
        self._inner.add(SSMLNode("raw", children=[ssml_content]))

        return self

    def clear_ssml(self) -> None:
        """Clear all SSML content."""
        self._inner.clear_ssml()
