import os

import pytest
from tts_wrapper import GoogleClient, GoogleTTS

from . import BaseEngineTest


def create_client():
    return GoogleClient(os.environ.get("GOOGLE_CREDS_PATH"))


@pytest.mark.parametrize("formats,tts_cls", [(["wav"], GoogleTTS)])
class TestGoogleOffline(BaseEngineTest):
    pass


@pytest.mark.slow
@pytest.mark.parametrize(
    "formats,tts_cls,client",
    [(GoogleTTS.supported_formats(), GoogleTTS, create_client)],
)
class TestGoogleOnline(BaseEngineTest):
    pass
