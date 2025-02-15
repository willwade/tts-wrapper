import time
import logging
from pathlib import Path
from tts_wrapper import AVSynthClient, AVSynthTTS

logging.basicConfig(level=logging.DEBUG)

client = AVSynthClient()
tts = AVSynthTTS(client)

def test_simple_speech():
    """Test simple speech synthesis."""
    try:
        tts.speak("This is a simple test of the AVSynth TTS engine.")
    except Exception as e:
        print(f"Error in simple speech test: {e}")

def test_ssml():
    """Test SSML functionality."""
    try:
        print("\nTesting SSML features:")
        
        # Test basic SSML with prosody
        print("Testing basic prosody...")
        text = "This text should be spoken slowly."
        ssml = f"<speak><prosody rate='slow'>{text}</prosody></speak>"
        print(f"SSML being sent: {ssml}")
        tts.speak(ssml)
        time.sleep(3)
        
        # Test simple break
        print("\nTesting simple break...")
        text = "<speak>This is a sentence<break time='1s'/>after a pause.</speak>"
        print(f"SSML being sent: {text}")
        tts.speak(text)
        time.sleep(4)
        
        # Test simple voice change
        print("\nTesting voice change...")
        voices = tts.get_voices()
        if len(voices) > 1:
            voice = next((v for v in voices if "en" in v["language_codes"][0].lower()), voices[0])
            text = f"<speak><voice name='{voice['id']}'>This text should be in a different voice.</voice></speak>"
            print(f"SSML being sent: {text}")
            tts.speak(text)
            time.sleep(3)
        
    except Exception as e:
        print(f"Error in SSML test: {e}")

def test_voice_selection():
    """Test voice selection and listing."""
    try:
        # Get available voices
        voices = tts.get_voices()
        print("\nAvailable voices:")
        for voice in voices:
            print(f"- {voice['name']} ({voice['language_codes'][0]})")
        
        # Try to find an English voice
        english_voices = [v for v in voices if "en" in v["language_codes"][0].lower()]
        if english_voices:
            voice = english_voices[0]
            print(f"\nSetting voice to: {voice['name']} ({voice['id']})")
            tts.set_voice(voice["id"])
            # Test with simple text first
            print("Testing with simple text...")
            tts.speak("This is a test with an English voice.")
            time.sleep(2)
        else:
            print("No English voices found!")

    except Exception as e:
        print(f"Error in voice selection test: {e}")

def test_rate_control():
    """Test speech rate control."""
    try:
        # Test different rates
        rates = ["x-slow", "slow", "medium", "fast", "x-fast"]
        for rate in rates:
            print(f"\nTesting rate: {rate}")
            tts.set_property("rate", rate)
            tts.speak(f"This is speech at {rate} rate.")
            time.sleep(2)  # Wait for speech to complete
    except Exception as e:
        print(f"Error in rate control test: {e}")

def test_volume_control():
    """Test volume control."""
    try:
        volumes = ["10", "50", "100"]
        for volume in volumes:
            print(f"\nTesting volume: {volume}")
            tts.set_property("volume", volume)
            tts.speak(f"This is speech at volume {volume}.")
            time.sleep(2)
    except Exception as e:
        print(f"Error in volume control test: {e}")

def test_pitch_control():
    """Test pitch control."""
    try:
        pitches = ["x-low", "low", "medium", "high", "x-high"]
        for pitch in pitches:
            print(f"\nTesting pitch: {pitch}")
            tts.set_property("pitch", pitch)
            tts.speak(f"This is speech with {pitch} pitch.")
            time.sleep(2)
    except Exception as e:
        print(f"Error in pitch control test: {e}")

def test_file_output():
    """Test saving speech to a file."""
    try:
        output_file = Path("output_avsynth.wav")
        text = "This is a test of saving speech to a file."
        tts.synth_to_file(text, str(output_file))
        print(f"\nSaved audio to {output_file}")
    except Exception as e:
        print(f"Error in file output test: {e}")

def cleanup_audio():
    """Safely cleanup audio resources."""
    try:
        tts.stop()
    except Exception as e:
        if "Stream already closed" not in str(e) and "Internal PortAudio error" not in str(e):
            logging.error("Error during cleanup: %s", e)

def test_streaming_and_control():
    """Test streaming with pause/resume/stop controls."""
    try:
        # Very short text for testing
        text = "Testing streaming."
        
        print("\nStarting streaming test...")
        tts.speak_streamed(text)
        
        # Quick control test
        time.sleep(0.3)
        print("Stopping...")
        cleanup_audio()
            
    except Exception as e:
        if "PortAudio" in str(e):
            print("Audio device error - this is usually not critical")
            logging.debug("Audio error details: %s", e)
        else:
            print(f"Error in streaming test: {e}")
    finally:
        cleanup_audio()

def test_callbacks():
    """Test word timing callbacks."""
    def my_callback(word: str, start_time: float, end_time: float) -> None:
        duration = end_time - start_time
        print(f"Word: {word}, Duration: {duration:.3f}s")

    def on_start() -> None:
        print("Speech started")

    def on_end() -> None:
        print("Speech ended")

    try:
        print("\nTesting callbacks...")
        text = "Testing word callbacks."
        tts.connect("onStart", on_start)
        tts.connect("onEnd", on_end)
        tts.start_playback_with_callbacks(text, callback=my_callback)
        time.sleep(2)
    except Exception as e:
        if "PortAudio" in str(e):
            print("Audio device error - this is usually not critical")
            logging.debug("Audio error details: %s", e)
        else:
            print(f"Error in callback test: {e}")
    finally:
        cleanup_audio()

if __name__ == "__main__":
    print("Testing AVSynth TTS Engine")
    print("=========================")
    
    try:
        # Basic speech test
        test_simple_speech()
        time.sleep(0.5)
        
        # Test streaming with controls
        test_streaming_and_control()
        time.sleep(0.5)
        
        # Test callbacks (most important for current task)
        print("\nTesting word timing callbacks...")
        test_callbacks()
        
        print("\nTests completed!")
    
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    finally:
        cleanup_audio()