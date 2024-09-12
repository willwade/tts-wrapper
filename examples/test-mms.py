from tts_wrapper import MMSTTS, MMSClient
import json
import time
from pathlib import Path
import os

# Initialize the client with only the lang parameter
client = MMSClient(('spa'))
tts = MMSTTS(client)
text = "hello world i like monkeys"
tts.speak(text)

print(text)

# volume control test
print("Volume setting is from 0-100")
text_read = ""
try:
    tts.set_property("volume", "50")
    print("Setting volume at 50")
    text_read = f"The current volume is at fifty"
    text_with_prosody = tts.construct_prosody_tag(text_read)
    ssml_text = tts.ssml.add(text_with_prosody)
    print("ssml_text", ssml_text)
    tts.speak(ssml_text)
    time.sleep(0.5)
    
    #clear ssml so the previous text is not repeated

    tts.set_property("volume", "100")
    print("Setting volume at 100")
    text_read = f"The current volume is at a hundred"
    text_with_prosody = tts.construct_prosody_tag(text_read)
    ssml_text = tts.ssml.add(text_with_prosody)
    print("ssml_text", ssml_text)

    tts.speak(ssml_text)
    time.sleep(0.5)

    tts.set_property("volume", "10")
    print("Setting volume at 10")
    text_read = f"The current volume is at ten"
    text_with_prosody = tts.construct_prosody_tag(text_read)        
    ssml_text = tts.ssml.add(text_with_prosody)
    print("ssml_text", ssml_text)

    tts.speak(ssml_text)
    time.sleep(0.5)

    print("save to file")
    tts.synth_to_file(ssml_text, "mms_output.wav", "wav")
except Exception as e:
    print(f"Error at setting volume: {e}")