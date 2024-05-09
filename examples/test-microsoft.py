from tts_wrapper import MicrosoftTTS, MicrosoftClient
import json

client = MicrosoftClient(credentials='key', region='region')
tts = MicrosoftTTS(client)


def my_callback(word: str, start_time: float):
        print(f'Word "{word}" spoken at {start_time} ms')


# pretty = json.dumps(tts.get_voices(), indent=4)
# print(pretty)
text = "Hello, world!"
ssml_text = tts.ssml.add(text)
#tts.speak(ssml_text)

try:
    text = "Hello, This is a word timing test"
    ssml_text = tts.ssml.add(text)
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
    # Now use `audio_content` as needed
except Exception as e:
    print(f"Error: {e}")