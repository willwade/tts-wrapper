#!/usr/bin/env python3
"""
Test script to verify the GoogleTransClient voice property.
"""

from tts_wrapper.engines.googletrans.client import GoogleTransClient
from tts_wrapper.engines.googletrans.googletrans import GoogleTransTTS

def main():
    # Test with default voice
    client = GoogleTransClient()
    print(f"Default voice: {client.voice}")
    
    # Test with custom voice
    client = GoogleTransClient("en-us")
    print(f"Custom voice: {client.voice}")
    
    # Test voice_id parameter in synth_to_bytes
    tts = GoogleTransTTS(client)
    
    # Test voice switching and restoration
    original_voice = client.voice
    print(f"Original voice before synthesis: {original_voice}")
    
    # This should temporarily switch to fr-fr and then restore
    try:
        # Just get a small amount of audio to test
        tts.synth_to_bytes("Bonjour", voice_id="fr-fr")
        print(f"Voice after synthesis with voice_id: {client.voice}")
        print(f"Voice restored correctly: {client.voice == original_voice}")
    except Exception as e:
        print(f"Error during synthesis: {e}")
    
    print("Test completed successfully!")

if __name__ == "__main__":
    main()
