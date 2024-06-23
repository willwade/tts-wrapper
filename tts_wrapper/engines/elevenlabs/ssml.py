from ...ssml import BaseSSMLRoot, SSMLNode, Child

class ElevenLabsSSMLNode(SSMLNode):
    def __str__(self) -> str:
        # Override to generate only the inner content without the actual SSML tags
        rendered_children = "".join(str(c) for c in self._children)
        return rendered_children

class ElevenLabsSSMLRoot(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()
        self._inner = ElevenLabsSSMLNode("speak")  # The tag is irrelevant but kept for compatibility

    def __str__(self) -> str:
        # Use the overridden __str__ method of ElevenLabsSSMLNode
        return str(self._inner)
        
    def clean_children(self):
        self._inner.clean_children()