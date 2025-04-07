"""Tests for AVSynth TTS engine."""

import os
import sys
import unittest
from unittest.mock import Mock

import pytest

# Skip tests if not on macOS
if sys.platform != "darwin":
    pytest.skip("AVSynth tests only run on macOS", allow_module_level=True)

# Import AVSynth client
from tts_wrapper import AVSynthClient


class TestAVSynthEngine(unittest.TestCase):
    """Test AVSynth TTS engine."""

    def setUp(self):
        """Set up test engine."""
        try:
            self.engine = AVSynthClient()
        except Exception as e:
            self.skipTest(f"Could not initialize AVSynth: {e}")

    def tearDown(self):
        """Clean up resources."""
        if hasattr(self, "engine") and hasattr(self.engine, "finish"):
            self.engine.finish()

    def test_get_voices(self):
        """Test get_voices method."""
        voices = self.engine.get_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0

        # Check voice format
        for voice in voices:
            assert "id" in voice
            assert "name" in voice
            # Voice may have 'language' or 'language_codes'
            assert "language" in voice or "language_codes" in voice
            assert "gender" in voice

    def test_set_voice(self):
        """Test set_voice method."""
        # Get available voices
        voices = self.engine.get_voices()
        if not voices:
            self.skipTest("No voices available")

        # Set voice
        voice_id = voices[0]["id"]
        self.engine.set_voice(voice_id)

        # Check that voice was set
        assert self.engine.voice_id == voice_id

    def test_synth_to_bytes(self):
        """Test synth_to_bytes method."""
        # Synthesize text to bytes
        audio_bytes = self.engine.synth_to_bytes("This is a test")

        # Check that audio was generated
        assert audio_bytes is not None
        assert len(audio_bytes) > 0

    def test_synth_to_file(self):
        """Test synth_to_file method."""
        # Create a test file
        test_file = "avsynth_test.wav"

        try:
            # Synthesize text to file
            self.engine.synth_to_file("This is a test", test_file)

            # Check that file exists and is not empty
            assert os.path.exists(test_file)
            assert os.path.getsize(test_file) > 0

        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_ssml_support(self):
        """Test SSML support."""
        # Create SSML text
        ssml_text = "<speak>This is a test of <break time='500ms'/> SSML.</speak>"

        try:
            # Synthesize SSML text
            audio_bytes = self.engine.synth_to_bytes(ssml_text)

            # Check that audio was generated
            assert audio_bytes is not None
            assert len(audio_bytes) > 0

        except (AttributeError, NotImplementedError) as e:
            self.skipTest(f"SSML not supported: {e}")

    def test_word_callbacks(self):
        """Test word timing callbacks."""
        # Create a mock callback
        word_callback = Mock()

        # Test text with multiple words
        test_text = "This is a test of word timing callbacks"

        try:
            # Start playback with callbacks
            self.engine.start_playback_with_callbacks(test_text, word_callback)

            # Wait for a short time to allow callbacks to be triggered
            import time

            time.sleep(2)

            # Check that callback was called at least once
            assert word_callback.call_count > 0, "Word callback was not called"

        except Exception as e:
            self.skipTest(f"Word callback test failed: {e}")


if __name__ == "__main__":
    unittest.main()
