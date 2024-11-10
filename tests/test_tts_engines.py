import contextlib
import os
import time
from pathlib import Path

import pytest

from tts_wrapper import (
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
    GoogleTransClient,
    GoogleTransTTS,
    GoogleTTS,
    MicrosoftClient,
    MicrosoftTTS,
    PollyClient,
    PollyTTS,
    SherpaOnnxClient,
    SherpaOnnxTTS,
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
)

# Dictionary to hold the TTS clients and their respective setup functions
TTS_CLIENTS = {
    "polly": {
        "client": lambda: PollyClient(credentials=(
            os.getenv("POLLY_REGION"),
            os.getenv("POLLY_AWS_KEY_ID"),
            os.getenv("POLLY_AWS_ACCESS_KEY"),
        )),
        "class": PollyTTS,
    },
    "google": {
        "client": lambda: GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH")),
        "class": GoogleTTS,
    },
    "microsoft": {
        "client": lambda: MicrosoftClient(credentials=(
            os.getenv("MICROSOFT_TOKEN"),
            os.getenv("MICROSOFT_REGION"),
        )),
        "class": MicrosoftTTS,
    },
    "watson": {
        "client": lambda: WatsonClient(credentials=(
            os.getenv("WATSON_API_KEY"),
            os.getenv("WATSON_REGION"),
            os.getenv("WATSON_INSTANCE_ID"),
        )),
        "class": WatsonTTS,
    },
    "elevenlabs": {
        "client": lambda: ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY")),
        "class": ElevenLabsTTS,
    },
    "witai": {
        "client": lambda: WitAiClient(credentials=os.getenv("WITAI_TOKEN")),
        "class": WitAiTTS,
    },
    "googletrans": {
        "client": lambda: GoogleTransClient("en-co.uk"),
        "class": GoogleTransTTS,
    },
    "sherpaonnx": {
        "client": lambda: SherpaOnnxClient(model_path=None, tokens_path=None, voice_id="eng"),
        "class": SherpaOnnxTTS,
    },
}

def create_tts_client(service):
    config = TTS_CLIENTS[service]
    client = config["client"]()
    tts_class = config["class"]
    return tts_class(client)

@pytest.mark.synthetic
@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_tts_engine(service) -> None:
    tts = create_tts_client(service)

    # Plain text demo
    text_read = "Hello, world! This is a text of plain text sending"
    with contextlib.suppress(Exception):
        tts.speak(text_read)

    # SSML with prosody control
    try:
        text_read = "Hello, world!"
        text_with_prosody = tts.construct_prosody_tag(text_read)

        tts.ssml.clear_ssml()
        ssml_text = tts.ssml.add(text_with_prosody)

        try:
            tts.speak_streamed(ssml_text)

            time.sleep(3)
            tts.ssml.clear_ssml()

            tts.set_property("volume","90")
            tts.set_property("pitch","x-high")

            text_read_2 = "This is louder than before"
            text_with_prosody = tts.construct_prosody_tag(text_read_2)
            time.sleep(0.5)
            ssml_text = tts.ssml.add(text_with_prosody)
            tts.speak_streamed(ssml_text)

            time.sleep(1)

        except Exception:
            pass

    except Exception:
        pass

    # Save to audio file
    try:
        tts.ssml.clear_ssml()
        ssml_text = tts.ssml.add("Lets save to an audio file")
        output_file = Path(f"output_{service}.wav")
        tts.synth(ssml_text, str(output_file), format="wav")
    except Exception:
        pass

    # Change voice and test again if possible
    try:
        voices = tts.get_voices()
        for voice in voices[:4]:  # Show details for first four voices
            language_codes = voice.get("language_codes", [])
            voice.get("name", "Unknown voice")
            language_codes[0] if language_codes else "Unknown"
        if len(voices) > 1:
            new_voice_id = voices[1].get("id")
            new_lang_codes = voices[1].get("language_codes", [])
            new_lang_id = new_lang_codes[0] if new_lang_codes else "Unknown"
            tts.set_voice(new_voice_id, new_lang_id)
            ssml_text_part2 = tts.ssml.add("Continuing with a new voice!")
            tts.speak_streamed(ssml_text_part2)
    except Exception:
        pass
