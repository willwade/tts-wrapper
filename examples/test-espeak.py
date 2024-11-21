import os
import time
import logging
from pathlib import Path
from tts_wrapper import eSpeakClient, eSpeakTTS

logging.basicConfig(level=logging.DEBUG)

client = eSpeakClient()
tts = eSpeakTTS(client)

# Methods for specific tests
def test_pausing_and_resuming():
    """Test pausing, resuming, and stopping audio."""
    try:
        tts.set_output_device(2)
        ssml_text = tts.ssml.construct_prosody(
            "This is me speaking with espeak.",
            rate="fast",
            volume="medium",
            pitch="high",
            range="x-high",
        )
        tts.speak_streamed(ssml_text)

        # Pause and resume
        time.sleep(0.3)
        tts.pause_audio()
        time.sleep(0.5)
        tts.resume_audio()
        time.sleep(1)
        tts.stop_audio()
    except Exception as e:
        print(f"Error in pausing/resuming test: {e}")

def test_saving_audio():
    """Test saving synthesized audio to a file."""
    try:
        ssml_text = tts.ssml.add("A second sentence to save to an audio file", clear=True)
        output_file = Path(f"output_google.mp3")
        tts.synth(ssml_text, str(output_file), format="mp3")
        print(f"Audio content saved to {output_file}")
    except Exception as e:
        print(f"Error in saving audio: {e}")

def test_changing_voices():
    """Test changing voices and synthesizing text."""
    try:
        voices = tts.get_voices()
        if not voices:
            print("No voices available.")
            return

        print("Getting voices")
        for voice in voices[:4]:
            language_codes = voice.get("language_codes", [])
            display_name = voice.get("name", "Unknown voice")
            first_language_code = language_codes[0] if language_codes else "Unknown"
            print(f"{display_name} ({first_language_code}): {voice['id']}")

        if len(voices) > 1:
            new_voice_id = voices[1].get("id")
            new_lang_codes = voices[1].get("language_codes", [])
            new_lang_id = new_lang_codes[0] if new_lang_codes else "Unknown"
            print(f"Running with {new_voice_id} and {new_lang_id}")
            try:
                tts.set_voice(new_voice_id, new_lang_id)
                ssml_text = tts.ssml.add("Continuing with a new voice!", clear=True)
                tts.speak_streamed(ssml_text)
            except Exception as e:
                print(f"Error at setting voice: {e}")
    except Exception as e:
        print(f"Error in voice changing test: {e}")

def test_callbacks():
    """Test onStart, onEnd, and word callbacks."""
    def my_callback(word: str, start_time: float, end_time: float) -> None:
        duration = end_time - start_time
        print(f"Word: {word}, Start Time: {start_time}, End time: {end_time},  Duration: {duration:.3f}s")

    def on_start() -> None:
        print("Starting")

    def on_end() -> None:
        print("Ending")

    try:
        text = "Hello, This is a word timing test"
        tts.connect("onStart", on_start)
        tts.connect("onEnd", on_end)
        tts.start_playback_with_callbacks(text, callback=my_callback)
    except Exception as e:
        print(f"Error in callback test: {e}")

def test_volume_control():
    """Test volume control."""
    try:
        for volume in ["50", "100", "10"]:
            tts.set_property("volume", volume)
            print(f"Setting volume to {volume}")
            text = f"The current volume is at {volume}"
            text_with_prosody = tts.construct_prosody_tag(text)
            ssml_text = tts.ssml.add(text_with_prosody, clear=True)
            tts.speak_streamed(ssml_text)
            time.sleep(2)
    except Exception as e:
        print(f"Error in volume control test: {e}")

# Main execution
if __name__ == "__main__":
    # Uncomment any line below to test the corresponding functionality
    # test_pausing_and_resuming()
    # test_saving_audio()
    # test_changing_voices()
    test_callbacks()
    # test_volume_control()