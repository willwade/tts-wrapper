# examples/all_engines_example.py
import sys
import json
import logging
from tts_wrapper import PollyTTS, PollyClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, GoogleTTS, GoogleClient, ElevenLabsTTS, ElevenLabsClient, DeepLearningTTSTTS, DeepLearningTTSClient
from tts_wrapper.audio_player import AudioPlayer

def load_settings_from_file():
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
        client = MicrosoftClient(credentials=creds.get('TOKEN'))
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

def test_tts_engine(tts):
    text_read = 'Hello, world!'
    audio_content = tts.synth_to_bytes(text_read, 'mp3')
    tts.play_audio(audio_content)
    input("Press enter to pause...")
    tts.pause_audio()
    input("Press enter to resume...")
    tts.resume_audio()
    input("Press enter to stop...")
    tts.stop_audio()

    voices = tts.get_voices()
    print("Available Voices:", voices)

    if len(voices) > 1:
        tts.set_voice(voices[1]['name'])
        text_read_part2 = 'Continuing with a new voice!'
        audio_content = tts.synth_to_bytes(text_read_part2, 'mp3')
        tts.play_audio(audio_content)

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    settings = load_settings_from_file()

    services = ["polly", "
