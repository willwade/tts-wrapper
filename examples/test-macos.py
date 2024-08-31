from tts_wrapper import MacOSClient, MacOSTTS

client = MacOSClient.new()
# Initialize the TTS engine
tts = MacOSTTS(client)
# Get available voices
# voices = tts.get_voices()
# print("Available voices:", voices)

# tts.set_voice('com.apple.voice.compact.en-GB.Daniel')

# Define the text to be synthesized
text = "Hello, This is a word timing test"
tts.speak(text)

# tts.set_property("rate", "high")
# print("Setting rate at 20")
# text_read = f"The current volume is at 20"
# text_with_prosody = tts.construct_prosody_tag(text_read)
# ssml_text = tts.ssml.add(text_with_prosody)
# print("ssml_test: ", ssml_text)
# tts.speak_streamed(ssml_text)


def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: '{word}' Started at {start_time:.3f}ms Duration: {duration:.3f}s")

def on_start():
    print('Speech started')

def on_end():
    print('Speech ended')

text = "Hello This is a word timing test"
tts.connect('onStart', on_start)
tts.connect('onEnd', on_end)
tts.start_playback_with_callbacks(text, callback=my_callback)


