# test-googletts.py

import logging
from tts_wrapper import GoogleClient, GoogleTTS
import time
from io import BytesIO
import os
from pathlib import Path
from load_credentials import load_credentials
# Load credentials
load_credentials('credentials.json')
import wave


def main():
    # Configure logging to display informational messages
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Path to your Google Cloud service account JSON credentials

        client = GoogleClient(credentials=os.getenv('GOOGLE_CREDS_PATH'))        

        # Initialize the GoogleTTS engine with the client
        tts = GoogleTTS(client=client)

        # Retrieve and display available voices
        voices = tts.get_voices()
        logging.info(f"Available voices: {voices}")

        # Set the desired voice using its ISO code (e.g., "en-US-Wavenet-C")
        iso_code = "en-US-Wavenet-C"  # Replace with a valid voice from the voices list
        tts.set_voice(voice_id=iso_code)
        logging.info(f"Voice set to ISO code: {iso_code}")

        # Define the text to be synthesized
        text = (
            "I want to test the streaming function and this is a much longer sentence "
            "than the previous one. This is a test of the streaming function."
        )
        logging.info(f"Text to synthesize: {text}")

        # Test synth_to_bytestream method
        output_file_bytestream = "output_streamed_google.wav"  # Change to 'mp3' or 'flac' as needed
        audio_format = "wav"  # Supported formats: 'wav', 'mp3', 'flac'

        if audio_format.lower() == 'wav':
            # Initialize WAV file
            with wave.open(output_file_bytestream, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(tts.audio_rate)
                logging.info(f"Starting synthesis and streaming to {output_file_bytestream} in {audio_format} format.")

                for chunk_idx, audio_chunk in enumerate(tts.synth_to_bytestream(text, format=audio_format)):
                    logging.info(f"Received audio chunk {chunk_idx} with size {len(audio_chunk)} bytes")
                    wf.writeframes(audio_chunk)  # Write PCM frames to WAV file

            logging.info(f"Audio successfully saved to {output_file_bytestream} in {audio_format} format via synth_to_bytestream.")

        else:
            # Handle non-WAV formats if implemented
            pass

        # Test speak_streamed method
        output_file_speak_streamed = "output_speak_streamed_google.wav"
        tts.speak_streamed(text)
        logging.info(f"Audio successfully saved to {output_file_speak_streamed} in wav format via speak_streamed.")

    except Exception as e:
        logging.error(f"An error occurred during synthesis: {e}")

if __name__ == "__main__":
    main()