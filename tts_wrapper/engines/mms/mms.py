from typing import Any, List, Dict, Optional
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MMSClient, MMSSSML
import re
import io

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

class MMSTTS(AbstractTTS):
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

    def synth_to_bytes(self, text: Any) -> bytes:        
        text = str(text)
        if not self._is_ssml(text):
            text = self.ssml.add(text)
            text = str(text)

        extracted_text = self.extract_text_from_tags(text)
        result = self._client.synth(str(extracted_text), self._voice, self._lang)
        
        self.audio_bytes = result["audio_content"]

        prosody_text = str(text)

        if "volume=" in prosody_text:
            volume = self.get_volume_value(prosody_text)
            print("extracted volume from prosody is ", volume)
            self.audio_bytes = self.adjust_volume_value(self.audio_bytes, volume)

        return self.audio_bytes

    def adjust_volume_value(self, generated_audio: bytes, volume: float) -> bytes:
        # Ensure even length
        if len(generated_audio) % 2 != 0:
            generated_audio += b'\x00'

        # Convert to float32 array
        samples = np.frombuffer(generated_audio, dtype=np.int16).astype(np.float32) / 32768.0

        # Calculate current RMS
        rms = np.sqrt(np.mean(samples**2))

        # Normalize audio to a reference RMS (e.g., -20 dB)
        target_rms = 10**(-20/20)
        samples = samples * (target_rms / rms)

        # Apply logarithmic volume scaling
        scaled_volume = np.exp2(volume / 100) - 1  # This maps 0-100 to a 0 to 1 range logarithmically

        # Apply volume change
        samples = samples * scaled_volume

        # Soft clipping
        samples = np.tanh(samples)

        # Convert back to int16
        output_samples = (samples * 32767).astype(np.int16)
        return output_samples.tobytes()

    def get_volume_value(self, text: str) -> float:
        pattern = r'volume="(\d+)"'
        match = re.search(pattern, text)
        
        return float(match.group(1))

    def synth(self, text: Any, output_file: str) -> None:
        audio_bytes = self.synth_to_bytes(text)
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    @property
    def ssml(self) -> MMSSSML:
        return MMSSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()
