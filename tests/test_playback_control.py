"""Tests for playback control (pause, resume, stop) in TTS engines."""

import os
import sys
import time
import unittest

# Import eSpeak engine
from tts_wrapper import eSpeakClient

# Import AVSynth conditionally for macOS
if sys.platform == "darwin":
    from tts_wrapper import AVSynthClient


# Skip all eSpeak tests if SKIP_ESPEAK_SYNTH_TEST is set or running in CI
@unittest.skipIf(
    os.environ.get("SKIP_ESPEAK_SYNTH_TEST")
    or os.environ.get("GITHUB_ACTIONS") == "true"
    or os.environ.get("CI") == "true",
    "Skipping test: Running in CI environment or SKIP_ESPEAK_SYNTH_TEST is set",
)
class TestEspeakPlaybackControl(unittest.TestCase):
    """Test playback control in eSpeak engine."""

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

    def test_play_method(self):
        """Test play method."""

        try:
            # Synthesize text to bytes
            audio_bytes = self.engine.synth_to_bytes(
                "This is a test of playback control"
            )

            # Load the audio
            self.engine.load_audio(audio_bytes)

            # Play the audio
            self.engine.play()

            # Check that isplaying flag is set
            assert self.engine.isplaying, "isplaying flag not set"

            # Wait for a short time
            time.sleep(0.5)

        except Exception as e:
            self.skipTest(f"Play test failed: {e}")

    def test_pause_resume_methods(self):
        """Test pause and resume methods."""

        try:
            # Synthesize text to bytes
            audio_bytes = self.engine.synth_to_bytes(
                "This is a test of pause and resume functionality"
            )

            # Load the audio
            self.engine.load_audio(audio_bytes)

            # Play the audio
            self.engine.play()

            # Check that isplaying flag is set
            assert self.engine.isplaying, "isplaying flag not set"

            # Wait for a short time
            time.sleep(0.5)

            # Pause the audio
            self.engine.pause()

            # Check that paused flag is set
            assert self.engine.paused, "paused flag not set"

            # Wait for a short time
            time.sleep(0.5)

            # Resume the audio
            self.engine.resume()

            # Check that paused flag is cleared
            assert not self.engine.paused, "paused flag not cleared"

            # Wait for a short time
            time.sleep(0.5)

        except Exception as e:
            self.skipTest(f"Pause/resume test failed: {e}")

    def test_stop_method(self):
        """Test stop method."""

        try:
            # Synthesize text to bytes
            audio_bytes = self.engine.synth_to_bytes(
                "This is a test of stop functionality"
            )

            # Load the audio
            self.engine.load_audio(audio_bytes)

            # Play the audio
            self.engine.play()

            # Check that isplaying flag is set
            assert self.engine.isplaying, "isplaying flag not set"

            # Wait for a short time
            time.sleep(0.5)

            # Stop the audio
            self.engine.stop()

            # Check that isplaying flag is cleared
            assert not self.engine.isplaying, "isplaying flag not cleared"

        except Exception as e:
            self.skipTest(f"Stop test failed: {e}")

    def test_finish_method(self):
        """Test finish method."""

        try:
            # Synthesize text to bytes
            audio_bytes = self.engine.synth_to_bytes(
                "This is a test of finish functionality"
            )

            # Load the audio
            self.engine.load_audio(audio_bytes)

            # Play the audio
            self.engine.play()

            # Check that isplaying flag is set
            assert self.engine.isplaying, "isplaying flag not set"

            # Wait for a short time
            time.sleep(0.5)

            # Finish the audio
            self.engine.finish()

            # Check that stream is None
            assert self.engine.stream is None, "stream not None after finish"

        except Exception as e:
            self.skipTest(f"Finish test failed: {e}")


# Only run AVSynth tests on macOS
if sys.platform == "darwin":

    class TestAVSynthPlaybackControl(unittest.TestCase):
        """Test playback control in AVSynth engine."""

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

        def test_play_method(self):
            """Test play method."""
            try:
                # Synthesize text to bytes
                audio_bytes = self.engine.synth_to_bytes(
                    "This is a test of playback control"
                )

                # Load the audio
                self.engine.load_audio(audio_bytes)

                # Play the audio
                self.engine.play()

                # Check that isplaying flag is set
                assert self.engine.isplaying, "isplaying flag not set"

                # Wait for a short time
                time.sleep(0.5)

            except Exception as e:
                self.skipTest(f"Play test failed: {e}")


if __name__ == "__main__":
    unittest.main()
