from tts_wrapper.ssml.ssml_node import SSMLNode
from ...ssml import BaseSSMLRoot


class WatsonSSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()

    def clear_ssml(self):
        pass
