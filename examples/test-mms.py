import time

from tts_wrapper import MMSTTS, MMSClient

# Initialize the client with only the lang parameter
client = MMSClient("spa")
tts = MMSTTS(client)
text = "hello world i like monkeys"
tts.speak(text)


# volume control test
text_read = ""
try:
    tts.set_output_device(2)
    tts.set_property("volume", "50")
    text_read = "The current volume is at fifty"
    text_with_prosody = tts.construct_prosody_tag(text_read)
    ssml_text = tts.ssml.add(text_with_prosody)
    tts.speak(ssml_text)
    time.sleep(0.5)

    #clear ssml so the previous text is not repeated

    tts.set_property("volume", "100")
    text_read = "The current volume is at a hundred"
    text_with_prosody = tts.construct_prosody_tag(text_read)
    ssml_text = tts.ssml.add(text_with_prosody)

    tts.speak(ssml_text)
    time.sleep(0.5)

    tts.set_property("volume", "10")
    text_read = "The current volume is at ten"
    text_with_prosody = tts.construct_prosody_tag(text_read)
    ssml_text = tts.ssml.add(text_with_prosody)

    tts.speak(ssml_text)
    time.sleep(0.5)

    tts.synth_to_file(ssml_text, "mms_output.wav", "wav")
except Exception:
    pass
