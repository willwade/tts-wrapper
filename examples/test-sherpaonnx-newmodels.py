# test_synth_to_bytestream.py

import logging
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
from io import BytesIO
import os
import tarfile
import bz2


def main():
    # Configure logging to display informational messages
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        # Initialize the SherpaOnnxClient
        # If model_path or tokens_path are None, the client will use default paths
        # if model are defined, it will use the defined model for TTS
        # client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="melo-zh_en-zh_en")

        # if none are defined it will either use the default language (english)
        # or it will take the language from the given iso_code in set_voices
        client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="mms_fra")

        # Initialize the SherpaOnnxTTS engine with the client
        tts = SherpaOnnxTTS(client=client)

        # Retrieve and display available voices
        voices = tts.get_voices()
        # logging.info(f"Available voices: {voices}")
        print("voice list loaded")

        # Set the desired voice using its ISO code
        # iso_code = "mms_zpg"  # Replace with a valid ISO code from the voices list. If empty default is mms_eng
        tts.set_voice()
        # logging.info(f"Voice set to ISO code: {iso_code}")

        # Define the text to be synthesized
        text = (
            "I want to test the streaming function and this is a much longer sentence "
            "than the previous one. This is a test of the streaming function."
        )
        # text = "Hola, como estas?"
        logging.info(f"Text to synthesize: {text}")
        tts.speak_streamed(text)
    except Exception as e:
        logging.error(f"An error occurred during synthesis: {e}")


if __name__ == "__main__":
    main()
