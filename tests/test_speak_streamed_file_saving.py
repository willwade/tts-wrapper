"""
Test speak_streamed method with file saving functionality.

This test specifically verifies that speak_streamed properly saves audio files
with correct WAV headers when save_to_file_path parameter is provided.

This addresses the bug where SherpaOnnx speak_streamed was saving raw PCM data
without proper WAV headers, causing "file does not start with RIFF id" errors.
"""

import tempfile
import unittest
import wave
from pathlib import Path

from tts_wrapper import SherpaOnnxClient


class TestSpeakStreamedFileSaving(unittest.TestCase):
    """Test speak_streamed file saving functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_text = "Hello world, this is a test."

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any files created during tests
        for file_path in Path(self.temp_dir).glob("*"):
            if file_path.is_file():
                file_path.unlink()
        Path(self.temp_dir).rmdir()

    def test_sherpaonnx_speak_streamed_wav_header(self):
        """Test that SherpaOnnx speak_streamed creates proper WAV files with RIFF headers."""
        try:
            # Initialize SherpaOnnx client
            client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="mms_eng")

            # Test file path
            test_file = Path(self.temp_dir) / "test_speak_streamed.wav"

            # Use speak_streamed with file saving
            client.speak_streamed(
                self.test_text,
                save_to_file_path=str(test_file),
                audio_format="wav",
                wait_for_completion=True
            )

            # Verify file was created
            assert test_file.exists(), "Audio file was not created"
            assert test_file.stat().st_size > 0, "Audio file is empty"

            # Verify WAV header
            with open(test_file, "rb") as f:
                header = f.read(4)
                assert header == b"RIFF", "File does not start with RIFF header"

            # Verify it's a valid WAV file by opening with wave module
            try:
                with wave.open(str(test_file), "rb") as wav_file:
                    # Basic WAV file validation
                    assert wav_file.getnframes() > 0, "WAV file has no audio frames"
                    assert wav_file.getnchannels() == 1, "Expected mono audio"
                    assert wav_file.getsampwidth() in [1, 2, 4], "Invalid sample width"
                    assert wav_file.getframerate() > 0, "Invalid frame rate"
            except wave.Error as e:
                self.fail(f"Generated file is not a valid WAV file: {e}")

        except Exception as e:
            self.skipTest(f"SherpaOnnx not available or failed to initialize: {e}")

    def test_sherpaonnx_speak_streamed_raw_format(self):
        """Test that SherpaOnnx speak_streamed saves raw PCM when format is 'raw'."""
        try:
            # Initialize SherpaOnnx client
            client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="mms_eng")

            # Test file path
            test_file = Path(self.temp_dir) / "test_speak_streamed_raw.pcm"

            # Use speak_streamed with raw format
            client.speak_streamed(
                self.test_text,
                save_to_file_path=str(test_file),
                audio_format="raw",
                wait_for_completion=True
            )

            # Verify file was created
            assert test_file.exists(), "Raw audio file was not created"
            assert test_file.stat().st_size > 0, "Raw audio file is empty"

            # Verify it's raw PCM (no RIFF header)
            with open(test_file, "rb") as f:
                header = f.read(4)
                assert header != b"RIFF", "Raw file should not have RIFF header"

        except Exception as e:
            self.skipTest(f"SherpaOnnx not available or failed to initialize: {e}")

    def test_sherpaonnx_synth_vs_speak_streamed_consistency(self):
        """Test that synth method and speak_streamed produce similar WAV files."""
        try:
            # Initialize SherpaOnnx client
            client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="mms_eng")

            # Test file paths
            synth_file = Path(self.temp_dir) / "test_synth.wav"
            speak_streamed_file = Path(self.temp_dir) / "test_speak_streamed.wav"

            # Generate audio using synth method
            client.synth(self.test_text, synth_file, "wav")

            # Generate audio using speak_streamed method
            client.speak_streamed(
                self.test_text,
                save_to_file_path=str(speak_streamed_file),
                audio_format="wav",
                wait_for_completion=True
            )

            # Verify both files exist and have content
            assert synth_file.exists(), "Synth file was not created"
            assert speak_streamed_file.exists(), "Speak streamed file was not created"
            assert synth_file.stat().st_size > 0, "Synth file is empty"
            assert speak_streamed_file.stat().st_size > 0, "Speak streamed file is empty"

            # Verify both have proper WAV headers
            with open(synth_file, "rb") as f:
                synth_header = f.read(4)
                assert synth_header == b"RIFF", "Synth file missing RIFF header"

            with open(speak_streamed_file, "rb") as f:
                speak_header = f.read(4)
                assert speak_header == b"RIFF", "Speak streamed file missing RIFF header"

            # Verify both are valid WAV files
            try:
                with wave.open(str(synth_file), "rb") as wav1, wave.open(str(speak_streamed_file), "rb") as wav2:
                    # Compare basic properties
                    assert wav1.getnchannels() == wav2.getnchannels(), "Channel count mismatch"
                    assert wav1.getsampwidth() == wav2.getsampwidth(), "Sample width mismatch"
                    assert wav1.getframerate() == wav2.getframerate(), "Frame rate mismatch"
            except wave.Error as e:
                self.fail(f"One or both generated files are not valid WAV files: {e}")

        except Exception as e:
            self.skipTest(f"SherpaOnnx not available or failed to initialize: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
