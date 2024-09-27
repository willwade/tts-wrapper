from tts_wrapper import MicrosoftTTS, MicrosoftClient
import json
import time
from pathlib import Path
import os
from load_credentials import load_credentials
import logging

# Load credentials
load_credentials("credentials.json")
client = MicrosoftClient(
    credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION"))
)
tts = MicrosoftTTS(client)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
# set timing on this


def on_start():
    first_word_time = time.time()
    logging.info(f"First word spoken after {first_word_time - start_time:.2f} seconds")


tts.connect("onStart", on_start)

tts.set_property("volume", "100")
tts.ssml.clear_ssml()
tts.set_property("rate", "medium")

text_read = f"Hello, this is a streamed test"
text_with_prosody = tts.construct_prosody_tag(text_read)
ssml_text = tts.ssml.add(text_with_prosody)
tts.pause_audio()
time.sleep(1)
print("ssml_test: ", ssml_text)

start_time = time.time()
tts.speak_streamed(ssml_text)
end_time = time.time()
logging.info(f"speak method took {end_time - start_time:.2f} seconds")
start_time = time.time()
tts.synth_to_file(ssml_text, "test-microsoft.mp3", "mp3")
end_time = time.time()
logging.info(f"speak stream method took {end_time - start_time:.2f} seconds")

start_time = time.time()
bytestream = tts.synth_to_bytestream(ssml_text)
# Save the audio bytestream to a file
with open("output_testazure.mp3", "wb") as f:
    f.write(bytestream.read())
print("Audio saved to output.mp3")
end_time = time.time()
logging.info(f"bytestream method took {end_time - start_time:.2f} seconds")
exit()
