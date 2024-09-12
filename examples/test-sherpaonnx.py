import logging
logging.basicConfig(level=logging.INFO)

from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
try:
    client = SherpaOnnxClient(model_path=None, tokens_path=None)
    # Initialize the TTS engine
    tts = SherpaOnnxTTS(client)

    # # Get available voices
    # voices = tts.get_voices()
    # print("Available voices:", voices)

    # Set the voice using ISO code
    iso_code = "eng"  # Example ISO code for the voice
    tts.set_voice(iso_code)

    # # Define the text to be synthesized
    # text = "Hello, This is a word timing test"
    # start_time = time.time()
    # tts.speak(text)
    # synthesis_time = time.time()
    # print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")

    text = "I want to test the streaming function and this a much longer sentence than the previous one. This is a test of the streaming function."
    start_time = time.time()
    tts.speak(text)
    #tts.synth_to_file("i like cheese", "test.wav")
    tts.synth_to_file(text, "test-sherpa.wav")
    synthesis_time = time.time()
    print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")
    # text = "I want to test the streaming function and this a much longer sentence than the previous one. This is a test of the streaming function."
    # start_time = time.time()
    # tts.speak_streamed(text)
    # synthesis_time = time.time()
    # print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")

    # tts.set_property("volume", "50")
    # print("Setting volume at 50")
    # text_read = f"The current volume is at fifty"
    # text_with_prosody = tts.construct_prosody_tag(text_read)
    # print("text_with_prosody", text_with_prosody)
    # ssml_text = tts.ssml.add(text_with_prosody)
    # print("ssml_text", ssml_text)
    # tts.speak(ssml_text)
 

except Exception as e:
    print(f"Error: {e}")
