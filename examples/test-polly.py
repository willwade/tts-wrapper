import os
import sys
from unittest.mock import MagicMock

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tts_wrapper import PollyClient, PollyTTS

# Try to use the real client if credentials are available, otherwise use the mock
try:
    # Try to get credentials from environment variables
    region = os.getenv("POLLY_REGION")
    aws_key_id = os.getenv("POLLY_AWS_KEY_ID")
    aws_access_key = os.getenv("POLLY_AWS_ACCESS_KEY")
    
    if region and aws_key_id and aws_access_key:
        print("Using real PollyClient with AWS credentials")
        client = PollyClient(
            credentials=(region, aws_key_id, aws_access_key)
        )
        using_real_client = True
    else:
        raise ValueError("AWS credentials not found in environment variables")
        
except Exception as e:
    print(f"Could not initialize real PollyClient: {e}")
    print("Using MockPollyClient instead")
    
    # Create a mock PollyClient
    class MockPollyClient:
        def __init__(self, *args, **kwargs):
            self.last_voice_used = None
            print("Initialized MockPollyClient")
        
        def synth_with_timings(self, ssml, voice):
            self.last_voice_used = voice
            print(f"MockPollyClient.synth_with_timings called with voice: '{voice}'")
            # Return mock audio data and word timings
            return b"mock_audio_data", [
                (0.1, "This"),
                (0.3, "is"),
                (0.5, "a"),
                (0.7, "test")
            ]
        
        def get_voices(self):
            return [
                {"id": "Matthew", "name": "Matthew", "gender": "Male"},
                {"id": "Joanna", "name": "Joanna", "gender": "Female"},
                {"id": "Olivia", "name": "Olivia", "gender": "Female"},
                {"id": "Brian", "name": "Brian", "gender": "Male"},
                {"id": "Amy", "name": "Amy", "gender": "Female"}
            ]
    
    client = MockPollyClient()
    using_real_client = False

# Create a TTS instance with a specific voice (not Joanna)
print("Creating PollyTTS with voice='Matthew'")
tts = PollyTTS(client, voice="Matthew")

# Print the voice ID to verify it's set correctly
print(f"Voice ID set in TTS: {tts._voice}")

# Test synthesizing a simple text
print("\nSynthesizing speech with the selected voice...")
try:
    audio_bytes = tts.synth_to_bytes("This is a test of the Amazon Polly voice selection.")
    print(f"Generated audio length: {len(audio_bytes)} bytes")
    if not using_real_client:
        print(f"Last voice used in client: '{client.last_voice_used}'")
except Exception as e:
    print(f"Error during synthesis: {e}")

# List available voices
print("\nAvailable voices:")
try:
    voices = tts.get_voices()
    for voice in voices[:5]:  # Show first 5 voices
        print(f"ID: {voice['id']}, Name: {voice['name']}, Gender: {voice['gender']}")
except Exception as e:
    print(f"Error getting voices: {e}")

# Try another voice
print("\nChanging voice to Olivia...")
tts.set_voice("Olivia", "en-US")
print(f"New voice ID set in TTS: {tts._voice}")

try:
    audio_bytes = tts.synth_to_bytes("This is now using the Olivia voice.")
    print(f"Generated audio length: {len(audio_bytes)} bytes")
    if not using_real_client:
        print(f"Last voice used in client: '{client.last_voice_used}'")
except Exception as e:
    print(f"Error during synthesis with new voice: {e}")
