from tts_wrapper import MicrosoftClient
from tts_wrapper.tts import AbstractTTS
import os
import tempfile
from pathlib import Path


def main():
    # Check if credentials are available
    subscription_key = os.environ.get("MS_SPEECH_KEY")
    region = os.environ.get("MS_SPEECH_REGION", "eastus")
    
    if not subscription_key:
        print("Microsoft Speech API key not found in environment variables.")
        print("Please set MS_SPEECH_KEY environment variable to test Microsoft TTS.")
        return
    
    # Initialize the client
    client = MicrosoftClient(credentials=(subscription_key, region))
    
    # Verify that the client inherits from AbstractTTS
    print(f"MicrosoftClient is an instance of AbstractTTS: {isinstance(client, AbstractTTS)}")
    
    # Test the get_voices method
    print("\nTesting get_voices method:")
    voices = client.get_voices()
    print(f"Found {len(voices)} voices")
    if voices:
        print(f"First voice: {voices[0]}")
    
    # Test different language code formats
    print("\nTesting different language code formats:")
    
    # ISO 639-3 format
    voices_iso = client.get_voices(langcodes="iso639_3")
    if voices_iso:
        print(f"ISO 639-3 format: {voices_iso[0]['language_codes']}")
    
    # Human-readable display names
    voices_display = client.get_voices(langcodes="display")
    if voices_display:
        print(f"Display names: {voices_display[0]['language_codes']}")
    
    # All formats
    voices_all = client.get_voices(langcodes="all")
    if voices_all:
        print(f"All formats: {voices_all[0]['language_codes']}")
    
    # Test synth_to_bytes method
    print("\nTesting synth_to_bytes method:")
    try:
        # Set a voice first
        if voices:
            client.set_voice(voices[0]["id"])
            
        # Synthesize text to bytes
        audio_bytes = client.synth_to_bytes("This is a test of the Microsoft TTS engine.")
        print(f"Generated {len(audio_bytes)} bytes of audio")
    except Exception as e:
        print(f"Error in synth_to_bytes: {e}")
    
    # Test synth method
    print("\nTesting synth method:")
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Synthesize text to file
        client.synth("This is a test of the Microsoft TTS engine.", temp_path)
        print(f"Generated audio file at {temp_path}")
        
        # Check if the file exists and has content
        file_size = Path(temp_path).stat().st_size
        print(f"Audio file size: {file_size} bytes")
    except Exception as e:
        print(f"Error in synth: {e}")


if __name__ == "__main__":
    main()
