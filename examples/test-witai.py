import os

from load_credentials import load_credentials

from tts_wrapper import WitAiClient, WitAiTTS

# Load credentials
load_credentials("credentials.json")


def my_callback(word: str, start_time: float) -> None:
    pass


client = WitAiClient(credentials=(os.getenv("WITAI_TOKEN")))
tts = WitAiTTS(client)
# voices = tts.get_voices()
# print(voices)


def my_callback(word: str, start_time: float, end_time: float) -> None:
    end_time - start_time


try:
    tts.set_output_device(2)
    text = "Hello, This is a word timing test"
    ssml_text = (
        tts.ssml.say_as("Hello,", interpret_as="greeting")
        .break_(time="500ms")
        .emphasis("This is a word timing test", level="strong")
        .prosody("Let's slow this part down", rate="slow")
        .add("This is a normal sentence")
    )
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
    # Now use `audio_content` as needed
except Exception:
    pass


def my_callback(word: str, start_time: float, end_time: float) -> None:
    end_time - start_time


def on_start() -> None:
    pass


def on_end() -> None:
    pass


try:
    text = "Hello, This is a word timing test"
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)
    tts.start_playback_with_callbacks(text, callback=my_callback)
except Exception:
    pass

try:
    text = "Test saving audio to file"
    tts.synth_to_file(text, "test-witai.wav", "wav")
except Exception:
    pass
