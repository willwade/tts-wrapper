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
        ssml_text = tts.ssml.add(
            "A second sentence to save to an audio file", clear=True
        )
        output_file = Path(f"output_google.mp3")
        tts.synth(ssml_text, str(output_file), format="mp3")
        print(f"Audio content saved to {output_file}")
    except Exception as e:
        print(f"Error in saving audio: {e}")


def test_changing_voices():
    """Test changing voices and synthesizing text."""
    try:
        # Get the list of available voices
        voices = tts.get_voices()
        logging.debug(f"Voices: {voices}")
        if not voices:
            print("No voices available.")
            return

        print("Getting voices...")
        english_voices = [
            voice for voice in voices if "English" in (voice.get("name") or [])
        ]

        if not english_voices:
            print("No English voices available.")
            return

        # Select and test the first four English voices
        for i, voice in enumerate(english_voices[:4], start=1):
            display_name = voice.get("name", "Unknown voice")
            voice_id = voice.get("id", "Unknown ID")
            language_codes = voice.get("language_codes", [])
            first_language_code = language_codes[0] if language_codes else "Unknown"

            print(
                f"Testing voice {i}: {display_name} ({first_language_code}) - ID: {voice_id}"
            )
            try:
                # Set the current voice and synthesize text
                tts.set_voice(voice_id, first_language_code)
                tts.speak_streamed(
                    f"This is voice {i}. Testing the {display_name} voice."
                )
            except Exception as e:
                print(f"Error testing voice {i}: {e}")
    except Exception as e:
        print(f"Error in voice changing test: {e}")


def test_callbacks():
    """Test onStart, onEnd, and word callbacks."""

    def my_callback(word: str, start_time: float, end_time: float) -> None:
        duration = end_time - start_time
        print(
            f"Word: {word}, Start Time: {start_time}, End time: {end_time},  Duration: {duration:.3f}s"
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
    test_changing_voices()
    # test_callbacks()
    # test_volume_control()
