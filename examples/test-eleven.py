from tts_wrapper import ElevenLabsTTS, ElevenLabsClient
import json
import time
from pathlib import Path
import os

client = ElevenLabsClient(credentials=(os.getenv('ELEVENLABS_API_KEY')))
tts = ElevenLabsTTS(client)

# # pausng
try:
    ssml_text = tts.ssml.add(f"This is me speaking with Speak function and ElevenLabs")
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
  
        
# Demonstrate saving audio to a file
try:
    output_file = Path(f"output_elevenlabs.mp3")
    tts.synth(ssml_text, str(output_file), format='mp3')
    # or you could do
    #tts.speak(ssml_text)
    print(f"Audio content saved to {output_file}")
except Exception as e:
    print(f"Error at saving: {e}")
  
      
# Change voice and test again if possible
try:
    voices = tts.get_voices()
except Exception as e:
    print(f"Error at getting voices: {e}")

print('Getting voices')
for voice in voices[:4]:  # Show details for first four voices
    language_codes = voice.get('language_codes', [])
    display_name = voice.get('name', 'Unknown voice')
    # Safely get the first language code, default to 'Unknown' if not available
    first_language_code = language_codes[0] if language_codes else 'Unknown'
    print(f"{display_name} ({first_language_code}): {voice['id']}")
# Change voice if more than one is available
if len(voices) > 1:
    new_voice_id = voices[1].get('id')
    # Attempt to get the first language from the second voice's language codes
    new_lang_codes = voices[1].get('language_codes', [])
    new_lang_id = new_lang_codes[0] if new_lang_codes else 'Unknown'
    print(f"Running with {new_voice_id} and {new_lang_id}")
    try:
        tts.set_voice(new_voice_id, new_lang_id)
    except Exception as e:
        print(f"Error at setting voice: {e}")
    ssml_text_part2 = tts.ssml.add('Continuing with a new voice!')
    tts.speak_streamed(ssml_text_part2)

# ## calbacks

def my_callback(word: str, start_time: float):
    print(f'Word "{word}" spoken at {start_time} ms')

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