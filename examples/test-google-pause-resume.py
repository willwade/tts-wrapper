from tts_wrapper import GoogleTTS, GoogleClient
import json
import time
from pathlib import Path
import os
from load_credentials import load_credentials
# Load credentials
load_credentials('credentials.json')

client = GoogleClient(credentials=os.getenv('GOOGLE_CREDS_PATH'))

tts = GoogleTTS(client)
try:
    text = "This is a pause and resume test. The text will be longer, depending on where the pause and resume works"
    audio_bytes = tts.synth_to_bytes(text)
    tts.load_audio(audio_bytes)
    print("Play audio for 3 seconds")
    tts.play(2)
    tts.pause(3)
    tts.resume()
    time.sleep(6)
finally:
    tts.cleanup()
