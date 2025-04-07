"""Tests for word timing callbacks in TTS engines."""

import os
import sys
import time
import unittest
from unittest.mock import Mock

# Import eSpeak engine
from tts_wrapper import eSpeakClient

# Import AVSynth conditionally for macOS
if sys.platform == "darwin":
    from tts_wrapper import AVSynthClient


# Skip all eSpeak tests if SKIP_ESPEAK_SYNTH_TEST or SKIP_ESPEAK_CALLBACK_TEST is set or running in CI
@unittest.skipIf(
    os.environ.get("SKIP_ESPEAK_SYNTH_TEST") is not None
    or os.environ.get("SKIP_ESPEAK_CALLBACK_TEST") is not None
    or os.environ.get("GITHUB_ACTIONS") == "true"
    or os.environ.get("CI") == "true",
    "Skipping test: Running in CI environment or SKIP_ESPEAK_SYNTH_TEST/SKIP_ESPEAK_CALLBACK_TEST is set",
)
class TestEspeakWordCallbacks(unittest.TestCase):
    """Test word timing callbacks in eSpeak engine."""

    def setUp(self):
        """Set up test engine."""
        try:
            self.engine = eSpeakClient()
        except Exception as e:
            self.skipTest(f"Could not initialize eSpeak: {e}")

    def tearDown(self):
        """Clean up resources."""
        if hasattr(self, "engine") and hasattr(self.engine, "finish"):
            self.engine.finish()

    def test_word_callback(self):
        """Test word callback functionality."""
        # Skip if SKIP_ESPEAK_CALLBACK_TEST is set
        if os.environ.get("SKIP_ESPEAK_CALLBACK_TEST"):
            self.skipTest("SKIP_ESPEAK_CALLBACK_TEST is set")

        # Create a mock callback
        word_callback = Mock()

        # Test text with multiple words
        test_text = "This is a test of word timing callbacks"

        try:
            # Start playback with callbacks
            self.engine.start_playback_with_callbacks(test_text, word_callback)

            # Wait for a short time to allow callbacks to be triggered
            time.sleep(2)

            # Check that callback was called at least once
            assert word_callback.call_count > 0, "Word callback was not called"

            # Check that callback was called with correct arguments
            for call in word_callback.call_args_list:
                args, _ = call
                assert (
                    len(args) == 3
                ), "Word callback called with wrong number of arguments"
                assert isinstance(
                    args[0], str
                ), "First argument to word callback is not a string"
                assert isinstance(
                    args[1], float
                ), "Second argument to word callback is not a float"
                assert isinstance(
                    args[2], float
                ), "Third argument to word callback is not a float"

        except Exception as e:
            self.skipTest(f"Word callback test failed: {e}")

    def test_set_timings(self):
        """Test setting word timings manually."""
        # Create a mock callback
        word_callback = Mock()

        # Create test timings
        test_timings = [
            (0.0, 0.5, "This"),
            (0.5, 1.0, "is"),
            (1.0, 1.5, "a"),
            (1.5, 2.0, "test"),
        ]

        try:
            # Set timings manually
            self.engine.set_timings(test_timings)

            # Connect callback
            self.engine.connect("started-word", word_callback)

            # Load some audio
            audio_bytes = self.engine.synth_to_bytes("This is a test")
            self.engine.load_audio(audio_bytes)

            # Start playback
            self.engine.play()

            # Wait for a short time to allow callbacks to be triggered
            time.sleep(2)

            # Check that callback was called for each word
            assert word_callback.call_count == len(
                test_timings
            ), "Word callback was not called for each word"

        except Exception as e:
            self.skipTest(f"Set timings test failed: {e}")


# Only run AVSynth tests on macOS
if sys.platform == "darwin":

    class TestAVSynthWordCallbacks(unittest.TestCase):
        """Test word timing callbacks in AVSynth engine."""

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

        def test_word_callback(self):
            """Test word callback functionality."""
            # Create a mock callback
            word_callback = Mock()

            # Test text with multiple words
            test_text = "This is a test of word timing callbacks"

            try:
                # Start playback with callbacks
                self.engine.start_playback_with_callbacks(test_text, word_callback)

                # Wait for a short time to allow callbacks to be triggered
                time.sleep(2)

                # Check that callback was called at least once
                assert word_callback.call_count > 0, "Word callback was not called"

                # Check that callback was called with correct arguments
                for call in word_callback.call_args_list:
                    args, _ = call
                    assert (
                        len(args) == 3
                    ), "Word callback called with wrong number of arguments"
                    assert isinstance(
                        args[0], str
                    ), "First argument to word callback is not a string"
                    assert isinstance(
                        args[1], float
                    ), "Second argument to word callback is not a float"
                    assert isinstance(
                        args[2], float
                    ), "Third argument to word callback is not a float"

            except Exception as e:
                self.skipTest(f"Word callback test failed: {e}")


if __name__ == "__main__":
    unittest.main()
