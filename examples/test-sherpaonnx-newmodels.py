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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Initialize the SherpaOnnxClient
        # If model_path or tokens_path are None, the client will use default paths
        client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id="melo-zh_en-zh_en")

        # Initialize the SherpaOnnxTTS engine with the client
        tts = SherpaOnnxTTS(client=client)

        # Retrieve and display available voices
        voices = tts.get_voices()
        #logging.info(f"Available voices: {voices}")
        print ("voice list loaded")
        # Set the desired voice using its ISO code
        iso_code = "eng"  # Replace with a valid ISO code from the voices list
        tts.set_voice(voice_id=iso_code)
        logging.info(f"Voice set to ISO code: {iso_code}")

        # Define the text to be synthesized
        text = (
            "I want to test the streaming function and this is a much longer sentence "
            "than the previous one. This is a test of the streaming function."
        )
        logging.info(f"Text to synthesize: {text}")
        tts.speak_streamed(text)
    except Exception as e:
        logging.error(f"An error occurred during synthesis: {e}")

if __name__ == "__main__":
    main()