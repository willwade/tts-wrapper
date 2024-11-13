import os
import time

from load_credentials import load_credentials

from tts_wrapper import GoogleClient, GoogleTTS

# Load credentials
load_credentials("credentials.json")

client = GoogleClient(credentials=os.getenv("GOOGLE_CREDS_PATH"))

tts = GoogleTTS(client)
try:
    text = "This is a pause and resume test. The text will be longer, depending on where the pause and resume works"
    audio_bytes = tts.synth_to_bytes(text)
    tts.load_audio(audio_bytes)
    tts.play(2)
    tts.pause(3)
    tts.resume()
    time.sleep(6)
finally:
    tts.cleanup()
