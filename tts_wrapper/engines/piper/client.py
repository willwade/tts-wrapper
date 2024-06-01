import logging
from typing import Optional, Tuple, Dict, List, Any

from ...engines.utils import process_wav
from ...exceptions import ModuleNotInstalled
import json

try:
    print("Importing piper_tts")
    import piper_tts
    from piper_tts import PiperVoice, get_voices, VoiceNotFoundError
    print("Imported piper_tts successfully")
except ImportError as e:
    piper_tts = None  # type: ignore
    print("Piper TTS not installed:", e)


Credentials = Tuple[str]

FORMATS = {
    "wav": "pcm",
    "mp3": "mp3",
}

logger = logging.getLogger(__name__)

class PiperClient:
    def __init__(
        self,
        model_path: Optional[str] = "en_US-lessac-medium.onnx",
        config_path: Optional[str] = None,
        use_cuda: Optional[bool] = False
    ) -> None:
        if piper_tts is None:
            raise ModuleNotInstalled("piper-tts")
        access_key = credentials
        self._client = PiperVoice.load(model_path, config_path, use_cuda)

    def synth(self, text: str, format: str, speaker_id: Optional[int] = None, length_scale: Optional[float] = None, noise_scale: Optional[float] = None, noise_w: Optional[float] = None, sentence_silence: float = 0.0) -> bytes:
        try:
            synthesize_args = {
                "speaker_id": speaker_id,
                "length_scale": length_scale,
                "noise_scale": noise_scale,
                "noise_w": noise_w,
                "sentence_silence": sentence_silence,
            }
            audio_stream = self._client.synthesize_stream_raw(text, **synthesize_args)
            return b''.join(audio_stream)  # Combining audio chunks into a single byte stream
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise

    def get_voices(self) -> List[Dict[str, Any]]:
        try:
            voices_info = get_voices(self._client.download_dir)
            voices = []
            for voice_id, voice_data in voices_info.items():
                lang_code = voice_data["language"]["code"].replace("_", "-")
                gender = voice_data.get("gender", "")
                voice = {
                    "id": voice_id,
                    "language_codes": [lang_code],
                    "gender": gender,
                    "full_details": voice_data
                }
                voices.append(voice)
            return voices
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    def __del__(self):
        if piper_tts is not None and hasattr(self, '_client'):
            if hasattr(self._client, 'delete'):
                self._client.delete()