"""Tests for SSML support in TTS engines."""

import os
import sys
import unittest

# Import engines that don't require credentials
from tts_wrapper import eSpeakClient

# Import AVSynth conditionally for macOS
if sys.platform == "darwin":
    from tts_wrapper import AVSynthClient


class TestEspeakSSML(unittest.TestCase):
    """Test SSML support in eSpeak engine."""

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

    def test_ssml_detection(self):
        """Test SSML detection."""
        # Test with SSML text
        ssml_text = "<speak>This is SSML</speak>"
        assert self.engine._is_ssml(ssml_text)

        # Test with plain text
        plain_text = "This is plain text"
        assert not self.engine._is_ssml(plain_text)

    def test_ssml_synthesis(self):
        """Test SSML synthesis."""
        # Skip if SKIP_ESPEAK_SYNTH_TEST is set
        if os.environ.get("SKIP_ESPEAK_SYNTH_TEST"):
            self.skipTest("SKIP_ESPEAK_SYNTH_TEST is set")

        # Create SSML text with various tags
        ssml_text = self.engine.ssml.add("This is a test")

        try:
            # Synthesize SSML text
            audio_bytes = self.engine.synth_to_bytes(ssml_text)

            # Check that audio was generated
            assert audio_bytes is not None
            assert len(audio_bytes) > 0

        except (AttributeError, NotImplementedError) as e:
            # Skip test if engine doesn't support SSML
            self.skipTest(f"eSpeak doesn't support SSML: {e}")
        except Exception as e:
            self.fail(f"SSML synthesis failed with error: {e}")

    def test_ssml_break_tag(self):
        """Test SSML break tag."""
        # Skip if SKIP_ESPEAK_SYNTH_TEST is set
        if os.environ.get("SKIP_ESPEAK_SYNTH_TEST"):
            self.skipTest("SKIP_ESPEAK_SYNTH_TEST is set")

        try:
            # Create SSML with break tag
            ssml = self.engine.ssml.create()
            ssml.add("This is a test")
            ssml.add_break(time="500ms")
            ssml.add("with a pause")
            ssml_text = str(ssml)

            # Synthesize SSML text
            audio_bytes = self.engine.synth_to_bytes(ssml_text)

            # Check that audio was generated
            assert audio_bytes is not None
            assert len(audio_bytes) > 0

        except (AttributeError, NotImplementedError) as e:
            # Skip test if engine doesn't support SSML
            self.skipTest(f"eSpeak doesn't support SSML: {e}")
        except Exception as e:
            self.fail(f"SSML break tag test failed with error: {e}")

    def test_ssml_prosody_tag(self):
        """Test SSML prosody tag."""
        # Skip if SKIP_ESPEAK_SYNTH_TEST is set
        if os.environ.get("SKIP_ESPEAK_SYNTH_TEST"):
            self.skipTest("SKIP_ESPEAK_SYNTH_TEST is set")

        try:
            # Create SSML with prosody tag
            ssml = self.engine.ssml.create()
            ssml.add("This is a test")
            ssml.add_prosody("with different rate", rate="slow")
            ssml_text = str(ssml)

            # Synthesize SSML text
            audio_bytes = self.engine.synth_to_bytes(ssml_text)

            # Check that audio was generated
            assert audio_bytes is not None
            assert len(audio_bytes) > 0

        except (AttributeError, NotImplementedError) as e:
            # Skip test if engine doesn't support SSML
            self.skipTest(f"eSpeak doesn't support SSML: {e}")
        except Exception as e:
            self.fail(f"SSML prosody tag test failed with error: {e}")


# Only run AVSynth tests on macOS
if sys.platform == "darwin":
    class TestAVSynthSSML(unittest.TestCase):
        """Test SSML support in AVSynth engine."""

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

        def test_ssml_detection(self):
            """Test SSML detection."""
            # Test with SSML text
            ssml_text = "<speak>This is SSML</speak>"
            assert self.engine._is_ssml(ssml_text)

            # Test with plain text
            plain_text = "This is plain text"
            assert not self.engine._is_ssml(plain_text)

        def test_ssml_synthesis(self):
            """Test SSML synthesis."""
            # Create SSML text with various tags
            ssml_text = self.engine.ssml.add("This is a test")

            try:
                # Synthesize SSML text
                audio_bytes = self.engine.synth_to_bytes(ssml_text)

                # Check that audio was generated
                assert audio_bytes is not None
                assert len(audio_bytes) > 0

            except (AttributeError, NotImplementedError) as e:
                # Skip test if engine doesn't support SSML
                self.skipTest(f"AVSynth doesn't support SSML: {e}")
            except Exception as e:
                self.fail(f"SSML synthesis failed with error: {e}")


if __name__ == "__main__":
    unittest.main()
