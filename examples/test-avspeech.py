import logging
from tts_wrapper import AVSynthClient
import time

logging.basicConfig(level=logging.DEBUG)

# Initialize client
tts = AVSynthClient()

print("Testing AVSynth TTS Engine")
print("=========================\n")

print("\nTesting voice capabilities:")
voices = tts.get_voices()
print(f"\nFound {len(voices)} voices:")
for voice in voices[:20]:  # Show first 20 voices
    # Get first language code from the list
    language = voice["language_codes"][0] if voice["language_codes"] else "unknown"
    print(f"- {voice['name']} ({language}) [ID: {voice['id']}]")
    print(f"  Gender: {voice['gender']}")

print("\nTesting first voice: Gordon")
tts.set_voice("com.apple.ttsbundle.siri_Gordon_en_AU_compact")
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

print("\nTesting word timing callbacks...")
text = "This is a test of word timing callbacks in speech synthesis."
print(f"Text to synthesize: {text}")


def word_callback(word: str, start: float, end: float) -> None:
    """Called for each word as it's spoken."""
    duration = end - start
    print(
        f"Word: {word:12} Start: {start:5.2f}s  End: {end:5.2f}s  "
        f"Duration: {duration:5.2f}s"
    )


def on_start():
    """Called when audio playback starts."""
    print("\nAudio started playing")


def on_end():
    """Called when audio playback ends."""
    print("\nAudio finished playing")


# First synthesize to get word timings
print("\nSynthesizing speech and setting up word timing callbacks...")
audio_bytes = tts.synth_to_bytes(text)

# Print the word timings we got
print("\nWord timings received:")
for start, end, word in tts.timings:
    duration = end - start
    print(
        f"Word: {word:12} Start: {start:5.2f}s  End: {end:5.2f}s  "
        f"Duration: {duration:5.2f}s"
    )

# Now play with callbacks
print("\nStarting playback...")
tts.connect("onStart", on_start)
tts.connect("onEnd", on_end)
tts.load_audio(audio_bytes)
tts.play()

# Wait for audio to finish with a timeout
start_time = time.time()
timeout = 15  # 15 second timeout
while tts.isplaying and (time.time() - start_time) < timeout:
    time.sleep(0.1)

if tts.isplaying:
    print("\nWarning: Playback timed out")
    tts.stop()
else:
    print("\nPlayback completed successfully")

print("\nTests completed!")
