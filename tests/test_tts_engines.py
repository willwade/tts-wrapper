import contextlib
import os
import sys
import time
from pathlib import Path
from unittest.mock import Mock

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
    PlayHTClient,
    PlayHTTTS,
    PollyClient,
    PollyTTS,
    SherpaOnnxClient,
    SherpaOnnxTTS,
    WatsonClient,
    WatsonTTS,
    WitAiClient,
    WitAiTTS,
    eSpeakClient,
    eSpeakTTS,
)

# Import AVSynth conditionally for macOS
if sys.platform == "darwin":
    from tts_wrapper import AVSynthClient, AVSynthTTS

# Dictionary to hold the TTS clients and their respective setup functions
TTS_CLIENTS = {
    "polly": {
        "client": lambda: PollyClient(
            credentials=(
                os.getenv("POLLY_REGION"),
                os.getenv("POLLY_AWS_KEY_ID"),
                os.getenv("POLLY_AWS_ACCESS_KEY"),
            )
        ),
        "class": PollyTTS,
    },
    "google": {
        "client": lambda: GoogleClient(credentials=os.getenv("GOOGLE_SA_PATH")),
        "class": GoogleTTS,
    },
    "microsoft": {
        "client": lambda: MicrosoftClient(
            credentials=(
                os.getenv("MICROSOFT_TOKEN"),
                os.getenv("MICROSOFT_REGION"),
            )
        ),
        "class": MicrosoftTTS,
    },
    "watson": {
        "client": lambda: WatsonClient(
            credentials=(
                os.getenv("WATSON_API_KEY"),
                os.getenv("WATSON_REGION"),
                os.getenv("WATSON_INSTANCE_ID"),
            )
        ),
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
        "client": lambda: SherpaOnnxClient(
            model_path=None, tokens_path=None, model_id="mms_eng"
        ),
        "class": SherpaOnnxTTS,
    },
    "espeak": {
        "client": lambda: eSpeakClient(),
        "class": eSpeakTTS,
    },
    "playht": {
        "client": lambda: PlayHTClient(
            credentials=(
                os.getenv("PLAYHT_API_KEY"),
                os.getenv("PLAYHT_USER_ID"),
            )
        ),
        "class": PlayHTTTS,
    },
}

# Add AVSynth only on macOS
if sys.platform == "darwin":
    TTS_CLIENTS["avsynth"] = {
        "client": lambda: AVSynthClient(),
        "class": AVSynthTTS,
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

            tts.set_property("volume", "90")
            tts.set_property("pitch", "x-high")

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


@pytest.mark.synthetic
@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_playback_with_callbacks(service):
    # Initialize TTS client for the service
    tts = create_tts_client(service)

    # Mocks for callbacks
    my_callback = Mock()
    on_start = Mock()
    on_end = Mock()

    # Example text and SSML text
    text = "Hello, this is a word timing test"
    try:
        ssml_text = tts.ssml.add(text)
    except (AttributeError, NotImplementedError):
        # Fall back to plain text for engines that don't support SSML
        ssml_text = text

    # Connect mock callbacks to the TTS instance
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)

    # Run playback with callbacks
    try:
        tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
        # Wait for playback to start and complete
        time.sleep(1)  # Wait for playback to start
        # Wait additional time for playback to complete
        max_wait = 5  # Maximum wait time in seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if on_end.call_count > 0:
                break
            time.sleep(0.1)
    except Exception as e:
        pytest.fail(f"Playback raised an exception: {e}")

    # Verify onStart and onEnd were called
    on_start.assert_called_once()
    on_end.assert_called_once()

    # Check that my_callback was called for each word in the text
    words_in_text = text.split()  # Split the text into individual words
    assert my_callback.call_count == len(
        words_in_text
    ), "Callback not called for each word."

    # Ensure each callback call has the correct structure: word, start_time, and end_time
    for call, word in zip(my_callback.call_args_list, words_in_text):
        args, _ = call  # Extract args from each callback call
        assert args[0] == word, f"Expected word '{word}' but got '{args[0]}'"
        assert isinstance(args[1], float), "Expected start_time to be a float"
        assert isinstance(args[2], float), "Expected end_time to be a float"
        assert args[2] > args[1], "End time should be greater than start time"


@pytest.mark.synthetic
def test_sherpaonnx_no_default_download():
    """Test that SherpaOnnxClient respects no_default_download flag."""
    # Initialize client with no_default_download=True
    client = SherpaOnnxClient(
        model_path=None, tokens_path=None, no_default_download=True
    )

    # Verify that tts is None (no model downloaded)
    assert client.tts is None

    # Verify that model_id is None
    assert client._model_id is None

    # Now explicitly set a voice
    client._model_id = "mms_eng"
    client.set_voice()

    # Verify that model is now downloaded and initialized
    assert client.tts is not None
    assert client._model_id == "mms_eng"

    # Test that we can use the voice after explicit setup
    try:
        client.synth("Test after explicit voice setup")
    except Exception as e:
        msg = "Failed to synthesize speech after explicit voice setup"
        pytest.fail(f"{msg}: {e}")
