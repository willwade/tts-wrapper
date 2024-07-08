import os

import pytest
from tts_wrapper import PollyClient, PollyTTS

from . import BaseEngineTest


def create_client():
    POLLY_REGION = os.environ.get("POLLY_REGION")
    POLLY_AWS_ID = os.environ.get("POLLY_AWS_KEY_ID")
    POLLY_AWS_KEY = os.environ.get("POLLY_AWS_ACCESS_KEY")
    return PollyClient(credentials=(POLLY_REGION, POLLY_AWS_ID, POLLY_AWS_KEY))

@pytest.mark.parametrize("formats,tts_cls", [(["wav"], PollyTTS)])
class TestPollyOffline(BaseEngineTest):
    pass


@pytest.mark.slow
@pytest.mark.parametrize(
    "formats,tts_cls,client", [(PollyTTS.supported_formats(), PollyTTS, create_client)]
)
class TestPollyOnline(BaseEngineTest):
    pass
