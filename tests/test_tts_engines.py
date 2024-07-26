import os
import pytest
from pathlib import Path
import time
from tts_wrapper import (
    PollyClient, PollyTTS, 
    GoogleClient, GoogleTTS, 
    MicrosoftClient, MicrosoftTTS, 
    WatsonClient, WatsonTTS,
    ElevenLabsClient, ElevenLabsTTS,
    WitAiClient, WitAiTTS,
    GoogleTransClient, GoogleTransTTS
)

# Dictionary to hold the TTS clients and their respective setup functions
TTS_CLIENTS = {
    "polly": {
        "client": lambda: PollyClient(credentials=(
            os.getenv('POLLY_REGION'), 
            os.getenv('POLLY_AWS_KEY_ID'), 
            os.getenv('POLLY_AWS_ACCESS_KEY')
        )),
        "class": PollyTTS
    },
    "google": {
        "client": lambda: GoogleClient(credentials=os.getenv('GOOGLE_SA_PATH')),
        "class": GoogleTTS
    },
    "microsoft": {
        "client": lambda: MicrosoftClient(credentials=(
            os.getenv('MICROSOFT_TOKEN'), 
            os.getenv('MICROSOFT_REGION')
        )),
        "class": MicrosoftTTS
    },
    "watson": {
        "client": lambda: WatsonClient(credentials=(
            os.getenv('WATSON_API_KEY'), 
            os.getenv('WATSON_REGION'), 
            os.getenv('WATSON_INSTANCE_ID')
        )),
        "class": WatsonTTS
    },
    "elevenlabs": {
        "client": lambda: ElevenLabsClient(credentials=os.getenv('ELEVENLABS_API_KEY')),
        "class": ElevenLabsTTS
    },
    "witai": {
        "client": lambda: WitAiClient(credentials=os.getenv('WITAI_TOKEN')),
        "class": WitAiTTS
    },
    "googletrans": {
        "client": lambda: GoogleTransClient('en-co.uk'),
        "class": GoogleTransTTS
    }
}

def create_tts_client(service):
    config = TTS_CLIENTS[service]
    client = config["client"]()
    tts_class = config["class"]
    tts = tts_class(client)
    return tts

@pytest.mark.parametrize("service", TTS_CLIENTS.keys())
def test_tts_engine(service):
    tts = create_tts_client(service)

    # Plain text demo
    text_read = 'Hello, world! This is a text of plain text sending'
    try:
        print(f"Testing {service} TTS engine...in a plain text demo")
        tts.speak(text_read)
    except Exception as e:
        print(f"Error testing {service} TTS engine at speak with plain text: {e}")

    # SSML with prosody control
    try:
        text_read = 'Hello, world!'
        text_with_prosody = tts.construct_prosody_tag(text_read)
        
        tts.ssml.clear_ssml()
        ssml_text = tts.ssml.add(text_with_prosody)
       
        try:
            print(f"Testing {service} TTS engine...volume control")
            tts.speak_streamed(ssml_text)

            time.sleep(3)
            tts.ssml.clear_ssml()

            tts.set_property("volume","90")
            tts.set_property("pitch","x-high")
            
            text_read_2 = "This is louder than before"
            text_with_prosody = tts.construct_prosody_tag(text_read_2)
            time.sleep(0.5)
            ssml_text = tts.ssml.add(text_with_prosody)
            print("ssml_test: ", ssml_text)
            print ("Testing setting volume to extra loud")
            tts.speak_streamed(ssml_text)
        
            time.sleep(1)
            
        except Exception as e:
            print(f"Error testing {service} TTS engine at speak_streamed (volume control): {e}")

    except Exception as e:
        print(f"Error testing {service} TTS engine: {e}")

    # Save to audio file
    try:
        tts.ssml.clear_ssml()
        ssml_text = tts.ssml.add('Lets save to an audio file')  
        output_file = Path(f"output_{service}.wav")
        tts.synth(ssml_text, str(output_file), format='wav')
        print(f"Audio content saved to {output_file}")
    except Exception as e:
        print(f"Error testing {service} TTS engine at synth to file: {e}")

    # Change voice and test again if possible
    try:
        voices = tts.get_voices()
        print('Getting voices')
        for voice in voices[:4]:  # Show details for first four voices
            language_codes = voice.get('language_codes', [])
            display_name = voice.get('name', 'Unknown voice')
            first_language_code = language_codes[0] if language_codes else 'Unknown'
            print(f"{display_name} ({first_language_code}): {voice['id']}")
        if len(voices) > 1:
            new_voice_id = voices[1].get('id')
            new_lang_codes = voices[1].get('language_codes', [])
            new_lang_id = new_lang_codes[0] if new_lang_codes else 'Unknown'
            print(f"Running with {new_voice_id} and {new_lang_id}")
            tts.set_voice(new_voice_id, new_lang_id)
            ssml_text_part2 = tts.ssml.add('Continuing with a new voice!')
            tts.speak_streamed(ssml_text_part2)
    except Exception as e:
        print(f"Error testing {service} TTS engine at voice change: {e}")
