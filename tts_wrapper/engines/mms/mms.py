from typing import Any, List, Dict, Optional
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MMSClient, MMSSSML
import re
import numpy as np
import io

class MMSTTS(AbstractTTS):
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav"]  # MMS only supports WAV format

    def __init__(self, client: MMSClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self._lang = lang or "eng"  # Default to English
        self._voice = voice or self._lang  # Use lang as voice ID for MMS
        self.audio_rate = 16000


    def construct_prosody_tag(self, text:str ) -> str:
        properties = []
        #commenting this for now as we don't have ways to control rate and pitch without ssml
        #rate = self.get_property("rate")
        #if rate != "":            
        #    properties.append(f'rate="{rate}"')
        #        
        #pitch = self.get_property("pitch")
        #if pitch != "":
        #    properties.append(f'pitch="{pitch}"')
    
        volume = self.get_property("volume")
        if volume != "":
            properties.append(f'volume="{volume}"')
        
        prosody_content = " ".join(properties)
        
        #text_with_tag = f'<prosody {property}="{volume_in_words}">{text}</prosody>'        
        text_with_tag = f'<prosody {prosody_content}>{text}</prosody>'

        return text_with_tag
        
    def extract_text_from_tags(self, input_string: str) -> str:
        pattern = r'<[^>]+>(.*?)</[^>]+>'
        match = re.search(pattern, input_string)
        if match:
            return str(match.group(1))
        return input_string

    def synth_to_bytes(self, text: Any, format: Optional[FileFormat] = "wav") -> bytes:
        if format not in self.supported_formats():
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)

        extracted_text = self.extract_text_from_tags(text)
        result = self._client.synth(str(extracted_text), self._voice, self._lang, format)
        
        self.audio_bytes = result["audio_content"]

        prosody_text = str(text)

        if "volume=" in prosody_text:
            volume = self.get_volume_value(prosody_text)
            self.audio_bytes = self.adjust_volume_value(self.audio_bytes, volume, format)

        return self.audio_bytes

    def adjust_volume_value(self, generated_audio: bytes, volume: float, format: str) -> bytes:
        #check if generated audio length is odd. If it is, add an empty byte since np.frombuffer is expecting
        #an even length
        if len(generated_audio)%2 != 0:
            generated_audio += b'\x00'

        generated_audio = np.frombuffer(generated_audio, dtype=np.int16)

        # Convert to float32 for processing
        samples_float = generated_audio.astype(np.float32) / 32768.0  # Normalize to [-1.0, 1.0]

        # Scale the samples with the volume
        scaled_volume = volume/100
        scaled_audio = scaled_volume * samples_float
        
        # Clip the values to make sure they're in the valid range for paFloat32
        clipped_audio = np.clip(scaled_audio, -1.0, 1.0)
        # Convert back to int16
        output_samples = (clipped_audio * 32768).astype(np.int16)
        output_bytes = output_samples.tobytes()

        return output_bytes

    def get_volume_value(self, text: str) -> float:
        pattern = r'volume="(\d+)"'
        match = re.search(pattern, text)
        
        return float(match.group(1))

    def synth(self, text: Any, output_file: str, format: Optional[FileFormat] = "wav") -> None:
        if format.lower() != "wav":
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        
        audio_bytes = self.synth_to_bytes(text, format)
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    @property
    def ssml(self) -> MMSSSML:
        return MMSSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()
