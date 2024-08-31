import objc
from AppKit import NSSpeechSynthesizer
from Foundation import NSURL
from PyObjCTools import AppHelper
import time

NSObject = objc.lookUpClass('NSObject')

class MacOSClient(NSObject):
    def init(self):
        self = objc.super(MacOSClient, self).init()
        if self is None: return None
        
        self._tts = NSSpeechSynthesizer.alloc().initWithVoice_(None)
        self._tts.setDelegate_(self)
        self.word_timings = []
        self.speech_start_time = None
        return self

    @classmethod
    def new(cls):
        return cls.alloc().init()

    @objc.python_method
    def set_voice(self, voice_id):
        self._tts.setVoice_(voice_id)

    @objc.python_method
    def set_rate(self, rate):
        if isinstance(rate, str):
            if rate == "high":
                self._tts.setRate_(300)
            elif rate == "low":
                self._tts.setRate_(100)
            else:
                self._tts.setRate_(200)  # Default
        else:
            self._tts.setRate_(float(rate))

    @objc.python_method
    def set_volume(self, volume):
        self._tts.setVolume_(volume)

    @objc.python_method
    def get_voices(self):
        voices = []
        for voice_id in NSSpeechSynthesizer.availableVoices():
            attrs = NSSpeechSynthesizer.attributesForVoice_(voice_id)
            voice_data = {
                'id': attrs['VoiceIdentifier'],
                'name': attrs['VoiceName'],
                'languages': str(attrs.get('VoiceLocaleIdentifier', attrs.get('VoiceLanguage'))).replace('_', '-'),
                'gender': attrs.get('VoiceGender', 'unknown'),
                'age': attrs.get('VoiceAge', 'unknown'),
                'voice_uri': attrs['VoiceIdentifier']
            }
            voices.append(voice_data)
        return voices

    @objc.python_method
    def synth_with_timings(self, text, voice_id, format='wav'):
        self.set_voice(voice_id)
        self.word_timings.clear()
        self.speech_start_time = time.time()
        self._tts.startSpeakingString_(text)

        while self._tts.isSpeaking():
            AppHelper.runConsoleEventLoop(mode=None, handleEvents=True)

        return b'', self.word_timings

    @objc.python_method
    def save_to_file(self, text, filename):
        url = NSURL.fileURLWithPath_(filename)
        self._tts.startSpeakingString_toURL_(text, url)

    def speechSynthesizer_willSpeakWord_ofString_(self, synthesizer, wordRange, string):
        current_time = time.time()
        start_time = (current_time - self.speech_start_time) * 1000.0
        word = string[wordRange.location:wordRange.location + wordRange.length]
        print(f"Word: '{word}' Start: {start_time} ms")
        duration = wordRange.length / 10.0  # Adjust this calculation as needed
        self.word_timings.append((start_time, duration, word))