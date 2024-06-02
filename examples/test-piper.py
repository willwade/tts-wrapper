from tts_wrapper import PiperTTS, PiperClient
import json


def my_callback(word: str, start_time: float):
        print(f'Word "{word}" spoken at {start_time} ms')

client = PiperClient()
tts = PiperTTS(client)
# voices = tts.get_voices()
# print(voices)
ssml_text = tts.ssml.add(f"Continuing with a new voice using piper!")
tts.speak(ssml_text) 

# try:
#     tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
#     # Now use `audio_content` as needed
# except Exception as e:
#     print(f"Error: {e}")

