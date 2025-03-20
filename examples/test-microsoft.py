import logging
import os
import time

from load_credentials import load_credentials
from tts_wrapper import MicrosoftClient, MicrosoftTTS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load credentials
load_credentials("credentials.json")
client = MicrosoftClient(
    credentials=(os.getenv("MICROSOFT_TOKEN"), os.getenv("MICROSOFT_REGION"))
)
tts = MicrosoftTTS(client)


def test_speech(text: str, description: str = "") -> None:
    """Helper to test speech with proper pausing."""
    if description:
        print(f"\n{description}")
    print(f"Speaking: {text}")
    tts.speak(text)
    time.sleep(3)  # Wait for speech to complete


print("\nTesting basic speech synthesis...")
test_speech("This is a test of basic speech synthesis.")

print("\nTesting speech rates...")
# Test predefined rates
for rate in ["x-slow", "slow", "medium", "fast", "x-fast"]:
    tts.set_property("rate", rate)
    test_speech(f"This is {rate} speech rate.", f"Testing {rate} rate")

# Test numeric rates
for rate in ["25", "50", "75"]:
    tts.set_property("rate", rate)
    test_speech(f"This is speech at {rate} percent speed.", f"Testing {rate}% rate")

print("\nTesting volume levels...")
for volume in ["20", "50", "100"]:
    tts.set_property("volume", volume)
    test_speech(f"This is volume level {volume}.", f"Testing volume {volume}")

print("\nTesting pitch levels...")
for pitch in ["x-low", "low", "medium", "high", "x-high"]:
    tts.set_property("pitch", pitch)
    test_speech(f"This is {pitch} pitch.", f"Testing {pitch} pitch")


def my_callback(word: str, start_time: float, end_time: float) -> None:
    """Called for each word as it's spoken."""
    duration = end_time - start_time
    print(
        f"Word: {word}, Start Time: {start_time}, End time: {end_time}, Duration: {duration:.3f}s"
    )


def on_start() -> None:
    """Called when audio playback starts."""
    print("Speech started")


def on_end() -> None:
    """Called when audio playback ends."""
    print("Speech ended")


print("\nTesting callbacks...")
try:
    text = "Hello, This is a word timing test"
    print(f"\nText to synthesize: {text}")

    # Connect the callbacks
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)

    # Start playback with callbacks
    tts.start_playback_with_callbacks(text, callback=my_callback)

    # Wait for speech to complete
    while tts.isplaying:
        time.sleep(0.1)

except Exception as e:
    print(f"Error in callback test: {e}")

print("\nAll tests complete!")
