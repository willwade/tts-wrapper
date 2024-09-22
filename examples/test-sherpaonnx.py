# test_synth_to_bytestream.py

import logging
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
from io import BytesIO

def main():
    # Configure logging to display informational messages
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Initialize the SherpaOnnxClient
        # If model_path or tokens_path are None, the client will use default paths
        client = SherpaOnnxClient(model_path=None, tokens_path=None)

        # Initialize the SherpaOnnxTTS engine with the client
        tts = SherpaOnnxTTS(client=client)

        # Retrieve and display available voices
        voices = tts.get_voices()
        logging.info(f"Available voices: {voices}")

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

        # Specify the output file and format
        output_file = "output_streamed.wav"  # Change to 'output_streamed.mp3' or other formats as needed
        audio_format = "wav"  # Supported formats: 'wav', 'mp3', 'flac'

        # Open the output file in binary write mode
        with open(output_file, "wb") as f:
            logging.info(f"Starting synthesis and streaming to {output_file} in {audio_format} format.")

            # Iterate over the generator returned by synth_to_bytestream
            for chunk_idx, audio_chunk in enumerate(tts.synth_to_bytestream(text, format=audio_format)):
                logging.info(f"Received audio chunk {chunk_idx} with size {len(audio_chunk)} bytes")
                f.write(audio_chunk)  # Write the chunk to the file

        logging.info(f"Audio successfully saved to {output_file} in {audio_format} format.")
        tts.speak_streamed(text)
    except Exception as e:
        logging.error(f"An error occurred during synthesis: {e}")

if __name__ == "__main__":
    main()