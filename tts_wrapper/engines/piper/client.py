import logging
from typing import Optional, Tuple, Dict, List, Any

from ...engines.utils import process_wav
from ...exceptions import ModuleNotInstalled
import json
from pathlib import Path
import os

try:
    print("Importing piper_tts")
    from piper.voice import PiperVoice
    from piper.download import get_voices, ensure_voice_exists, find_voice, VoiceNotFoundError
    piper_tts = True  # type: ignore
    print("Imported piper_tts successfully")
except ImportError as e:
    piper_tts = False  # type: ignore
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
        model_path: Optional[str] = "en_US-lessac-medium",
        config_path: Optional[str] = None,
        use_cuda: Optional[bool] = False,
        download_dir: Optional[str] = None
    ) -> None:
        if piper_tts is False:
            raise ModuleNotInstalled("piper-tts")

        # Set download directory to first data directory by default
        if not download_dir:
            download_dir = os.path.join(os.path.expanduser('~'), '.piper', 'data')
            logging.debug(f"Download directory not provided. Using default: {download_dir}")
            try:
                os.makedirs(download_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Error creating download directory: {e}")
                raise

        # Download voice if file doesn't exist
        model_path = Path(model_path)
        model_path_str = str(model_path)
        if not model_path.exists():
            # Load voice info
            try:
                self.voices_info = get_voices(download_dir, update_voices=True)

            except Exception as e:
                print(f"Error getting voices: {e}")  # Print any exceptions raised by get_voices
                raise

            try:

                print(f"Model path: {model_path}")
                print(f"Voices info keys: {self.voices_info.keys()}")
                # Check if model_path is in voices_info
                if model_path_str not in self.voices_info:
                    print(f"Voice not found in voices_info: {model_path_str}")
                else:
                    print(f"Voice found in voices_info: {model_path_str}")

                print(f"Ensuring voice exists: {model_path}, {download_dir}, {download_dir}")
                ensure_voice_exists(model_path_str, [download_dir], download_dir, self.voices_info)
                print(f"Voice exists: {model_path}")
                print(f"Finding voice: {model_path}, {download_dir}")
                model_path, config_path = find_voice(model_path, [download_dir])
            except Exception as e:
                logger.error(f"Error loading voice: {e}")
                raise
        print(f"Loading voice: {model_path}, {config_path}, {use_cuda}")    
        self._client = PiperVoice.load(str(model_path), config_path, use_cuda)

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
            voices = []
            for voice_id, voice_data in self.voices_info.items():
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