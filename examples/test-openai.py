#!/usr/bin/env python3
"""
Example script for using the OpenAI TTS engine.
"""

import logging
import os
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts_wrapper.engines.openai import OpenAIClient


def test_basic_synthesis():
    """Test basic text-to-speech synthesis."""
    try:
        # Create the OpenAI TTS client
        # You need to set the OPENAI_API_KEY environment variable or pass it as an argument
        tts = OpenAIClient(
            voice="alloy",
            model="gpt-4o-mini-tts",
            instructions="Speak in a cheerful and positive tone.",
        )

        # Set output device (optional)
        tts.set_output_device(0)

        # Simple text synthesis
        text = "Hello! This is a test of the OpenAI text-to-speech engine."
        print(f"Speaking: {text}")

        # Speak the text
        tts.speak(text)

        # Wait for playback to complete
        time.sleep(1)

        # Save to file
        output_file = Path(__file__).parent / "openai_output.mp3"
        tts.synth(text, output_file, output_format="mp3")
        print(f"Saved audio to {output_file}")

        # Test with different voice
        tts.set_voice("nova")
        text = "Now I'm speaking with a different voice."
        print(f"Speaking with nova voice: {text}")
        tts.speak(text)

        # Create a new client with different settings
        tts2 = OpenAIClient(
            voice="echo",
            model="tts-1-hd",  # Higher quality model
            instructions="Speak in a slow, deep voice.",
        )

        # Test with the new client
        text = "This is a test with a different model and voice."
        print(f"Speaking with echo voice and tts-1-hd model: {text}")
        tts2.speak(text)

        # Test with SSML (will be stripped as OpenAI doesn't support SSML)
        ssml_text = tts.ssml.construct_prosody(
            "This is me speaking with OpenAI's text-to-speech.",
            rate="fast",
            volume="medium",
            pitch="high",
        )
        print(f"Speaking with SSML (will be stripped): {ssml_text}")
        tts.speak(ssml_text)

        # Test with streaming
        text = "This is a streaming test. The audio should play while it's being generated."
        print(f"Streaming: {text}")
        tts.speak_streamed(text)

    except Exception as e:
        print(f"Error in basic synthesis test: {e}")


def test_word_callbacks():
    """Test word timing callbacks."""
    try:
        # Create the OpenAI TTS client
        tts = OpenAIClient(voice="alloy")

        # Define a callback function for word events
        def word_callback(word_obj):
            start_time, end_time, word = word_obj
            print(f"Word: {word}, Time: {start_time:.2f}s - {end_time:.2f}s")

        # Connect the callback
        tts.connect("onWord", word_callback)

        # Speak with word timing
        text = "This is a test of word timing callbacks with OpenAI."
        print(f"Speaking with word callbacks: {text}")

        # Note: OpenAI doesn't provide word timing information, so this will use
        # the estimated word timings from AbstractTTS
        tts.speak(text)

    except Exception as e:
        print(f"Error in word callbacks test: {e}")


if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("You can set it with: export OPENAI_API_KEY='your-api-key'")
        print("Continuing anyway in case you're providing the API key in the code...")

    # Run the tests
    test_basic_synthesis()
    test_word_callbacks()
