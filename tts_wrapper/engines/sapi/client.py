from typing import Optional, Tuple, Dict, List, Any
from ...exceptions import ModuleNotInstalled
from ..utils import create_temp_filename
import os
import platform

Credentials = Tuple[str]

FORMATS = {
    "wav": "wav"
}

class SAPIClient:
    def __init__(self):
        try:
            from comtypes import client
            from comtypes.gen import SpeechLib
            engine = client.CreateObject("SAPI.SpVoice")
            stream = client.CreateObject("SAPI.SpFileStream")
            self._tts = client.CreateObject('SAPI.SpVoice')
        except ImportError:
            raise ModuleNotInstalled("comtypes is not installed")

    def synth(self, text, filename=None):
        if filename:
            # Save speech to file
            stream = client.CreateObject('SAPI.SpFileStream')
            stream.Open(filename, SpeechLib.SSFMCreateForWrite)
            self._tts.AudioOutputStream = stream
            self._tts.Speak(text)
            stream.Close()
        else:
            # Speak directly
            self._tts.Speak(text)

    def synth_with_timings(self, text, voice_id, format='wav'):
        # Set the voice
        self.set_voice(voice_id)

        # Create a temporary stream to capture audio data and word timings
        audio_stream = client.CreateObject('SAPI.SpMemoryStream')
        self._tts.AudioOutputStream = audio_stream
        word_timings = []

        def on_word_start(_stream_number, _stream_position, _character_position, length):
            # Capture the start time and length of each word
            word_timings.append((_character_position, length))

        # Add event listener for word start
        self._tts.EventInterests = SpeechLib.SpeechVoiceEvents.SVEWordBoundary
        self._tts.SetNotifySink(on_word_start)

        # Speak the text, capture audio
        self._tts.Speak(text, SpeechLib.SpeechVoiceSpeakFlags.SVSFlagsAsync)

        # Wait for speaking to finish
        while self._tts.Status.RunningState == SpeechLib.SpeechRunState.SRSEIsSpeaking:
            pythoncom.PumpWaitingMessages()

        # Retrieve audio data
        audio_stream.Seek(0, 0)
        audio_data = audio_stream.Read(audio_stream.Seek(0, 2))

        return audio_data, word_timings

    def _standardize_gender(self, gender):
        # Example function to standardize gender; can be customized
        gender_map = {
            SpeechLib.SpeechVoiceGender.SVGFemale: 'Female',
            SpeechLib.SpeechVoiceGender.SVGMale: 'Male',
            SpeechLib.SpeechVoiceGender.SVGBoth: 'Both',
            SpeechLib.SpeechVoiceGender.SVGUnknown: 'Unknown'
        }
        return gender_map.get(gender, 'unknown')

    def get_voices(self):
        voices = self._tts.GetVoices()
        standardized_voices = []

        for voice in voices:
            voice_data = {
                'id': voice.Id,
                'name': voice.GetDescription(),
                'languages': str(voice.GetAttribute('Language')).replace('_', '-'),
                'gender': self._standardize_gender(voice.GetAttribute('Gender')),
                'age': voice.GetAttribute('Age'),  # Placeholder; actual attribute name may differ
                'voice_uri': voice.Id
            }
            standardized_voices.append(voice_data)

        return standardized_voices
    
    def set_voice(self, voice_id):
        for token in self._tts.GetVoices():
            if token.Id == voice_id:
                self._tts.Voice = token
                break

    def set_rate(self, rate):
        self._tts.Rate = rate

    def set_volume(self, volume):
        self._tts.Volume = int(volume * 100)