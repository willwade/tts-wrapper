# if running within the project dir
# export PYTHONPATH="/Users/willwade/GitHub/tts-wrapper:$PYTHONPATH"
# python examples/all_engines_example.py

# examples/all_engines_example.py
import sys
import json
import logging
from pathlib import Path
from tts_wrapper import PollyTTS, PollyClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, GoogleTTS, GoogleClient, ElevenLabsTTS, ElevenLabsClient

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
        client = WatsonClient(credentials=(creds.get('API_KEY'), creds.get('API_URL')))
        tts = WatsonTTS(client=client)
    elif service == "google":
        creds = settings.get('Google', {})
        client = GoogleClient(credentials=creds.get('creds_path'))
        tts = GoogleTTS(client=client)
    else:
        raise ValueError("Unsupported TTS service")
    return tts

def test_tts_engine(tts, service_name):
    try:
        text_read = 'Hello, world!'
        ssml_text = tts.ssml.add(text_read)  # Assuming there's a method to add SSML correctly
        print(ssml_text)
        try:
            audio_content = tts.synth_to_bytes(ssml_text)  # Default format assumed internally
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
        # Play audio content directly
        tts.play_audio(audio_content)
        input("Press enter to pause...")
        tts.pause_audio()
        input("Press enter to resume...")
        tts.resume_audio()
        input("Press enter to stop...")
        tts.stop_audio()

    except Exception as e:
        print(f"Error testing {service_name} TTS engine: {e}")
        
    # Demonstrate saving audio to a file
    output_file = Path(f"output_{service_name}.mp3")
    tts.synth_to_file(ssml_text, str(output_file), format='mp3')
    print(f"Audio content saved to {output_file}")

    # Change voice and test again if possible
    voices = tts.get_voices()
    for voice in voices[:4]:  # Limit the output to 'count' entries
        print(f"- {voice['DisplayName']} ({voice['Locale']}): {voice['ShortName']}")
    if len(voices) > 1:
        new_voice_id = voices[1]['ShortName']
        new_lang_id = voices[1]['Locale']
        print(f"running with {new_voice_id} and {new_lang_id}")
        tts.set_voice(new_voice_id,new_lang_id)
        ssml_text_part2 = tts.ssml.add('Continuing with a new voice!')
        audio_content_part2 = tts.synth_to_bytes(ssml_text_part2)
        tts.play_audio(audio_content_part2)

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    settings = load_settings()

    services = ["polly", "microsoft", "watson", "google", "elevenlabs", "deeplearning"] if service == "all" else [service]
    for svc in services:
        print(f"Testing {svc.upper()} TTS engine.")
        tts = create_tts_client(svc, settings)
        test_tts_engine(tts, svc)

if __name__ == "__main__":
    main()
