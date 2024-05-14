from typing import Optional, Tuple, Dict, List, Any

from ...engines.utils import process_wav
from ...exceptions import ModuleNotInstalled
import json

try:
    import piper
except ImportError:
    pvPiper = None  # type: ignore

Credentials = Tuple[str]

FORMATS = {
    "wav": "pcm",
    "mp3": "mp3",
}


class PiperClient:
    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        use_cuda: bool = False,
        credentials: Optional[Credentials] = None,
    ) -> None:
        if piper is None:
            raise ModuleNotInstalled("piper-tts")
        access_key = credentials
        self._client = PiperVoice.load(model_path, config_path, use_cuda)

    def synth(self, text: str, voice: str, format: str) -> bytes:
        synthesize_args = {
        "speaker_id": args.speaker,
        "length_scale": args.length_scale,
        "noise_scale": args.noise_scale,
        "noise_w": args.noise_w,
        "sentence_silence": args.sentence_silence,
        }
        audio_stream = self._voice.synthesize_raw(text,**synthesize_args)
        return audio_stream


   def get_voices(self) -> List[Dict[str, Any]]:
        voice_data = piper.get_voices()
        voices = []
        # Iterate over the voices
        for voice_id, voice_data in voices_data.items():
            lang_code = voice_data["language"]["code"].replace("_", "-")
            gender = voice_data.get("gender", "")

            # Add voice to the list
            voice = {
                "id": voice_id,
                "language_codes": [lang_code],
                "gender": gender
                "full_details": voice_data
            }
            voices.append(voice)

    def __del__(self):
        """Ensure resources are cleaned up."""
        self._client.delete()