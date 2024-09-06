from tts_wrapper import GoogleTransClient, GoogleTransTTS
import time
try:
    voice_id = "en-co.uk"  # Example voice ID for UK English
    client = GoogleTransClient(voice_id)
    # Initialize the TTS engine
    tts = GoogleTransTTS(client)

    # Get available voices
#     voices = tts.get_voices()
#     print("Available voices:", voices)

    # Set the voice using ISO code
    iso_code = "en-co.uk"  # Example ISO code for the voice
    tts.set_voice(iso_code)

    # Define the text to be synthesized
    text = "Hello, This is a word timing test"
    start_time = time.time()
    tts.speak(text)
    synthesis_time = time.time()
    print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")
    text = "Hello, This is a word timing test"
    start_time = time.time()
    tts.synth_to_file(text,"test.mp3", "mp3")
    synthesis_time = time.time()
    print(f"Synthesis time: {synthesis_time - start_time:.3f} seconds")

except Exception as e:
    print(f"Error: {e}")
