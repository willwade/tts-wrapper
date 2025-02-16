import logging
import sys
import numpy as np
import sounddevice as sd
from tts_wrapper import AVSynthClient, AVSynthTTS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def play_audio_stream(tts, text: str):
    """Example of manual audio playback using raw audio data."""
    print(f"\nPlaying text: {text}")
    
    # Get the raw audio data
    audio_data = tts.synth_to_bytes(text)
    
    # Convert to numpy array for playback
    samples = np.frombuffer(audio_data, dtype=np.int16)
    
    # Play the audio
    print("Starting playback...")
    sd.play(samples, samplerate=tts.audio_rate)
    sd.wait()  # Wait until audio is finished playing
    print("Playback complete")

def play_audio_chunked(tts, text: str, chunk_size: int = 4096):
    """Example of manual chunked audio playback using a continuous stream."""
    print(f"\nPlaying text (chunked): {text}")
    
    # Get the raw audio data
    audio_data = tts.synth_to_bytes(text)
    
    # Create a continuous stream
    stream = sd.OutputStream(
        samplerate=tts.audio_rate,
        channels=1,  # Mono audio
        dtype=np.int16
    )
    
    print("Starting chunked playback...")
    with stream:
        # Process in chunks
        for i in range(0, len(audio_data), chunk_size):
            # Get next chunk
            chunk = audio_data[i:i + chunk_size]
            
            # Ensure chunk size is even (for 16-bit audio)
            if len(chunk) % 2 != 0:
                chunk = chunk[:-1]
                
            # Convert chunk to numpy array
            samples = np.frombuffer(chunk, dtype=np.int16)
            
            # Write the chunk to the stream
            stream.write(samples)
        
    print("Chunked playback complete")

def main():
    print("\nTesting AVSynth TTS Engine with Manual Audio Processing")
    print("=================================================\n")

    # Check if we're on macOS
    if sys.platform != "darwin":
        print("Error: AVSynth is only available on macOS")
        return

    try:
        # Initialize client and TTS
        print("Initializing AVSynth...")
        client = AVSynthClient()
        tts = AVSynthTTS(client)
        
        # Get available voices
        voices = tts.get_voices()
        if not voices:
            print("Error: No voices found!")
            return
            
        # Find an English voice
        english_voice = next(
            (v for v in voices if any('en' in code for code in v['language_codes'])),
            voices[0]  # fallback to first voice if no English voice found
        )
        
        print(f"\nUsing voice: {english_voice['name']} ({english_voice['id']})")
        tts.set_voice(english_voice['id'])
        
        # Test with different voice properties
        print("\nTesting different playback methods:")
        
        # Test 1: Direct playback
        tts.set_property("rate", "medium")
        tts.set_property("volume", "100")
        play_audio_stream(tts, "This is a test of direct audio playback.")
        
        # Test 2: Chunked playback
        tts.set_property("rate", "medium")
        play_audio_chunked(tts, "This is a test of chunked audio playback.")

    except Exception as e:
        print(f"Error during testing: {str(e)}")
        logging.exception("Detailed error information:")
    finally:
        if 'tts' in locals():
            tts.cleanup()

if __name__ == "__main__":
    main() 