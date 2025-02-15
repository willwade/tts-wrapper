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
        print("Testing prosody...")
        ssml = tts.ssml.construct_prosody_tag(
            "This text should be spoken with modified prosody.",
            rate="slow",
            pitch="low",
            volume="soft"
        )
        tts.speak(ssml)
        time.sleep(3)
        
        # Test breaks
        print("\nTesting breaks...")
        text = (
            "This is a sentence<break time='1s'/>"
            "with a pause<break time='500ms'/>"
            "and another pause."
        )
        tts.speak(text)
        time.sleep(4)
        
        # Test voice changes
        print("\nTesting voice changes...")
        voices = tts.get_voices()
        if len(voices) > 1:
            voice = voices[1]  # Use second available voice
            ssml = (
                f"<voice name='{voice['id']}'>"
                "This text should be in a different voice."
                "</voice>"
            )
            tts.speak(ssml)
            time.sleep(3)
        
        # Test combined features
        print("\nTesting combined SSML features...")
        combined_ssml = (
            "<prosody rate='slow' pitch='low'>"
            "This is slow and low pitched"
            "<break time='500ms'/>"
            "Still slow and low"
            "</prosody>"
        )
        tts.speak(combined_ssml)
        time.sleep(4)
        
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
        
        # Try to find and use an English voice
        english_voices = [v for v in voices if "en" in v["language_codes"][0].lower()]
        if english_voices:
            voice = english_voices[0]
            print(f"\nSetting voice to: {voice['name']}")
            tts.set_voice(voice["id"])
            tts.speak("This is a test with a different voice.")
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

def test_streaming_and_control():
    """Test streaming with pause/resume/stop controls."""
    try:
        text = (
            "This is a long piece of text that we will use to test streaming "
            "and playback controls. We will pause in the middle, then resume, "
            "and finally stop before the end."
        )
        
        print("\nStarting streaming test...")
        tts.speak_streamed(text)
        
        # Give time for playback to start
        time.sleep(1)
        
        try:
            print("Pausing...")
            tts.pause()
            time.sleep(1)
            
            print("Resuming...")
            tts.resume()
            time.sleep(1)
            
            print("Stopping...")
            tts.stop()
        except Exception as control_error:
            print(f"Playback control error: {control_error}")
            # Ensure we stop the audio even if controls fail
            try:
                tts.stop()
            except Exception:
                pass
            
    except Exception as e:
        print(f"Error in streaming test: {e}")
    finally:
        # Always try to clean up the audio stream
        try:
            tts.stop()
        except Exception:
            pass

if __name__ == "__main__":
    print("Testing AVSynth TTS Engine")
    print("=========================")
    
    test_simple_speech()
    time.sleep(1)
    
    test_ssml()
    time.sleep(1)
    
    test_voice_selection()
    time.sleep(1)
    
    test_rate_control()
    time.sleep(1)
    
    test_volume_control()
    time.sleep(1)
    
    test_pitch_control()
    time.sleep(1)
    
    test_file_output()
    time.sleep(1)
    
    test_streaming_and_control()