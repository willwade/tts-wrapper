"""Tests for the OpenAI TTS engine."""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

from tts_wrapper.engines.openai import OpenAIClient
from tts_wrapper.engines.openai.ssml import OpenAISSML


class TestOpenAISSML(unittest.TestCase):
    """Test the OpenAI SSML implementation."""

    def setUp(self):
        """Set up the test."""
        self.ssml = OpenAISSML()

    def test_to_string(self):
        """Test converting SSML to plain text."""
        # Add a text node
        self.ssml.add_text("Hello, world!")
        # The to_string method should return plain text
        assert self.ssml.to_string() == "Hello, world!"

    def test_construct_prosody(self):
        """Test constructing a prosody element."""
        # Construct a prosody element
        text = self.ssml.construct_prosody(
            "Hello, world!", rate="fast", volume="medium", pitch="high"
        )
        # The construct_prosody method should return plain text
        assert text == "Hello, world!"


@unittest.skipIf(
    not os.environ.get("OPENAI_API_KEY"),
    "OPENAI_API_KEY environment variable not set",
)
class TestOpenAIClient(unittest.TestCase):
    """Test the OpenAI TTS client."""

    def setUp(self):
        """Set up the test."""
        self.client = OpenAIClient()

    def test_get_voices(self):
        """Test getting available voices."""
        voices = self.client.get_voices()
        # Check that we have at least one voice
        assert len(voices) > 0
        # Check that each voice has the required fields
        for voice in voices:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice
            assert "language_codes" in voice

    def test_set_voice(self):
        """Test setting the voice."""
        # Set a valid voice
        self.client.set_voice("alloy")
        assert self.client.voice_id == "alloy"

        # Set an invalid voice
        with pytest.raises(ValueError):
            self.client.set_voice("invalid_voice")

    def test_model_setting(self):
        """Test that model is set correctly during initialization."""
        # Create a client with a specific model
        client = OpenAIClient(model="tts-1")
        assert client.model == "tts-1"

        # Create a client with a different model
        client = OpenAIClient(model="tts-1-hd")
        assert client.model == "tts-1-hd"

        # Create a client with the default model
        client = OpenAIClient()
        assert client.model == "gpt-4o-mini-tts"

    def test_internal_format(self):
        """Test that internal format is set correctly."""
        # Create a client
        client = OpenAIClient()
        # Check that the internal format is set to wav
        assert client._internal_format == "wav"

    def test_instructions_setting(self):
        """Test that instructions are set correctly during initialization."""
        # Create a client with specific instructions
        instructions = "Speak in a cheerful tone."
        client = OpenAIClient(instructions=instructions)
        assert client.instructions == instructions


@unittest.skipIf(
    not os.environ.get("OPENAI_API_KEY"),
    "OPENAI_API_KEY environment variable not set",
)
class TestOpenAIClientWithMocks(unittest.TestCase):
    """Test the OpenAI TTS client with mocks."""

    def setUp(self):
        """Set up the test."""
        # Create a mock OpenAI client
        self.mock_openai = MagicMock()

        # Create a patch for the OpenAI client
        self.openai_patch = patch(
            "tts_wrapper.engines.openai.client.OpenAI", return_value=self.mock_openai
        )

        # Start the patch
        self.openai_patch.start()

        # Create the OpenAI TTS client
        self.client = OpenAIClient(api_key="test_api_key")

        # Set up the mock response
        self.mock_response = MagicMock()
        self.mock_response.content = b"test_audio_content"

        # Set up the mock speech create method
        self.mock_openai.audio.speech.create.return_value = self.mock_response

    def tearDown(self):
        """Tear down the test."""
        # Stop the patch
        self.openai_patch.stop()

    def test_synth_to_bytes(self):
        """Test synthesizing text to bytes."""
        # Synthesize text to bytes
        audio_bytes = self.client.synth_to_bytes("Hello, world!")

        # Check that the OpenAI client was called with the correct arguments
        self.mock_openai.audio.speech.create.assert_called_once_with(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input="Hello, world!",
            response_format="mp3",
            instructions=None,
        )

        # Check that the audio bytes are correct
        assert audio_bytes == b"test_audio_content"

    def test_synth_to_bytes_with_ssml(self):
        """Test synthesizing SSML to bytes."""
        # Create SSML
        ssml = OpenAISSML()
        ssml.add_text("Hello, world!")

        # Synthesize SSML to bytes
        audio_bytes = self.client.synth_to_bytes(ssml)

        # Check that the OpenAI client was called with the correct arguments
        self.mock_openai.audio.speech.create.assert_called_once_with(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input="Hello, world!",
            response_format="mp3",
            instructions=None,
        )

        # Check that the audio bytes are correct
        assert audio_bytes == b"test_audio_content"


if __name__ == "__main__":
    unittest.main()
