# client.py
from typing import List, Dict, Any
from ...exceptions import UnsupportedFileFormat
from io import BytesIO
import wave
import logging

try:
    from gtts import gTTS
    from gtts.lang import tts_langs
    from pydub import AudioSegment
except ImportError:
    gtts = None  # type: ignore

FORMATS = {
    "mp3": "mp3",
    "wav": "wav"
}

class GoogleTransClient:
    def __init__(self, voice_id='en-co.uk'):
        self.lang, self.tld = self._parse_voice_id(voice_id)

    def _parse_voice_id(self, voice_id: str):
        parts = voice_id.split('-')
        lang = parts[0]
        tld = parts[1] if len(parts) > 1 else 'com'
        return lang, tld

    def set_voice(self, voice_id: str):
        self.lang, self.tld = self._parse_voice_id(voice_id)
    
    def synth(self, text: str, format: str) -> bytes:
        tts = gTTS(text, lang=self.lang, tld=self.tld)

        mp3_fp = BytesIO()
        for chunk in tts.stream():
            mp3_fp.write(chunk)
        mp3_fp.seek(0)

        if format == 'mp3':
            return mp3_fp.read()
        elif format == 'wav':
            mp3_fp.seek(0)
            audio = AudioSegment.from_file(mp3_fp, format="mp3")
            wav_fp = BytesIO()
            audio.export(wav_fp, format="wav")
            wav_fp.seek(0)
            return wav_fp.read()
        else:
            raise UnsupportedFileFormat(format, 'GoogleTransClient')        
        
    def get_voices(self) -> List[Dict[str, Any]]:
        # Retrieve available languages from gtts
        languages = tts_langs()
        standardized_voices = []
        accents = {
            'en': ['com.au', 'co.uk', 'us', 'ca', 'co.in', 'ie', 'co.za', 'com.ng'],
            'fr': ['ca', 'fr'],
            'zh-CN': ['any'],
            'zh-TW': ['any'],
            'pt': ['com.br', 'pt'],
            'es': ['com.mx', 'es', 'us']
        }
        
        for lang_code, lang_name in languages.items():
            if lang_code in accents:
                for accent in accents[lang_code]:
                    standardized_voices.append({
                        'id': f"{lang_code}-{accent}",
                        'language_codes': [lang_code],
                        'name': f"{lang_name} ({accent})",
                        'gender': 'Unknown'
                    })
            else:
                standardized_voices.append({
                    'id': lang_code,
                    'language_codes': [lang_code],
                    'name': lang_name,
                    'gender': 'Unknown'
                })
                
        return standardized_voices