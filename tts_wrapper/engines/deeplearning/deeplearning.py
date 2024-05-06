from typing import Any, List, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import DeepLearningClient, DeepLearningSSML


class DeepLearningTTS(AbstractTTS):
    def __init__(self, client):
        self.client = client

    def synth_to_bytes(self, text, format):
        return self.client.synth(text, "default_voice", format)

    def get_voices(self):
        return self.client.get_voices()
