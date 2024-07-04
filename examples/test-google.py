from tts_wrapper import GoogleTTS, GoogleClient
import json
import time
from pathlib import Path
import os
from load_credentials import load_credentials
# Load credentials
load_credentials('credentials.json')

client = GoogleClient(credentials=os.getenv('GOOGLE_CREDS_PATH'))

tts = GoogleTTS(client)

# # # pausng
# try:
#     ssml_text = tts.ssml.add(f"This is me speaking with Speak function and google")
#     tts.speak_streamed(ssml_text)
#     # Pause after 5 seconds
#     time.sleep(0.3)
#     tts.pause_audio()
#     print("Pausing..")
#     # Resume after 3 seconds
#     time.sleep(0.5)
#     tts.resume_audio()
#     print("Resuming")
#     # Stop after 2 seconds
#     time.sleep(1)
#     tts.stop_audio()
#     print("Stopping.")
# except Exception as e:
#     print(f"Error at pausing: {e}")
#   
# time.sleep(3)        
# # Demonstrate saving audio to a file
# try:
#     output_file = Path(f"output_google.mp3")
#     tts.synth(ssml_text, str(output_file), format='mp3')
#     # or you could do
#     #tts.speak(ssml_text)
#     print(f"Audio content saved to {output_file}")
# except Exception as e:
#     print(f"Error at saving: {e}")
#   
#       
# # Change voice and test again if possible
# try:
#     voices = tts.get_voices()
# except Exception as e:
#     print(f"Error at getting voices: {e}")
# 
# print('Getting voices')
# for voice in voices[:4]:  # Show details for first four voices
#     language_codes = voice.get('language_codes', [])
#     display_name = voice.get('name', 'Unknown voice')
#     # Safely get the first language code, default to 'Unknown' if not available
#     first_language_code = language_codes[0] if language_codes else 'Unknown'
#     print(f"{display_name} ({first_language_code}): {voice['id']}")
# # Change voice if more than one is available
# if len(voices) > 1:
#     new_voice_id = voices[1].get('id')
#     # Attempt to get the first language from the second voice's language codes
#     new_lang_codes = voices[1].get('language_codes', [])
#     new_lang_id = new_lang_codes[0] if new_lang_codes else 'Unknown'
#     print(f"Running with {new_voice_id} and {new_lang_id}")
#     try:
#         tts.set_voice(new_voice_id, new_lang_id)
#     except Exception as e:
#         print(f"Error at setting voice: {e}")
#     ssml_text_part2 = tts.ssml.add('Continuing with a new voice!')
#     tts.speak_streamed(ssml_text_part2)

# ## calbacks
# 
def my_callback(word: str, start_time: float, end_time: float):
    duration = end_time - start_time
    print(f"Word: '{word}' Started at {start_time:.3f}ms Duration: {duration:.3f}s")

def on_start():
    print('Speech started')

def on_end():
    print('Speech ended')


try:
    text = "Hello, This is a word timing test"
    tts.connect('onStart', on_start)
    tts.connect('onEnd', on_end)
    tts.start_playback_with_callbacks(text, callback=my_callback)
except Exception as e:
    print(f"Error at callbacks: {e}")


# # volume control test
# print("Volume setting is from 0-100")
# text_read = ""
# try:
#     tts.set_property("volume", "20")
#     print("Setting volume at 20")
#     text_read = f"The current volume is at 20"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(3)
#     
#     #clear ssml so the previous text is not repeated
#     tts.ssml.clear_ssml()
#     tts.set_property("volume", "100")
#     print("Setting volume at 100")
#     text_read = f"The current volume is at 100"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(3)
# 
#     tts.ssml.clear_ssml()
#     tts.set_property("volume", "10")
#     print("Setting volume at 10")
#     text_read = f"The current volume is at 10"
#     text_with_prosody = tts.construct_prosody_tag(text_read)        
#     ssml_text = tts.ssml.add(text_with_prosody)
#     tts.speak_streamed(ssml_text)
#     time.sleep(3)
# 
# except Exception as e:
#     print(f"Error at setting volume: {e}")
# 
# # pitch control test
# print("Pitch control is from x-low, low, medium, high, x-high")
# text_read = ""
# tts.set_property("volume", "70")
# try:
#     tts.ssml.clear_ssml()
#     tts.set_property("pitch", "low")
#     print("Setting pitch at low")
#     text_read = f"The current pitch is LOW"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
#     
#     #clear ssml so the previous text is not repeated
#     tts.ssml.clear_ssml()
#     tts.set_property("pitch", "x-high")
#     print("Setting pitch at EXTRA HIGH")
#     text_read = f"The current pitch is at EXTRA HIGH"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
# 
#     tts.ssml.clear_ssml()
#     tts.set_property("pitch", "x-low")
#     print("Setting pitch at EXTRA LOW")
#     text_read = f"The current pitch at EXTRA LOW"
#     text_with_prosody = tts.construct_prosody_tag(text_read)        
#     ssml_text = tts.ssml.add(text_with_prosody)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
# except Exception as e:
#     print(f"Error at setting pitch: {e}")   
# 
# # rate control test
# print("Rate setting is from x-slow, slow, medium, fast, x-fast")
# text_read = ""
# tts.set_property("volume", "70")
# try:
#     tts.ssml.clear_ssml()
#     tts.set_property("rate", "slow")
#     print("Setting rate at SLOW")
#     text_read = f"The current rate is SLOW"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
#     
#     #clear ssml so the previous text is not repeated
#     tts.ssml.clear_ssml()
#     tts.set_property("rate", "x-fast")
#     print("Setting rate at EXTRA FAST")
#     text_read = f"The current rate is at EXTRA FAST"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
# 
#     tts.ssml.clear_ssml()
#     tts.set_property("rate", "x-slow")
#     print("Setting rate at EXTRA SLOW")
#     text_read = f"The current rate at EXTRA SLOW"
#     text_with_prosody = tts.construct_prosody_tag(text_read)        
#     ssml_text = tts.ssml.add(text_with_prosody)
#     tts.speak_streamed(ssml_text)
#     time.sleep(5)
# except Exception as e:
#     print(f"Error at setting pitch: {e}")  