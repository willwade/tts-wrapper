# if running within the project dir
# export PYTHONPATH="/Users/willwade/GitHub/tts-wrapper:$PYTHONPATH"
# python examples/all_engines_example.py

# examples/all_engines_example.py
import sys
import json
import logging
from pathlib import Path
from tts_wrapper import PollyTTS, PollyClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, GoogleTTS, GoogleClient, ElevenLabsTTS, ElevenLabsClient
import signal
import sys
import time

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        logging.debug("Settings loaded from file.")
        return settings
    except FileNotFoundError:
        logging.error("Settings file not found. Ensure 'settings.json' is in the correct location.")
        return {}

def create_tts_client(service, settings):
    if service == "polly":
        creds = settings.get('Polly', {})
        client = PollyClient(credentials=(creds.get('region'), creds.get('aws_key_id'), creds.get('aws_access_key')))
        tts = PollyTTS(client=client, voice='Joanna')
    elif service == "microsoft":
        creds = settings.get('Microsoft', {})
        client = MicrosoftClient(credentials=creds.get('TOKEN'), region=creds.get('region'))
        tts = MicrosoftTTS(client=client)
    elif service == "watson":
        creds = settings.get('Watson', {})
        client = WatsonClient(credentials=(creds.get('api_key'), creds.get('region'), creds.get('instance_id')))
        tts = WatsonTTS(client=client)
    elif service == "google":
        creds = settings.get('Google', {})
        client = GoogleClient(credentials=creds.get('creds_path'))
        tts = GoogleTTS(client=client)
    elif service == "elevenlabs":
        creds = settings.get('ElevenLabs', {})
        client = ElevenLabsClient(credentials=creds.get('API_KEY'))
        tts = ElevenLabsTTS(client=client)
    else:
        raise ValueError("Unsupported TTS service")
    return tts

def test_tts_engine(tts, service_name):
    try:
        text_read = 'Hello, world!'
        ssml_text = tts.ssml.add(text_read)  # Assuming there's a method to add SSML correctly
        try:
            print(f"Testing {service_name} TTS engine...in a timed play/pause demo")
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
            print(f"Error testing {service_name} TTS engine: {e}")
        

    except Exception as e:
        print(f"Error testing {service_name} TTS engine: {e}")
        
    # Demonstrate saving audio to a file
    output_file = Path(f"output_{service_name}.mp3")
    tts.synth(ssml_text, str(output_file), format='mp3')
    # or you could do
    #tts.speak(ssml_text)
    print(f"Audio content saved to {output_file}")

    # Change voice and test again if possible
    voices = tts.get_voices()
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
        tts.set_voice(new_voice_id, new_lang_id)
        ssml_text_part2 = tts.ssml.add('Continuing with a new voice!')
        tts.speak_streamed(ssml_text_part2)

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    settings = load_settings()

    services = ["watson", "google", "elevenlabs", "microsoft","polly", ] if service == "all" else [service]
    for svc in services:
        print(f"Testing {svc.upper()} TTS engine.")
        tts = create_tts_client(svc, settings)
        test_tts_engine(tts, svc)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
