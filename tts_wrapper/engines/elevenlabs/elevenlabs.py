from typing import Any, List, Dict, Optional, Tuple
from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import ElevenLabsClient, ElevenLabsSSMLRoot
import re
import numpy as np
import pathlib

class ElevenLabsTTS(AbstractTTS):
    def __init__(self, client: ElevenLabsClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self.audio_rate = 22050  # Kept at 22050
        self.set_voice(voice or "yoZ06aMxZJJ28mfd3POQ", lang or "en-US")

    def synth_to_bytes(self, text: Any) -> bytes:
        if not self._voice:
            raise ValueError("Voice ID must be set before synthesizing speech.")

        # Get the audio and word timings from the ElevenLabs API
        self.generated_audio, word_timings = self._client.synth(str(text), self._voice)
        self.set_timings(word_timings)

        prosody_text = str(text)
        if "volume=" in prosody_text:
            volume = self.get_volume_value(prosody_text)
            self.generated_audio = self.adjust_volume_value(self.generated_audio, volume)

        #check if wav file has header. Strip header to make it raw
        if self.generated_audio[:4] == b'RIFF':
            self.generated_audio = tts._strip_wav_header(self.generated_audio)

        return self.generated_audio

    def get_audio_duration(self) -> float:
        """
        Calculate the duration of the audio based on the number of samples and sample rate.
        """
        if self.generated_audio is not None:
            num_samples = len(self.generated_audio) // 2  # Assuming 16-bit audio
            return num_samples / self.audio_rate
        return 0.0

    def adjust_volume_value(self, generated_audio: bytes, volume: float) -> bytes:
        #check if generated audio length is odd. If it is, add an empty byte since np.frombuffer is expecting
        #an even length
        
        try:
            import numpy as np
        except ImportError:
            raise ModuleNotInstalled("numpy")

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

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_voices()

    def construct_prosody_tag(self, text:str ) -> str:
        properties = []

        #commenting this for now as we don't have ways to control rate and pitch without ssml
        rate = self.get_property("rate")
        if rate != "":            
            properties.append(f'rate="{rate}"')
        #        
        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')
    
        volume = self.get_property("volume")
        if volume != "":
            properties.append(f'volume="{volume}"')
        
        prosody_content = " ".join(properties)
        
        #text_with_tag = f'<prosody {property}="{volume_in_words}">{text}</prosody>'        
        text_with_tag = f'<prosody {prosody_content}>{text}</prosody>'
        
        return text_with_tag

    @property
    def ssml(self) -> ElevenLabsSSMLRoot:
        return ElevenLabsSSMLRoot()
        
    def set_voice(self, voice_id: str, lang_id: str=None):
        """Updates the currently set voice ID."""
        super().set_voice(voice_id)
        self._voice = voice_id
        #NB: Lang doesnt do much for ElevenLabs
        self._lang = lang_id
