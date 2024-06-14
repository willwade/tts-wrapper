from tts_wrapper import WitAiTTS, WitAiClient
import json
import os 

def my_callback(word: str, start_time: float):
        print(f'Word "{word}" spoken at {start_time} ms')

client = WitAiClient(credentials=(os.getenv('WITAI_TOKEN')))
tts = WitAiTTS(client)
# voices = tts.get_voices()
# print(voices)

try:
    text = "Hello, This is a word timing test"
    ssml_text = (tts.ssml
                 .say_as("Hello,", interpret_as="greeting")
                 .break_(time="500ms")
                 .emphasis("This is a word timing test", level="strong")
                 .prosody("Let's slow this part down", rate="slow")
                 .add('This is a normal sentence'))
    tts.start_playback_with_callbacks(ssml_text, callback=my_callback)
    # Now use `audio_content` as needed
except Exception as e:
    print(f"Error: {e}")

