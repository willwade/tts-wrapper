import logging
import os
from pathlib import Path
from typing import Any, Optional

from tts_wrapper.exceptions import ModuleNotInstalled

try:
    logging.debug("Importing piper_tts")
    from piper.download import (
        VoiceNotFoundError,
        ensure_voice_exists,
        find_voice,
        get_voices,
    )
    from piper.voice import PiperVoice
    piper_tts = True  # type: ignore
    logging.debug("Imported piper_tts successfully")
except ImportError as e:
    PiperVoice = None
    piper_tts = False  # type: ignore
    logging.debug("Piper TTS not installed:", e)


Credentials = tuple[str]

#FORMATS = {
#    "wav": "pcm",
#    "mp3": "mp3",
#}

class PiperClient:
    def __init__(
        self,
        model_path: Optional[str] = "en_US-lessac-medium",
        config_path: Optional[str] = None,
        use_cuda: Optional[bool] = False,
        download_dir: Optional[str] = None,
    ) -> None:
        if piper_tts is False:
            msg = "piper-tts"
            raise ModuleNotInstalled(msg)

        # Set download directory to first data directory by default
        if not download_dir:
            download_dir = os.path.join(os.path.expanduser("~"), ".piper", "data")
            logging.debug("Download directory not provided. Using default: %s", download_dir)
            try:
                os.makedirs(download_dir, exist_ok=True)
            except Exception as e:
                logger.exception(f"Error creating download directory: {e}")
                raise

        # Download voice if file doesn't exist
        model_path = Path(model_path)
        model_path_str = str(model_path)
        if not model_path.exists():
            # Load voice info
            try:
                self.voices_info = get_voices(download_dir, update_voices=True)

            except Exception:
                raise

            try:
                # Check if model_path is in voices_info
                if model_path_str not in self.voices_info:
                    pass
                else:
                    pass

                ensure_voice_exists(model_path_str, [download_dir], download_dir, self.voices_info)
                model_path, config_path = find_voice(model_path, [download_dir])
            except Exception as e:
                logger.exception(f"Error loading voice: {e}")
                raise
        self._client = PiperVoice.load(str(model_path), config_path, use_cuda)

    def synth(self, text: str, speaker_id: Optional[int] = None, length_scale: Optional[float] = None, noise_scale: Optional[float] = None, noise_w: Optional[float] = None, sentence_silence: float = 0.0) -> bytes:
        try:
            synthesize_args = {
                "speaker_id": speaker_id,
                "length_scale": length_scale,
                "noise_scale": noise_scale,
                "noise_w": noise_w,
                "sentence_silence": sentence_silence,
            }
            audio_stream = self._client.synthesize_stream_raw(text, **synthesize_args)
            return b"".join(audio_stream)  # Combining audio chunks into a single byte stream
        except Exception as e:
            logger.exception(f"Error synthesizing speech: {e}")
            raise

    def get_voices(self) -> list[dict[str, Any]]:
        try:
            voices = []
            for voice_id, voice_data in self.voices_info.items():
                lang_code = voice_data["language"]["code"].replace("_", "-")
                gender = voice_data.get("gender", "")
                voice = {
                    "id": voice_id,
                    "language_codes": [lang_code],
                    "gender": gender,
                    "full_details": voice_data,
                }
                voices.append(voice)
            return voices
        except Exception as e:
            logger.exception(f"Error getting voices: {e}")
            return []

    def __del__(self) -> None:
        if piper_tts is not None and hasattr(self, "_client"):
            if hasattr(self._client, "delete"):
                self._client.delete()
