from tts_wrapper import PollyTTS, PollyClient
import json


def my_callback(word: str, start_time: float):
    print(f'Word "{word}" spoken at {start_time} ms')

def on_start():
    print('Speech started')

def on_end():
    print('Speech ended')


client = PollyClient(credentials=('region','aws_key_id', 'aws_access_key'))
tts = PollyTTS(client)
try:
    text = "Hello, This is a word timing test"
    ssml_text = tts.ssml.add(text)
    tts.connect('onStart', on_start)
    tts.connect('onEnd', on_end)
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
except Exception as e:
    print(f"Error: {e}")