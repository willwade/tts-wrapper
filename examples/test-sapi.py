import time
from pathlib import Path

from tts_wrapper import SAPIEngine, SAPIClient

tts = SAPIEngine(sapi_version=4)

long_text = '''"Title: "The Silent Truth"
The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace.
Chapter 1: A Quiet Morning
"'''
try:
    #tts.set_property("rate", 8000)
    #tts.set_property("volume", 100)
    tts.speak(long_text)
except Exception:
    pass