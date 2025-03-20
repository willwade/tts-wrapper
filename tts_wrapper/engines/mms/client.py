import json
import os
import tempfile
from typing import Any, Optional, Union

from tts_wrapper.exceptions import (
    ModelNotFound,
    ModuleNotInstalled,
)


class MMSClient:
    def __init__(
        self, params: Optional[Union[str, tuple[Optional[str], str]]] = None
    ) -> None:
        self._using_temp_dir = False

        if isinstance(params, tuple):
            model_dir, lang = params
            self._model_dir = (
                model_dir if model_dir else os.path.expanduser("~/mms_models")
            )
        else:
            self._model_dir = os.path.expanduser("~/mms_models")
            lang = params if isinstance(params, str) else "eng"

        self.lang = lang

        if not os.path.exists(self._model_dir):
            try:
                os.makedirs(self._model_dir, exist_ok=True)
            except Exception as e:
                msg = f"Failed to create model directory {self._model_dir}: {e!s}"
                raise RuntimeError(msg)

        # Lazy load the TTS and download functions
        self._tts = None
        self._download = None
        self._initialize_tts(self.lang)

    def _initialize_tts(self, lang: str) -> None:
        if self._tts is None or self._download is None:
            try:
                from ttsmms import TTS, download

                self._tts = TTS
                self._download = download
            except ImportError:
                msg = "ttsmms"
                raise ModuleNotInstalled(msg)

            try:
                import requests
            except ImportError:
                msg = "requests"
                raise ModuleNotInstalled(msg)

        try:
            model_path = os.path.join(self._model_dir, lang)
            self._tts_instance = self._tts(model_path)
            self._tts_instance.speaking_rate = 1.5
        except Exception:
            # If TTS initialization fails, attempt to download the model
            try:
                self._download(lang, self._model_dir)
                new_model_path = os.path.join(self._model_dir, lang)
                self._tts_instance = self._tts(new_model_path)
            except Exception as download_error:
                raise ModelNotFound(lang, str(download_error))

    def synth(self, text: str, voice: str, lang: str) -> dict[str, Any]:
        # Ensure the TTS model is initialized for the correct language
        self._initialize_tts(lang)

        # Lazy load numpy and soundfile
        import numpy as np
        import soundfile as sf

        # Use a temporary file for synthesis
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()

        try:
            # Perform the synthesis
            self._tts_instance.synthesis(text, wav_path=temp_file.name)

            # Read the file using soundfile
            audio_data, sample_rate = sf.read(temp_file.name, dtype="float32")

            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)

            # Ensure the file has been written correctly
            if audio_data.size == 0:
                msg = "Synthesis resulted in an empty file."
                raise RuntimeError(msg)

            # Convert to bytes
            audio_bytes = audio_data.tobytes()

            return {
                "audio_content": audio_bytes,
                "sampling_rate": sample_rate,
            }
        except Exception as e:
            msg = f"Synthesis failed: {e!s}"
            raise RuntimeError(msg)
        finally:
            # Do not unlink the file for debugging purposes
            os.unlink(temp_file.name)

    def get_voices(self, ignore_cache: bool = False) -> list[dict[str, Any]]:
        url = "https://dl.fbaipublicfiles.com/mms/tts/all-tts-languages.html"
        cache_file = os.path.join(tempfile.gettempdir(), "mms_voices_cache.json")

        if not ignore_cache and os.path.exists(cache_file):
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass

        try:
            response = requests.get(url)
            response.encoding = "utf-8"
            response.raise_for_status()
            lines = response.text.strip().split("\n")
            standardized_voices = []

            for line in lines:
                line = line.strip()
                if not line.startswith("<p>") or not line.endswith("</p>"):
                    continue
                line = line[3:-4].replace("&emsp;", "\t").strip()
                parts = line.split("\t")
                if len(parts) == 2:
                    iso_code, language = parts
                    iso_code = iso_code.strip()  # Remove leading/trailing spaces
                    language = language.strip()  # Remove leading/trailing spaces
                    if (
                        iso_code.lower() == "iso code"
                        and language.lower() == "language name"
                    ):
                        continue  # Skip the header
                    voice = {
                        "id": iso_code,
                        "language_codes": [iso_code],
                        "name": f"{language} ({iso_code})",
                        "gender": "N",
                    }
                    standardized_voices.append(voice)

            with open(cache_file, "w") as f:
                json.dump(standardized_voices, f)
            return standardized_voices
        except requests.RequestException as e:
            msg = f"Failed to fetch voices: {e!s}"
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Error processing voices data: {e!s}"
            raise RuntimeError(msg)

    def __del__(self) -> None:
        if (
            hasattr(self, "_using_temp_dir")
            and self._using_temp_dir
            and self._model_dir
        ):
            # Clean up the temporary directory when the object is destroyed
            import shutil

            shutil.rmtree(self._model_dir, ignore_errors=True)
