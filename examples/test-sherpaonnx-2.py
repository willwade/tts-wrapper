import logging
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
from io import BytesIO
from pathlib import Path


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

# # # pausng
try:
    ssml_text = tts.ssml.add(text)
    print("ssml text")
    print(ssml_text)
    tts.speak_streamed(ssml_text)
    # Pause after 5 seconds
except Exception as e:
    print(f"Error at speak_streamed: {e}")
#   
# time.sleep(3)        
# # Demonstrate saving audio to a file
try:
    ssml_text = tts.ssml.add(text)
    output_file = Path(f"output_sherpaonnx.wav")
    tts.speak_streamed(ssml_text, str(output_file), audio_format='wav')
#     # or you could do
     #tts.speak(ssml_text)
    print(f"Audio content saved to {output_file}")
except Exception as e:
    print(f"Error at saving: {e}")
#   
# 