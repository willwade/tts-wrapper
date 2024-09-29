import os
import unittest

from pathlib import Path
import time
from tts_wrapper import (
    PollyClient, PollyTTS, 
    GoogleClient, GoogleTTS, 
    MicrosoftClient, MicrosoftTTS, 
    WatsonClient, WatsonTTS,
    ElevenLabsClient, ElevenLabsTTS,
    WitAiClient, WitAiTTS,
    GoogleTransClient, GoogleTransTTS,
    SherpaOnnxClient, SherpaOnnxTTS
)

from load_credentials import load_credentials
# Load credentials
load_credentials('credentials-private.json')

elevenlabsclient = ElevenLabsClient(credentials=(os.getenv('ELEVENLABS_API_KEY')))
elevenlabstts = ElevenLabsTTS(elevenlabsclient)

googleclient = GoogleClient(credentials=os.getenv('GOOGLE_CREDS_PATH'))
googletts = GoogleTTS(googleclient)

voice_id = "en-co.uk"  # Example voice ID for UK English
googletransclient = GoogleTransClient(voice_id)
googletranstts = GoogleTransTTS(googletransclient)

load_credentials('credentials.json')
microsoftclient = MicrosoftClient(credentials=(os.getenv('MICROSOFT_TOKEN'), os.getenv('MICROSOFT_REGION')))
microsofttts = MicrosoftTTS(microsoftclient)

pollyclient = PollyClient(credentials=(os.getenv('POLLY_REGION'),os.getenv('POLLY_AWS_KEY_ID'), os.getenv('POLLY_AWS_ACCESS_KEY')))
pollytts = PollyTTS(pollyclient)

sherpaonnxclient = SherpaOnnxClient(model_path=None, tokens_path=None)
sherpaonnxtts = SherpaOnnxTTS(client=sherpaonnxclient)
voices = sherpaonnxtts.get_voices()
iso_code = "eng"  # Replace with a valid ISO code from the voices list
sherpaonnxtts.set_voice(voice_id=iso_code)

api_key = os.getenv('WATSON_API_KEY')
region = os.getenv('WATSON_REGION')
instance_id = os.getenv('WATSON_INSTANCE_ID')
watsonclient = WatsonClient(credentials=(api_key, region, instance_id))
watsontts = WatsonTTS(client=watsonclient)

wtaiclient = WitAiClient(credentials=(os.getenv('WITAI_TOKEN')))
wtaitts = WitAiTTS(wtaiclient)

class TestFileCreation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.success_count = 0

    @classmethod
    def tearDownClass(cls):
        print(f"\nSuccessfully passed {cls.success_count} tests.")

    def setUp(self):
        self.google_filename = "google-test.wav"
        self.googletrans_filename = "googletrans-test.wav"
        self.elevenlabs_filename = "elevenlabs-test.wav"
        self.microsoft_filename = "microsoft-test.wav"
        self.polly_filename = "polly-test.wav"
        self.sherpaonnx_filename = "sherpaonnx-test.wav"
        self.watson_filename = "watson-test.wav"
        self.wtai_filename = "wtai-test.wav"


    def tearDown(self):
        if os.path.exists(self.google_filename):
            os.remove(self.google_filename)
        if os.path.exists(self.elevenlabs_filename):
            os.remove(self.elevenlabs_filename)
        if os.path.exists(self.googletrans_filename):
            os.remove(self.googletrans_filename)
        if os.path.exists(self.microsoft_filename):
            os.remove(self.microsoft_filename)
        if os.path.exists(self.polly_filename):
            os.remove(self.polly_filename)
        if os.path.exists(self.sherpaonnx_filename):
            os.remove(self.sherpaonnx_filename)
        if os.path.exists(self.watson_filename):
            os.remove(self.watson_filename)
        if os.path.exists(self.wtai_filename):
            os.remove(self.wtai_filename)

    def test_google_audio_creation(self):
        ssml_text = googletts.ssml.add(f"This is me speaking with speak_streamed function and google")
        print(ssml_text)
        googletts.speak_streamed(ssml_text,self.google_filename,"wav")        
        self.assertTrue(os.path.exists(self.google_filename))
        print(f"Test passed: File '{self.google_filename}' was created successfully.")
        self.__class__.success_count += 1        

    def test_elevenlabs_audio_creation(self):
        ssml_text = elevenlabstts.ssml.add(f"This is me speaking with speak_streamed function and elevenlabs")
        print(ssml_text)
        elevenlabstts.speak_streamed(ssml_text,self.elevenlabs_filename,"wav")
        self.assertTrue(os.path.exists(self.elevenlabs_filename))
        print(f"Test passed: File '{self.elevenlabs_filename}' was created successfully.")
        self.__class__.success_count += 1        

    def test_googletrans_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and googletrans"
        print(ssml_text)
        googletranstts.speak_streamed(ssml_text,self.googletrans_filename,"wav")
        self.assertTrue(os.path.exists(self.googletrans_filename))
        print(f"Test passed: File '{self.googletrans_filename}' was created successfully.")
        self.__class__.success_count += 1        

    def test_microsoft_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and microsoft"
        print(ssml_text)        
        microsofttts.speak_streamed(ssml_text,self.microsoft_filename,"wav")
        self.assertTrue(os.path.exists(self.microsoft_filename))
        print(f"Test passed: File '{self.microsoft_filename}' was created successfully.")
        self.__class__.success_count += 1        

    def test_polly_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and polly"
        print(ssml_text)        
        pollytts.speak_streamed(ssml_text,self.polly_filename,"wav")
        self.assertTrue(os.path.exists(self.polly_filename))
        print(f"Test passed: File '{self.polly_filename}' was created successfully.")
        self.__class__.success_count += 1   

    def test_sherpaonnx_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and sherpaonnx"
        print(ssml_text)        
        sherpaonnxtts.speak_streamed(ssml_text,self.sherpaonnx_filename,"wav")
        self.assertTrue(os.path.exists(self.sherpaonnx_filename))
        print(f"Test passed: File '{self.sherpaonnx_filename}' was created successfully.")
        self.__class__.success_count += 1   

    def test_watson_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and watson"
        print(ssml_text)        
        watsontts.speak_streamed(ssml_text,self.watson_filename,"wav")
        self.assertTrue(os.path.exists(self.watson_filename))
        print(f"Test passed: File '{self.watson_filename}' was created successfully.")
        self.__class__.success_count += 1   

    def test_wtai_audio_creation(self):
        ssml_text = f"This is me speaking with speak_streamed function and WTAI"
        print(ssml_text)        
        wtaitts.speak_streamed(ssml_text,self.wtai_filename,"wav")
        self.assertTrue(os.path.exists(self.wtai_filename))
        print(f"Test passed: File '{self.wtai_filename}' was created successfully.")
        self.__class__.success_count += 1 

if __name__ == '__main__':
    unittest.main(verbosity=1)