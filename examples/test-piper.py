
from tts_wrapper import PiperClient, PiperTTS


def my_callback(word: str, start_time: float) -> None:
        pass

client = PiperClient()
tts = PiperTTS(client)
# voices = tts.get_voices()
# print(voices)
tts.set_output_device(2)
ssml_text = tts.ssml.add("Continuing with a new voice using piper!")
tts.speak(ssml_text)

# try:
#     tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
#     # Now use `audio_content` as needed
# except Exception as e:
#     print(f"Error: {e}")

