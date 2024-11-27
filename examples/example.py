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
    ElevenLabsClient,
    ElevenLabsTTS,
    GoogleClient,
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


def signal_handler(signal, frame) -> None:
    sys.exit(0)


def create_tts_client(service):
    if service == "polly":
        region = os.getenv("POLLY_REGION")
        aws_key_id = os.getenv("POLLY_AWS_KEY_ID")
        aws_access_key = os.getenv("POLLY_AWS_ACCESS_KEY")
        client = PollyClient(credentials=(region, aws_key_id, aws_access_key))
        tts = PollyTTS(client=client, voice="Joanna")
    elif service == "microsoft":
        token = os.getenv("MICROSOFT_TOKEN")
        region = os.getenv("MICROSOFT_REGION")
        client = MicrosoftClient(credentials=(token, region))
        tts = MicrosoftTTS(client=client)
    elif service == "watson":
        api_key = os.getenv("WATSON_API_KEY")
        region = os.getenv("WATSON_REGION")
        instance_id = os.getenv("WATSON_INSTANCE_ID")
        client = WatsonClient(credentials=(api_key, region, instance_id))
        tts = WatsonTTS(client=client)
    elif service == "google":
        creds_path = os.getenv("GOOGLE_SA_PATH")
        client = GoogleClient(credentials=creds_path)
        tts = GoogleTTS(client=client)
    elif service == "elevenlabs":
        api_key = os.getenv("ELEVENLABS_API_KEY")
        client = ElevenLabsClient(credentials=api_key)
        tts = ElevenLabsTTS(client=client)
    elif service == "witai":
        api_key = os.getenv("WITAI_TOKEN")
        client = WitAiClient(credentials=(api_key))
        tts = WitAiTTS(client=client)
    elif service == "sherpaonnx":
        client = SherpaOnnxClient(model_path=None, tokens_path=None)
        tts = SherpaOnnxTTS(client)
    elif service == "watson":
        api_key = os.getenv("WATSON_API_KEY")
        region = os.getenv("WATSON_REGION")
        instance_id = os.getenv("WATSON_INSTANCE_ID")
        client = WatsonClient(credentials=(api_key, region, instance_id))
        tts = WatsonTTS(client=client)
    else:
        msg = "Unsupported TTS service"
        raise ValueError(msg)
    return tts

def test_tts_engine(tts, service_name) -> None:

    text_read = "Hello, world! This is a text of plain text sending"
    with contextlib.suppress(Exception):
        tts.speak_streamed(text_read)

    try:
        text_read = "Hello, world!"
        text_with_prosody = tts.construct_prosody_tag(text_read)

        tts.ssml.clear_ssml()
        ssml_text = tts.ssml.add(text_with_prosody)  # Assuming there's a method to add SSML correctly

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

            #print ("Testing setting volume to 90")
            tts.speak_streamed(ssml_text)

            time.sleep(1)

        except Exception:
            pass


    except Exception:
        pass

    tts.ssml.clear_ssml()
    ssml_text = tts.ssml.add("Lets save to an audio file")
    # Demonstrate saving audio to a file
    output_file = Path(f"output_{service_name}.wav")
    tts.synth(ssml_text, str(output_file))
    # or you could do
    #tts.speak(ssml_text)

    # Change voice and test again if possible
    voices = tts.get_voices()
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
        tts.set_voice(new_voice_id, new_lang_id)
        ssml_text_part2 = tts.ssml.add("Continuing with a new voice!")
        tts.speak_streamed(ssml_text_part2)

def main() -> None:
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    # Load credentials
    load_credentials("credentials-private.json")
    services = ["elevenlabs", "google", "microsoft", "polly", "watson", "witai"] if service == "all" else [service]
    for svc in services:
        tts = create_tts_client(svc)
        #microsoft test with absolute value
        #tts.set_property("volume", "20")

        #google test with predefined words or decibels
        tts.set_property("volume", "5")
        tts.set_property("rate", "x-slow")
        tts.set_property("pitch", "x-low")
        test_tts_engine(tts, svc)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
