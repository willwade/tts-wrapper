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
