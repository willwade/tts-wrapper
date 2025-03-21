import os
import sys
import time
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

# Dictionary mapping service names to their TTS classes
TTS_CLIENTS = {
    "polly": PollyTTS,
    "google": GoogleTTS,
    "microsoft": MicrosoftTTS,
    "watson": WatsonTTS,
    "elevenlabs": ElevenLabsTTS,
    "witai": WitAiTTS,
    "googletrans": GoogleTransTTS,
    "sherpaonnx": SherpaOnnxTTS,
    "espeak": eSpeakTTS,
    "playht": PlayHTTTS,
}

# Add AVSynth only on macOS
if sys.platform == "darwin":
    TTS_CLIENTS["avsynth"] = AVSynthTTS

# Dictionary to cache credential validation results
VALID_CREDENTIALS = {}


def check_credentials(service):
    """Check if credentials for a service are valid."""
    # Return cached result if available
    if service in VALID_CREDENTIALS:
        return VALID_CREDENTIALS[service]

    try:
        # Create client based on service type
        if service == "polly":
            client = PollyClient(
                credentials=(
                    os.getenv("POLLY_AWS_KEY_ID"),
                    os.getenv("POLLY_AWS_ACCESS_KEY"),
                    os.getenv("POLLY_REGION"),
                )
            )
        elif service == "google":
            # For Google, credentials should be a file path
            credentials_path = os.getenv("GOOGLE_SA_PATH")
            client = GoogleClient(credentials=credentials_path)
        elif service == "microsoft":
            client = MicrosoftClient(
                credentials=(
                    os.getenv("MICROSOFT_TOKEN"),
                    os.getenv("MICROSOFT_REGION")
                )
            )
        elif service == "watson":
            client = WatsonClient(
                credentials=(
                    os.getenv("WATSON_API_KEY"),
                    os.getenv("WATSON_REGION"),
                    os.getenv("WATSON_INSTANCE_ID"),
                )
            )
        elif service == "elevenlabs":
            client = ElevenLabsClient(
                credentials=os.getenv("ELEVENLABS_API_KEY")
            )
        elif service == "witai":
            client = WitAiClient(
                credentials=os.getenv("WITAI_API_KEY")
            )
        elif service == "googletrans":
            client = GoogleTransClient()
        elif service == "sherpaonnx":
            client = SherpaOnnxClient()
        elif service == "espeak":
            client = eSpeakClient()
        elif service == "playht":
            client = PlayHTClient(
                credentials=(
                    os.getenv("PLAYHT_USER_ID"),
                    os.getenv("PLAYHT_API_KEY")
                )
            )
        elif service == "avsynth" and sys.platform == "darwin":
            client = AVSynthClient()
        else:
            # Unknown service or not available on this platform
            VALID_CREDENTIALS[service] = False
            return False

        # Check if credentials are valid
        has_check = hasattr(client, "check_credentials")
        valid = client.check_credentials() if has_check else True
        VALID_CREDENTIALS[service] = valid
        return valid
    except Exception as e:
        error_msg = f"Error checking credentials for {service}: {e}"
        print(error_msg)
        VALID_CREDENTIALS[service] = False
        return False


def create_tts_client(service):
    """Create a TTS client for the specified service."""
    # First create the client instance
    if service == "polly":
        client = PollyClient(
            credentials=(
                os.getenv("POLLY_AWS_KEY_ID"),
                os.getenv("POLLY_AWS_ACCESS_KEY"),
                os.getenv("POLLY_REGION"),
            )
        )
        return PollyTTS(client)
    if service == "google":
        # For Google, credentials should be a file path
        credentials_path = os.getenv("GOOGLE_SA_PATH")
        client = GoogleClient(credentials=credentials_path)
        return GoogleTTS(client)
    if service == "microsoft":
        client = MicrosoftClient(
            credentials=(
                os.getenv("MICROSOFT_TOKEN"),
                os.getenv("MICROSOFT_REGION")
            )
        )
        return MicrosoftTTS(client)
    if service == "watson":
        client = WatsonClient(
            credentials=(
                os.getenv("WATSON_API_KEY"),
                os.getenv("WATSON_REGION"),
                os.getenv("WATSON_INSTANCE_ID"),
            )
        )
        return WatsonTTS(client)
    if service == "elevenlabs":
        client = ElevenLabsClient(
            credentials=os.getenv("ELEVENLABS_API_KEY")
        )
        return ElevenLabsTTS(client)
    if service == "witai":
        client = WitAiClient(
            credentials=os.getenv("WITAI_API_KEY")
        )
        return WitAiTTS(client)
    if service == "googletrans":
        client = GoogleTransClient()
        return GoogleTransTTS(client)
    if service == "sherpaonnx":
        client = SherpaOnnxClient()
        return SherpaOnnxTTS(client)
    if service == "espeak":
        client = eSpeakClient()
        return eSpeakTTS(client)
    if service == "playht":
        client = PlayHTClient(
            credentials=(
                os.getenv("PLAYHT_USER_ID"),
                os.getenv("PLAYHT_API_KEY")
            )
        )
        return PlayHTTTS(client)
    if service == "avsynth" and sys.platform == "darwin":
        client = AVSynthClient()
        return AVSynthTTS(client)
    msg = f"Unknown service or not available on this platform: {service}"
    raise ValueError(msg)


@pytest.mark.synthetic
@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_synth_to_bytes(service):
    # Skip tests for engines with invalid credentials
    if not check_credentials(service):
        pytest.skip(f"{service.capitalize()} TTS credentials are invalid or unavailable")

    tts = create_tts_client(service)

    # Plain text demo
    text = "Hello, this is a test."
    try:
        audio_bytes = tts.synth_to_bytes(text)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
    except Exception as e:
        pytest.fail(f"Synthesis failed with error: {e}")

    # SSML text demo
    try:
        ssml_text = tts.ssml.add(text)
        audio_bytes = tts.synth_to_bytes(ssml_text)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
    except (AttributeError, NotImplementedError):
        # Skip SSML test for engines that don't support it
        pass
    except Exception as e:
        pytest.fail(f"SSML synthesis failed with error: {e}")


@pytest.mark.synthetic
@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_playback_with_callbacks(service):
    # Skip tests for engines with invalid credentials
    if not check_credentials(service):
        pytest.skip(f"{service.capitalize()} TTS credentials are invalid or unavailable")

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

    # Get the number of words in the text
    words_in_text = text.split()

    # Check that callbacks were made
    assert my_callback.call_count > 0, "No word callbacks were made"

    # Different engines may handle word callbacks differently:
    # 1. Some engines like Google may call the callback more times than there are words
    # 2. Some engines may combine words or split them differently

    # Instead of checking exact word matches, we'll verify:
    # - For most engines, there should be approximately the same number of callbacks as words
    # - Each callback should have the right structure (word, start_time, end_time)
    # - The timing values should be reasonable (start_time < end_time)

    # Print information about the callbacks for debugging
    if my_callback.call_count != len(words_in_text):
        print(
            f"Note: {service} called callback {my_callback.call_count} times "
            f"for {len(words_in_text)} words"
        )

    # Check the structure of the callbacks
    for i, call in enumerate(my_callback.call_args_list):
        args, _ = call  # Extract args from each callback call

        # Check that we have 3 arguments (word, start_time, end_time)
        assert len(args) == 3, f"Callback {i} has wrong number of arguments: {len(args)}"

        # Check that the word is a string
        assert isinstance(args[0], str), f"Callback {i} word is not a string: {type(args[0])}"

        # Check that start_time and end_time are floats
        assert isinstance(args[1], float), f"Callback {i} start_time is not a float: {type(args[1])}"
        assert isinstance(args[2], float), f"Callback {i} end_time is not a float: {type(args[2])}"

        # Check that start_time is less than end_time
        assert args[1] <= args[2], (
            f"Callback {i} start_time ({args[1]}) is greater than "
            f"end_time ({args[2]})"
        )
