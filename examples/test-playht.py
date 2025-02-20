import os
import sys
import time
from pathlib import Path

from tts_wrapper import PlayHTClient, PlayHTTTS

# Get credentials from environment
api_key = os.getenv("PLAYHT_API_KEY")
user_id = os.getenv("PLAYHT_USER_ID")

if not api_key or not user_id:
    raise ValueError(
        "PLAYHT_API_KEY and PLAYHT_USER_ID environment variables must be set"
    )

# Initialize client and TTS
client = PlayHTClient(credentials=(api_key, user_id))
tts = PlayHTTTS(client)


# Define a callback for when audio starts playing
def on_start():
    print("Audio started playing")


def on_end():
    print("Audio finished playing")


# Connect callbacks
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)

# Test synthesis
print("Starting audio playback...")
tts.speak_streamed(
    "The town of Brookhollow was the kind of place where people left their "
    "doors unlocked and trusted everyone they met. Tucked away in the rolling "
    "hills of the countryside, it was a town where time seemed to stand still. "
    "But on a crisp October morning, something sinister shattered the peace.",
)

# Wait a moment for audio to start
time.sleep(2)
print("Pausing audio...")
tts.pause()
input("Press enter to resume")
tts.resume()

# Wait for audio to finish
while tts.isplaying:
    time.sleep(0.1)

print("Test complete")

long_text = '''"Title: "The Silent Truth"
The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace.
Chapter 1: A Quiet Morningully. There were no signs of a struggle, and nothing seemed out of place. It was clean. Too clean."'''
# # # pausing
try:
    ssml_text = tts.ssml.add(long_text)
    tts.speak_streamed(str(ssml_text))
    # Pause after 5 seconds
    time.sleep(0.3)
    tts.pause()
    # Resume after 3 seconds
    time.sleep(0.5)
    tts.resume()
    # Stop after 2 seconds
    time.sleep(1)
    tts.stop()
except Exception as e:
    print(f"Error in playback control: {e}")
    pass

time.sleep(3)

# Demonstrate saving audio to a file
try:
    text = "This is me speaking with Speak function and PlayHT"
    output_file = "output_playht.wav"
    tts.speak_streamed(text, output_file, "wav")
except Exception as e:
    print(f"Error saving audio: {e}")

time.sleep(3)

# Volume control test
print("Volume setting is from 0-100")
try:
    # Test with 50% volume
    tts.set_property("volume", "50")
    print("Setting volume at 50")
    text = "The current volume is at 50 percent"
    tts.speak_streamed(text)
    time.sleep(2)

    # Test with 100% volume
    tts.set_property("volume", "100")
    print("Setting volume at 100")
    text = "The current volume is at 100 percent"
    tts.speak_streamed(text)
    time.sleep(2)

    # Test with 10% volume
    tts.set_property("volume", "10")
    print("Setting volume at 10")
    text = "The current volume is at 10 percent"
    tts.speak_streamed(text)
    time.sleep(2)

except Exception as e:
    print(f"Error in volume control: {e}")

try:
    voices = tts.get_voices()
except Exception as e:
    print(f"Error at getting voices: {e}")

print("Getting voices")
for voice in voices[:4]:  # Show details for first four voices
    language_codes = voice.get("language_codes", [])
    display_name = voice.get("name", "Unknown voice")
    # Safely get the first language code, default to 'Unknown' if not available
    first_language_code = language_codes[0] if language_codes else "Unknown"
    print(f"{display_name} ({first_language_code}): {voice['id']}")
# Change voice if more than one is available
if len(voices) > 1:
    new_voice_id = voices[1].get("id")
    # Attempt to get the first language from the second voice's language codes
    new_lang_codes = voices[1].get("language_codes", [])
    new_lang_id = new_lang_codes[0] if new_lang_codes else "Unknown"
    print(f"Running with {new_voice_id} and {new_lang_id}")
    try:
        tts.set_voice(new_voice_id, new_lang_id)
    except Exception as e:
        print(f"Error at setting voice: {e}")
    ssml_text_part2 = tts.ssml.add("Continuing with a new voice!")
    tts.speak_streamed(ssml_text_part2)

time.sleep(3)

## calbacks


def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: {word}, Duration: {duration:.3f}s")


def on_start():
    print("Speech started")


def on_end():
    print("Speech ended")


try:
    text = "Hello, This is a word timing test"
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)
    tts.start_playback_with_callbacks(text, callback=my_callback)
except Exception as e:
    print(f"Error at callbacks: {e}")

time.sleep(3)
