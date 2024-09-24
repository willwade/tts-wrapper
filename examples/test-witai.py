from tts_wrapper import WitAiTTS, WitAiClient
import json
import os 
import os
from load_credentials import load_credentials

# Load credentials
load_credentials('credentials.json')

def my_callback(word: str, start_time: float):
        print(f'Word "{word}" spoken at {start_time} ms')

client = WitAiClient(credentials=(os.getenv('WITAI_TOKEN')))
tts = WitAiTTS(client)
# voices = tts.get_voices()
# print(voices)

def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: {word}, Duration: {duration:.3f}s")


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


def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: {word}, Duration: {duration:.3f}s")

def on_start():
    print('Speech started')

def on_end():
    print('Speech ended')

try:
    #text = "Hello, This is a word timing test"
    #tts.connect('onStart', on_start)
    #tts.connect('onEnd', on_end)
    #tts.start_playback_with_callbacks(text, callback=my_callback)
    text = "This is a speak streamed function test using WITAI"
    tts.speak_streamed(text)
except Exception as e:
    print(f"Error at callbacks: {e}")

try:
    text = "Test saving audio to file"
    print(text)
    tts.synth_to_file(text, "test-witai.wav", "wav")
except Exception as e:
    print(f"Error saving audio to file")
