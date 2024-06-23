from ...ssml import BaseSSMLRoot, SSMLNode

class PollySSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()
    
    def clean_children(self):
        self._inner.clean_children()

#PollySSML = BaseSSMLRoot
