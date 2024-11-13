from tts_wrapper.ssml import BaseSSMLRoot


class PollySSML(BaseSSMLRoot):
    def __init__(self) -> None:
        super().__init__()

    def clear_ssml(self) -> None:
        self._inner.clear_ssml()


# PollySSML = BaseSSMLRoot
