import os

import pytest
from tts_wrapper import WatsonClient, WatsonTTS

from . import BaseEngineTest


def create_client():
    WATSON_API_KEY = os.getenv('WATSON_API_KEY')
    WATSON_REGION = os.getenv('WATSON_REGION')
    WATSON_INSTANCE_ID = os.getenv('WATSON_INSTANCE_ID')
    return WatsonClient(credentials=(WATSON_API_KEY, WATSON_REGION, WATSON_INSTANCE_ID))

@pytest.mark.parametrize("formats,tts_cls", [(["wav"], WatsonTTS)])
class TestWatsonOffline(BaseEngineTest):
    pass


@pytest.mark.slow
@pytest.mark.parametrize(
    "formats,tts_cls,client",
    [(WatsonTTS.supported_formats(), WatsonTTS, create_client)],
)
class TestWatsonOnline(BaseEngineTest):
    pass
