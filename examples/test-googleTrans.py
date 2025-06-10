import time

from tts_wrapper import GoogleTransClient

try:
    # Initialize the TTS client with UK English voice
    tts = GoogleTransClient(voice_id="en-co.uk")

    # Get available voices
    # voices = tts.get_voices()
    # print("Available voices:", voices)

    # Set the voice using ISO code
    tts.set_voice("en-co.uk")

    # Define the text to be synthesized
    text = "Hello, This is a word timing test"

    # Test speech synthesis
    print("Testing speech synthesis...")
    start_time = time.time()
    tts.speak(text)
    synthesis_time = time.time()
    print(f"Speech synthesis took {synthesis_time - start_time:.2f} seconds")

    # Test file synthesis
    print("Testing file synthesis...")
    start_time = time.time()
    tts.synth_to_file(text, "test.mp3", "mp3")
    synthesis_time = time.time()
    print(f"File synthesis took {synthesis_time - start_time:.2f} seconds")

    # Test word timing callbacks
    print("Testing word timing callbacks...")
    def word_callback(word, start_time, end_time):
        print(f"Word: '{word}' at {start_time:.2f}s - {end_time:.2f}s")

    tts.start_playback_with_callbacks("This is a word timing test", callback=word_callback)
    time.sleep(3)  # Give it time to complete

    print("All tests completed successfully!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
