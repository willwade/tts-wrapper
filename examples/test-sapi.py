import time
from pathlib import Path

from tts_wrapper import SAPIEngine, SAPIClient

tts = SAPIEngine(sapi_version=5)

# long_text = '''"Title: "The Silent Truth"
# The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace.
# Chapter 1: A Quiet Morning
# "'''
# try:
#    tts.speak(long_text)
# except Exception:
#    pass


# ## calbacks
#
def my_callback(word: str, start_time: float, end_time: float) -> None:
    duration = end_time - start_time
    print(
        f"Word: '{word}' Started at {start_time:.3f}s, Ended at {end_time:.3f}s, Duration: {duration:.3f}s"
    )


def on_start() -> None:
    print("Starting")


def on_end() -> None:
    print("Ending")


try:
    text = "Hello, This is a word timing test"
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)
    tts.start_playback_with_callbacks(text, callback=my_callback)
except Exception:
    pass
