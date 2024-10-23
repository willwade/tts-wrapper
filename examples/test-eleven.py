from tts_wrapper import ElevenLabsTTS, ElevenLabsClient
import time
from pathlib import Path
import os
from load_credentials import load_credentials

# Load credentials
load_credentials("credentials-private.json")

client = ElevenLabsClient(credentials=(os.getenv("ELEVENLABS_API_KEY")))
tts = ElevenLabsTTS(client)
tts.speak_streamed(
    "The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace."
)
tts.pause_audio()
input("Press enter to resume")
tts.resume_audio()
exit()
print(client.get_voices())

long_text = '''"Title: "The Silent Truth"
The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace.
Chapter 1: A Quiet Morning
Detective Emma Hayes had just finished her morning coffee when the phone rang. It was a local officer from the Brookhollow precinct. Something felt wrong from the tone of his voice.
"Detective Hayes, there's been an incident," Officer Morgan said, his voice tight. "You need to come to the Harrison estate right away."
The Harrison estate was the largest property in Brookhollow, home to George Harrison, a well-known philanthropist and businessman. Emma grabbed her coat, knowing instinctively that this wasn’t a routine call.
When she arrived, the estate was cordoned off. Police officers and forensic teams were scattered around the front lawn. Emma approached Officer Morgan, who was standing by the front entrance.
"What's the situation?" she asked.
Morgan gestured towards the house. "George Harrison. He’s dead. The maid found him this morning, lying in his study. Looks like a murder."
Emma followed him inside, her mind racing. The air was thick with tension as they entered the study. The room was tastefully decorated, books lined the walls, and a grand mahogany desk stood in the center. But the most striking thing was the body slumped over the desk, a pool of blood soaking the papers beneath George Harrison's hand. A single gunshot to the back of the head.
Emma examined the scene carefully. There were no signs of a struggle, and nothing seemed out of place. It was clean. Too clean."'''
# # # pausing
try:
    ssml_text = tts.ssml.add(long_text)
    tts.speak_streamed(ssml_text)
    # Pause after 5 seconds
    time.sleep(0.3)
    tts.pause_audio()
    print("Pausing..")
    # Resume after 3 seconds
    time.sleep(0.5)
    tts.resume_audio()
    print("Resuming")
    # Stop after 2 seconds
    time.sleep(1)
    tts.stop_audio()
    print("Stopping.")
except Exception as e:
    print(f"Error at pausing: {e}")

time.sleep(3)
#
# # Demonstrate saving audio to a file
try:
    ssml_text = tts.ssml.add(f"This is me speaking with Speak function and ElevenLabs")

    #   ssml_text = tts.ssml.add(long_text)
    output_file = Path(f"output_elevenlabs.wav")
    # tts.synth(ssml_text, str(output_file), format='wav')
    tts.speak_streamed(ssml_text, output_file, audio_format="wav")
    # or you could do
    # tts.speak(ssml_text)
    print(f"Audio content saved to {output_file}")
except Exception as e:
    print(f"Error at saving: {e}")

time.sleep(3)

# Change voice and test again if possible
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
#
# time.sleep(3)

# ## calbacks

# def my_callback(word: str, start_time: float, end_time: float):
#     duration = end_time - start_time
#     print(f"Word: {word}, Duration: {duration:.3f}s")
#
# def on_start():
#     print('Speech started')
#
# def on_end():
#     print('Speech ended')
#
# try:
#     text = "Hello, This is a word timing test"
#     tts.connect('onStart', on_start)
#     tts.connect('onEnd', on_end)
#     tts.start_playback_with_callbacks(text, callback=my_callback)
# except Exception as e:
#     print(f"Error at callbacks: {e}")

time.sleep(3)

# # volume control test
# print("Volume setting is from 0-100")
# text_read = ""
# try:
#     tts.set_property("volume", "50")
#     print("Setting volume at 50")
#     text_read = f"The current volume is at 50"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     tts.speak_streamed(ssml_text)
#     time.sleep(0.5)
#
#     #clear ssml so the previous text is not repeated
#     tts.ssml.clear_ssml()
#     tts.set_property("volume", "100")
#     print("Setting volume at 100")
#     text_read = f"The current volume is at 100"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     tts.speak_streamed(ssml_text)
#     time.sleep(0.5)
#
#     tts.ssml.clear_ssml()
#     tts.set_property("volume", "10")
#     print("Setting volume at 10")
#     text_read = f"The current volume is at 10"
#     text_with_prosody = tts.construct_prosody_tag(text_read)
#     ssml_text = tts.ssml.add(text_with_prosody)
#     print("ssml_test: ", ssml_text)
#     tts.speak_streamed(ssml_text)
#     time.sleep(0.5)
#
# except Exception as e:
#     print(f"Error at setting volume: {e}")
