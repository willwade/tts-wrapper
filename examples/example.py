# if running within the project dir
# export PYTHONPATH="/Users/willwade/GitHub/tts-wrapper:$PYTHONPATH"
# python examples/example.py
import contextlib
import os
import signal
import sys
import time
from pathlib import Path

from load_credentials import load_credentials

from tts_wrapper import (
    AVSynthClient,
    ElevenLabsClient,
    GoogleClient,
    MicrosoftClient,
    PollyClient,
    SherpaOnnxClient,
    WatsonClient,
    WitAiClient,
    eSpeakClient,
)


def signal_handler(sig, frame) -> None:
    """Handle Ctrl+C signal.

    Args:
        sig: Signal number (unused but required by signal.signal)
        frame: Current stack frame (unused but required by signal.signal)
    """
    sys.exit(0)


def create_tts_client(service):
    if service == "polly":
        region = os.getenv("POLLY_REGION")
        aws_key_id = os.getenv("POLLY_AWS_KEY_ID")
        aws_access_key = os.getenv("POLLY_AWS_ACCESS_KEY")
        client = PollyClient(credentials=(region, aws_key_id, aws_access_key))
        client.set_voice("Joanna")
    elif service == "microsoft":
        token = os.getenv("MICROSOFT_TOKEN")
        region = os.getenv("MICROSOFT_REGION")
        client = MicrosoftClient(credentials=(token, region))
    elif service == "watson":
        api_key = os.getenv("WATSON_API_KEY")
        region = os.getenv("WATSON_REGION")
        instance_id = os.getenv("WATSON_INSTANCE_ID")
        client = WatsonClient(credentials=(api_key, region, instance_id))
    elif service == "google":
        creds_path = os.getenv("GOOGLE_SA_PATH")
        client = GoogleClient(credentials=creds_path)
    elif service == "elevenlabs":
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(credentials=api_key)
    elif service == "witai":
        api_key = os.getenv("WITAI_TOKEN")
        client = WitAiClient(credentials=(api_key))
    elif service == "sherpaonnx":
        client = SherpaOnnxClient(model_path=None, tokens_path=None)
    elif service == "espeak":
        client = eSpeakClient()
    elif service == "avsynth":
        client = AVSynthClient()
    else:
        msg = "Unsupported TTS service"
        raise ValueError(msg)
    return client


def test_tts_engine(client, service_name) -> None:

    text_read = "Hello, world! This is a text of plain text sending"
    with contextlib.suppress(Exception):
        client.speak_streamed(text_read)

    try:
        text_read = "Hello, world!"
        text_with_prosody = client.construct_prosody_tag(text_read)

        client.ssml.clear_ssml()
        ssml_text = client.ssml.add(
            text_with_prosody
        )  # Assuming there's a method to add SSML correctly

        try:
            client.speak_streamed(ssml_text)

            time.sleep(3)
            client.ssml.clear_ssml()

            client.set_property("volume", "90")
            client.set_property("pitch", "x-high")

            text_read_2 = "This is louder than before"

            text_with_prosody = client.construct_prosody_tag(text_read_2)
            time.sleep(0.5)
            ssml_text = client.ssml.add(text_with_prosody)

            # print ("Testing setting volume to 90")
            client.speak_streamed(ssml_text)

            time.sleep(1)

        except Exception:
            pass

    except Exception:
        pass

    client.ssml.clear_ssml()
    ssml_text = client.ssml.add("Lets save to an audio file")
    # Demonstrate saving audio to a file
    output_file = Path(f"output_{service_name}.wav")
    client.synth(ssml_text, str(output_file))
    # or you could do
    # client.speak(ssml_text)

    # Change voice and test again if possible
    voices = client.get_voices()
    for voice in voices[:4]:  # Show details for first four voices
        language_codes = voice.get("language_codes", [])
        voice.get("name", "Unknown voice")
        # Safely get the first language code, default to 'Unknown' if not available
        language_codes[0] if language_codes else "Unknown"
    # Change voice if more than one is available
    if len(voices) > 1:
        new_voice_id = voices[1].get("id")
        # Attempt to get the first language from the second voice's language codes
        new_lang_codes = voices[1].get("language_codes", [])
        new_lang_id = new_lang_codes[0] if new_lang_codes else "Unknown"
        client.set_voice(new_voice_id, new_lang_id)
        ssml_text_part2 = client.ssml.add("Continuing with a new voice!")
        client.speak_streamed(ssml_text_part2)


def main() -> None:
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    # Load credentials
    try:
        load_credentials("credentials-private.json")
    except FileNotFoundError:
        print("Credentials file not found. Using environment variables if available.")
    services = (
        [
            "elevenlabs",
            "google",
            "microsoft",
            "polly",
            "watson",
            "witai",
            "espeak",
            "avsynth",
            "sherpaonnx",
        ]
        if service == "all"
        else [service]
    )
    for svc in services:
        client = create_tts_client(svc)
        # microsoft test with absolute value
        # client.set_property("volume", "20")

        # google test with predefined words or decibels
        client.set_property("volume", "5")
        client.set_property("rate", "x-slow")
        client.set_property("pitch", "x-low")
        test_tts_engine(client, svc)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
