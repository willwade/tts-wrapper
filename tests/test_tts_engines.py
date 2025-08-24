import logging
import os
import sys
import time
from unittest.mock import Mock

import pytest

from tts_wrapper import (
    ElevenLabsClient,
    GoogleClient,
    GoogleTransClient,
    MicrosoftClient,
    OpenAIClient,
    PlayHTClient,
    PollyClient,
    SherpaOnnxClient,
    UpliftAIClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)

# Import AVSynth conditionally for macOS
if sys.platform == "darwin":
    from tts_wrapper import AVSynthClient

# Dictionary mapping service names to their client classes
TTS_CLIENTS = {
    "polly": PollyClient,
    "google": GoogleClient,
    "microsoft": MicrosoftClient,
    "watson": WatsonClient,
    "elevenlabs": ElevenLabsClient,
    "witai": WitAiClient,
    "googletrans": GoogleTransClient,
    "sherpaonnx": SherpaOnnxClient,
    "espeak": eSpeakClient,
    "playht": PlayHTClient,
    "openai": OpenAIClient,
    "upliftai": UpliftAIClient,
}

# Add AVSynth only on macOS
if sys.platform == "darwin":
    TTS_CLIENTS["avsynth"] = AVSynthClient

# Dictionary to cache credential validation results
VALID_CREDENTIALS: dict[str, bool] = {}


def check_credentials(service):
    """Check if credentials for a service are valid."""
    # Return cached result if available
    if service in VALID_CREDENTIALS:
        return VALID_CREDENTIALS[service]

    # For AVSynth, check if we're on macOS
    if service == "avsynth":
        if sys.platform != "darwin":
            VALID_CREDENTIALS[service] = False
            return False
        VALID_CREDENTIALS[service] = True
        return True

    # Special cases for services that don't need credentials
    if service in ["espeak", "sherpaonnx", "googletrans"]:
        # For these services, just return True
        VALID_CREDENTIALS[service] = True
        return True

    # For PlayHT, check if environment variables are set
    if service == "playht":
        if os.getenv("PLAYHT_USER_ID") and os.getenv("PLAYHT_API_KEY"):
            VALID_CREDENTIALS[service] = True
            return True
        VALID_CREDENTIALS[service] = False
        return False

    try:
        # Create client based on service type
        if service == "polly":
            client = PollyClient(
                credentials=(
                    os.getenv("POLLY_REGION"),
                    os.getenv("POLLY_AWS_KEY_ID"),
                    os.getenv("POLLY_AWS_ACCESS_KEY"),
                )
            )
        elif service == "google":
            # For Google, credentials should be a file path
            credentials_path = os.getenv("GOOGLE_SA_PATH")
            print(f"Google credentials path: {credentials_path}")
            # Check if the file exists
            if credentials_path:
                # Try both the path as-is and as a relative path from the current directory
                if os.path.exists(credentials_path):
                    print(
                        f"Google credentials file exists: {os.path.abspath(credentials_path)}"
                    )
                    client = GoogleClient(credentials=credentials_path)
                elif os.path.exists(os.path.join(os.getcwd(), credentials_path)):
                    abs_path = os.path.join(os.getcwd(), credentials_path)
                    print(f"Google credentials file exists at: {abs_path}")
                    client = GoogleClient(credentials=abs_path)
                else:
                    print(f"Google credentials file does not exist: {credentials_path}")
                    VALID_CREDENTIALS[service] = False
                    return False
            else:
                print("Google credentials path is not set")
                VALID_CREDENTIALS[service] = False
                return False
        elif service == "microsoft":
            client = MicrosoftClient(
                credentials=(
                    os.getenv("MICROSOFT_TOKEN"),
                    os.getenv("MICROSOFT_REGION"),
                )
            )
        elif service == "watson":
            # Watson credentials are known to be invalid, skip the test
            VALID_CREDENTIALS[service] = False
            return False
        elif service == "elevenlabs":
            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            print(
                f"ElevenLabs API key: {elevenlabs_api_key[:5]}...{elevenlabs_api_key[-5:] if elevenlabs_api_key else ''}"
            )
            client = ElevenLabsClient(credentials=elevenlabs_api_key)
        elif service == "upliftai":
            client = UpliftAIClient(api_key=os.getenv("UPLIFTAI_KEY"))
        elif service == "witai":
            client = WitAiClient(credentials=os.getenv("WITAI_API_KEY"))
        elif service == "googletrans":
            client = GoogleTransClient()
        elif service == "sherpaonnx":
            client = SherpaOnnxClient()
        elif service == "espeak":
            client = eSpeakClient()
        elif service == "playht":
            client = PlayHTClient(
                credentials=(os.getenv("PLAYHT_API_KEY"), os.getenv("PLAYHT_USER_ID"))
            )
        elif service == "avsynth" and sys.platform == "darwin":
            client = AVSynthClient()
        elif service == "openai":
            client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
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
    if service == "polly":
        return PollyClient(
            credentials=(
                os.getenv("POLLY_REGION"),
                os.getenv("POLLY_AWS_KEY_ID"),
                os.getenv("POLLY_AWS_ACCESS_KEY"),
            )
        )
    if service == "google":
        # For Google, credentials should be a file path
        credentials_path = os.getenv("GOOGLE_SA_PATH")
        return GoogleClient(credentials=credentials_path)
    if service == "microsoft":
        return MicrosoftClient(
            credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION"))
        )
    if service == "watson":
        return WatsonClient(
            credentials=(
                os.getenv("WATSON_API_KEY"),
                os.getenv("WATSON_REGION"),
                os.getenv("WATSON_INSTANCE_ID"),
            )
        )
    if service == "elevenlabs":
        return ElevenLabsClient(credentials=os.getenv("ELEVENLABS_API_KEY"))
    if service == "witai":
        return WitAiClient(credentials=os.getenv("WITAI_API_KEY"))
    if service == "googletrans":
        return GoogleTransClient()
    if service == "sherpaonnx":
        return SherpaOnnxClient()
    if service == "espeak":
        return eSpeakClient()
    if service == "playht":
        return PlayHTClient(
            credentials=(os.getenv("PLAYHT_API_KEY"), os.getenv("PLAYHT_USER_ID"))
        )
    if service == "upliftai":
        return UpliftAIClient(api_key=os.getenv("UPLIFTAI_KEY"))
    if service == "avsynth" and sys.platform == "darwin":
        return AVSynthClient()
    if service == "openai":
        return OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    msg = f"Unknown service or not available on this platform: {service}"
    raise ValueError(msg)


@pytest.mark.synthetic
@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_synth_to_bytes(service):
    # Skip tests for engines with invalid credentials
    if not check_credentials(service):
        pytest.skip(
            f"{service.capitalize()} TTS credentials are invalid or unavailable"
        )

    # Skip eSpeak test if it's causing segmentation faults
    if service == "espeak" and os.environ.get("SKIP_ESPEAK_SYNTH_TEST", "") == "1":
        pytest.skip("Skipping eSpeak test due to potential segmentation fault")

    client = create_tts_client(service)

    # Set a valid voice for Microsoft client
    if service == "microsoft":
        client.set_voice("en-US-JennyMultilingualNeural")

    # Plain text demo
    text = "Hello, this is a test."
    try:
        audio_bytes = client.synth_to_bytes(text)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
    except Exception as e:
        pytest.fail(f"Synthesis failed with error: {e}")

    # SSML text demo
    try:
        # Use a simple text for SSML to avoid issues with complex SSML structures
        simple_text = "This is a simple test."
        ssml_text = client.ssml.add(simple_text)

        # Log the SSML text for debugging
        logging.debug(f"SSML text for {service}: {ssml_text}")

        audio_bytes = client.synth_to_bytes(ssml_text)
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
    # Skip eSpeak test if it's causing segmentation faults
    if service == "espeak" and os.environ.get("SKIP_ESPEAK_CALLBACK_TEST", "") == "1":
        pytest.skip("Skipping eSpeak callback test due to potential segmentation fault")

    # Special handling for services that don't need credentials
    if service in ["espeak", "sherpaonnx", "googletrans"]:
        # These services don't need credentials, continue with the test
        pass
    # For AVSynth, check if we're on macOS
    elif service == "avsynth":
        if sys.platform != "darwin":
            pytest.skip("AVSynth is only available on macOS")
    # For PlayHT, check if environment variables are set
    elif service == "playht":
        if not (os.getenv("PLAYHT_USER_ID") and os.getenv("PLAYHT_API_KEY")):
            pytest.skip("PlayHT credentials are not set")
    # For other services, check credentials
    elif not check_credentials(service):
        pytest.skip(
            f"{service.capitalize()} TTS credentials are invalid or unavailable"
        )

    # Initialize TTS client for the service
    client = create_tts_client(service)

    # Set a valid voice for Microsoft client
    if service == "microsoft":
        client.set_voice("en-US-JennyMultilingualNeural")

    # Mocks for callbacks
    my_callback = Mock()
    on_start = Mock()
    on_end = Mock()

    # Example text and SSML text
    text = "Hello, this is a word timing test"
    try:
        # Use a simple text for SSML to avoid issues with complex SSML structures
        simple_text = "This is a simple test."
        ssml_text = client.ssml.add(simple_text)

        # Log the SSML text for debugging
        logging.debug(f"SSML text for {service} callback test: {ssml_text}")
    except (AttributeError, NotImplementedError):
        # Fall back to plain text for engines that don't support SSML
        ssml_text = text

    # Connect mock callbacks to the TTS instance
    client.connect("onStart", on_start)
    client.connect("onEnd", on_end)

    # Run playback with callbacks
    try:
        client.start_playback_with_callbacks(ssml_text, callback=my_callback)
        # Wait for playback to start and complete
        time.sleep(2)  # Wait for playback to start
        # Wait additional time for playback to complete
        max_wait = 10  # Maximum wait time in seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if on_end.call_count > 0:
                break
            time.sleep(0.1)
    except Exception as e:
        pytest.fail(f"Playback raised an exception: {e}")

    # Verify onStart and onEnd were called
    if service == "googletrans":
        # GoogleTrans may call callbacks multiple times, just check that they were called
        assert on_start.call_count > 0, "onStart callback was not called"
        assert on_end.call_count > 0, "onEnd callback was not called"
    else:
        # For other engines, expect exactly one call
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
        assert (
            len(args) == 3
        ), f"Callback {i} has wrong number of arguments: {len(args)}"

        # Check that the word is a string
        assert isinstance(
            args[0], str
        ), f"Callback {i} word is not a string: {type(args[0])}"

        # Check that start_time and end_time are floats
        assert isinstance(
            args[1], float
        ), f"Callback {i} start_time is not a float: {type(args[1])}"
        assert isinstance(
            args[2], float
        ), f"Callback {i} end_time is not a float: {type(args[2])}"

        # Check that start_time is less than end_time
        assert args[1] <= args[2], (
            f"Callback {i} start_time ({args[1]}) is greater than "
            f"end_time ({args[2]})"
        )
