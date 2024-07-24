from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
try:
    client = SherpaOnnxClient(model_path=None, tokens_path=None)
    # Initialize the TTS engine
    tts = SherpaOnnxTTS(client)

#     # Get available voices
#     voices = tts.get_voices()
#     print("Available voices:", voices)

    # Set the voice using ISO code
    iso_code = "eng"  # Example ISO code for the voice
    tts.set_voice(iso_code)

    # Define the text to be synthesized
    text = "Hello, This is a word timing test"
    start_time = time.time()
    tts.speak(text)
    synthesis_time = time.time()
    print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")
    text = "Hello, This is a word timing test"
    start_time = time.time()
    tts.speak(text)
    synthesis_time = time.time()
    print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")

except Exception as e:
    print(f"Error: {e}")
