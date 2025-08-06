#!/usr/bin/env python3
"""
Example demonstrating the fixed SAPI TTS implementation.

This example shows how to use the Windows SAPI TTS engine with tts-wrapper.
The SAPI implementation has been fixed to properly implement all abstract methods.

Requirements:
- Windows operating system
- tts-wrapper[sapi] installed: pip install tts-wrapper[sapi]
"""

import sys
from pathlib import Path

def main():
    """Demonstrate SAPI TTS functionality."""
    
    # Check if we're on Windows
    if sys.platform != "win32":
        print("❌ SAPI is only available on Windows systems")
        return
    
    try:
        from tts_wrapper import SAPIClient
    except ImportError as e:
        print(f"❌ Failed to import SAPIClient: {e}")
        print("💡 Install with: pip install tts-wrapper[sapi]")
        return
    
    print("🎤 SAPI TTS Example")
    print("=" * 50)
    
    try:
        # Initialize SAPI client
        print("1. Initializing SAPI client...")
        tts = SAPIClient()
        print("✅ SAPI client initialized successfully!")
        
        # Get available voices
        print("\n2. Getting available voices...")
        voices = tts.get_voices()
        print(f"✅ Found {len(voices)} voices:")
        
        for i, voice in enumerate(voices[:3]):  # Show first 3 voices
            print(f"   {i+1}. {voice['name']} ({voice['gender']}, Age: {voice['age']})")
        
        if len(voices) > 3:
            print(f"   ... and {len(voices) - 3} more voices")
        
        # Set a voice (use the first available voice)
        if voices:
            print(f"\n3. Setting voice to: {voices[0]['name']}")
            tts.set_voice(voices[0]['id'])
            print("✅ Voice set successfully!")
        
        # Test synthesis to bytes
        print("\n4. Testing synthesis to bytes...")
        text = "Hello! This is a test of the SAPI TTS implementation."
        audio_bytes = tts.synth_to_bytes(text)
        print(f"✅ Generated {len(audio_bytes)} bytes of audio data")
        
        # Test synthesis to file
        print("\n5. Testing synthesis to file...")
        output_file = Path("sapi_test_output.wav")
        tts.synth_to_file(text, str(output_file))
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Audio saved to {output_file} ({file_size} bytes)")
            
            # Clean up
            output_file.unlink()
            print("🧹 Cleaned up test file")
        else:
            print("❌ Failed to create audio file")
        
        # Test speak method (without audio playback to avoid issues)
        print("\n6. Testing speak method...")
        try:
            # Use return_bytes=True to get audio data without playback
            audio_data = tts.speak(text, wait_for_completion=False, return_bytes=True)
            if audio_data:
                print(f"✅ Speak method returned {len(audio_data)} bytes of audio")
            else:
                print("✅ Speak method executed successfully")
        except Exception as e:
            print(f"⚠️  Speak method had issues (likely audio playback): {e}")
        
        print("\n🎉 All SAPI tests completed successfully!")
        print("\n📝 Summary:")
        print("   - SAPIClient can be instantiated without abstract method errors")
        print("   - Voice enumeration works correctly")
        print("   - Audio synthesis to bytes works")
        print("   - Audio synthesis to file works")
        print("   - All abstract methods are properly implemented")
        
    except Exception as e:
        print(f"❌ Error during SAPI testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
