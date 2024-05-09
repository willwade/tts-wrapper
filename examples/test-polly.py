from tts_wrapper import PollyTTS, PollyClient
import json

def my_callback(word: str, start_time: float):
        print(f'Word "{word}" spoken at {start_time} ms')

client = PollyClient(credentials=('region','key', 'privatekey'))
tts = PollyTTS(client)
try:
    text = "Hello, This is a word timing test"
    ssml_text = tts.ssml.add(text)
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
    # Now use `audio_content` as needed
except Exception as e:
    print(f"Error: {e}")

