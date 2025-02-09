import json
import logging
from pathlib import Path
from unittest import TestCase, skipIf

from tts_wrapper.engines.playht import PlayHTClient, PlayHTTTS


# Set up logging
logging.basicConfig(level=logging.DEBUG)


def get_credentials():
    """Get credentials from the private credentials file."""
    creds_path = Path(__file__).parent.parent / "keys" / "credentials-private.json"
    if not creds_path.exists():
        return None
    
    with open(creds_path) as f:
        creds = json.load(f)
        if "PlayHT" not in creds:
            return None
        return creds["PlayHT"]


@skipIf(get_credentials() is None, "PlayHT credentials not found")
class TestPlayHT(TestCase):
    """Test the Play.HT TTS engine."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class with credentials."""
        creds = get_credentials()
        cls.client = PlayHTClient((creds["api_key"], creds["user_id"]))
        cls.tts = PlayHTTTS(cls.client)

    def test_credentials(self):
        """Test that credentials are valid."""
        self.assertTrue(self.client.check_credentials())

    def test_get_voices(self):
        """Test getting available voices."""
        voices = self.client.get_voices()
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        
        # Check voice format
        voice = voices[0]
        self.assertIn("id", voice)
        self.assertIn("name", voice)
        self.assertIn("language_codes", voice)
        self.assertIn("gender", voice)
        
        # Check types
        self.assertIsInstance(voice["id"], str)
        self.assertIsInstance(voice["name"], str)
        self.assertIsInstance(voice["language_codes"], list)
        self.assertIsInstance(voice["gender"], str)
        
        # Log first voice for debugging
        logging.debug(f"First available voice: {voice}")

    def test_basic_synthesis(self):
        """Test basic text-to-speech synthesis."""
        text = "Hello, this is a test."
        audio = self.tts.synth_to_bytes(text)
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0)

    def test_synthesis_with_voice(self):
        """Test synthesis with a specific voice."""
        # Get first available voice
        voices = self.client.get_voices()
        voice_id = voices[0]["id"]
        logging.debug(f"Using voice ID: {voice_id}")
        
        # Set voice and synthesize
        self.tts.set_voice(voice_id)
        text = "Testing synthesis with a specific voice."
        audio = self.tts.synth_to_bytes(text)
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0)

    def test_synthesis_with_options(self):
        """Test synthesis with various options."""
        text = "Testing synthesis with options."
        options = {
            "speed": 1.2,
            "quality": "medium",
            "voice_engine": "PlayHT2.0"
        }
        
        # Set properties and synthesize
        for key, value in options.items():
            self.tts.set_property(key, value)
        
        audio = self.tts.synth_to_bytes(text)
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0)

    def test_ssml_handling(self):
        """Test that SSML is handled gracefully (stripped to plain text)."""
        ssml_text = '<speak>Hello <break time="1s"/> world!</speak>'
        audio = self.tts.synth_to_bytes(ssml_text)
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 0)

    def test_word_timings(self):
        """Test that word timings are estimated (not actual)."""
        text = "Testing word timings."
        self.tts.synth_to_bytes(text)
        timings = self.tts.timings
        
        # Check that we have timings
        self.assertGreater(len(timings), 0)
        
        # Check timing format (should be tuples of (start_time, end_time, word))
        timing = timings[0]
        self.assertIsInstance(timing, tuple)
        self.assertEqual(len(timing), 3)
        self.assertIsInstance(timing[0], float)  # start time
        self.assertIsInstance(timing[1], float)  # end time
        self.assertIsInstance(timing[2], str)    # word 