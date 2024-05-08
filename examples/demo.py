from tts_wrapper import PollyTTS, PollyClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, GoogleTTS, GoogleClient, ElevenLabsTTS, ElevenLabsClient
import sys
import json

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        print("Settings file not found. Ensure 'settings.json' is in the correct location.")
        return {}

def create_tts_client(service, settings):
    if service == "polly":
        creds = settings.get('Polly', {})
        client = PollyClient(credentials=(creds.get('region'), creds.get('aws_key_id'), creds.get('aws_access_key')))
        tts = PollyTTS(client=client)
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
    elif service == "elevenlabs":
        creds = settings.get('ElevenLabs', {})
        client = ElevenLabsClient(credentials=creds.get('API_KEY'))
        tts = ElevenLabsTTS(client=client)
    else:
        raise ValueError("Unsupported TTS service")
    return client, tts


engines = [ "elevenlabs", "polly", "google", "microsoft", "watson"] 
settings = load_settings()

for engine in engines:
    client, tts = create_tts_client(engine,settings)
    ssml_text = tts.ssml.add(f"This is me speaking with Speak function and {engine}")
    #NB: If you dont provide a voice in the TTS init e.g.
    # tts = MicrosoftTTS(client=client,voice="Voice ID") 
    #we will pick a default English one
    print(f"speaking with {engine}")
    tts.speak(ssml_text) 

    #Lets save that as a file. 
    tts.synth_to_file(ssml_text, f"output_{engine}.mp3", format='mp3')
    
    #So lets choose a new voice
    voices = tts.get_voices()

    english_voices = [v for v in voices if any(lang.startswith('en') for lang in v.get('language_codes', []))]
    if english_voices:
        new_voice_id = english_voices[0].get('id')
        new_lang_id = english_voices[0].get('language_codes', [])[0]
        print(f"Switching to voice ({engine}): {new_voice_id} Language: {new_lang_id}")
        tts.set_voice(new_voice_id, new_lang_id)
        
        # Demo speaking streamed with a new voice
        ssml_text_part2 = tts.ssml.add(f"Continuing with a new voice using {engine}!")
        audio_content_part2 = tts.synth_to_bytes(ssml_text_part2)
        tts.speak_streamed(audio_content_part2)       
    exit()
