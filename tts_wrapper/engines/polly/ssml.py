from ...ssml import BaseSSMLRoot, SSMLNode

class PollySSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()
    
    def clear_ssml(self):
        self._inner.clear_ssml()

#PollySSML = BaseSSMLRoot
