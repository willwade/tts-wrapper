import logging
from tts_wrapper.engines.avsynth import AVSynthClient, AVSynthTTS
import time

logging.basicConfig(level=logging.DEBUG)

# Initialize client
client = AVSynthClient()
tts = AVSynthTTS(client)

print("Testing AVSynth TTS Engine")
print("=========================\n")

print("\nTesting voice capabilities:")
voices = tts.get_voices()
print(f"\nFound {len(voices)} voices:")
for voice in voices[:20]:  # Show first 20 voices
    # Get first language code from the list
    language = voice['language_codes'][0] if voice['language_codes'] else 'unknown'
    print(f"- {voice['name']} ({language}) [ID: {voice['id']}]")
    print(f"  Gender: {voice['gender']}")

print("\nTesting first voice: Gordon")
tts.set_voice("com.apple.ttsbundle.siri_Gordon_en-AU_compact")
tts.set_property("rate", "50")  # 50% speed
tts.set_property("volume", "100")  # Full volume
tts.set_property("pitch", "1.0")
print("Speaking with Gordon's voice...")
tts.speak("This is a test with Gordon's voice.")

# Wait for audio to finish
while tts.isplaying:
    time.sleep(0.1)

print("\nTesting second voice: Karen")
tts.set_voice("com.apple.voice.compact.en-AU.Karen")
print("Speaking with Karen's voice...")
tts.speak("And this is a test with Karen's voice.")

# Wait for audio to finish
while tts.isplaying:
    time.sleep(0.1)

print("\nTesting streaming synthesis...")
text = "Testing streaming synthesis with word timing callbacks."
print(f"Text to synthesize: {text}")

def word_callback(word: str, start: float, end: float) -> None:
    print(f"Word: {word}, Start: {start:.2f}s, End: {end:.2f}s")

def on_start():
    print("Audio started playing")

def on_end():
    print("Audio finished playing")

# Connect callbacks
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)
tts.connect("on_word", word_callback)

# Start playback with callbacks
tts.start_playback_with_callbacks(text)

# Wait for audio to finish
while tts.isplaying:
    time.sleep(0.1)

print("\nTests completed!")