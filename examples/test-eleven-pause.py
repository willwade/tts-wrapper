from tts_wrapper import ElevenLabsTTS, ElevenLabsClient
import time
from pathlib import Path
import os
import threading
from load_credentials import load_credentials

# Load credentials
load_credentials("credentials-private.json")

client = ElevenLabsClient(credentials=(os.getenv("ELEVENLABS_API_KEY")))
tts = ElevenLabsTTS(client)
#tts.speak_streamed(
#    "The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace."
#)
#tts.pause_audio()
#input("Press enter to resume")
#tts.resume_audio()
#exit()
#print(client.get_voices())

long_text = '''"Title: "The Silent Truth"
The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace.
Chapter 1: A Quiet Morning.
Detective Emma Hayes had just finished her morning coffee when the phone rang."'''
# # # pausing
try:
    #ssml_text = tts.ssml.add(long_text)
    tts.stream_pausable(long_text)
    print("Does it reach here?")
    time.sleep(6)  # Let it speak for a bit
    print("Pausing for 4 seconds")
    tts.pause()
    time.sleep(4)  # Paused for 2 seconds
    print("Continue after 2 seconds")
    tts.resume()

except Exception as e:
    print(f"Error at pausing: {e}")



