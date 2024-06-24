import requests
import tempfile
import os
import json
import numpy as np
import soundfile as sf
from typing import List, Dict, Any, Optional, Union, Tuple
from ...exceptions import ModuleNotInstalled, UnsupportedFileFormat, ModelNotFound

try:
    from ttsmms import TTS, download
except ImportError:
    TTS = None
    download = None

class MMSClient:
    def __init__(self, params: Optional[Union[str, Tuple[Optional[str], str]]] = None) -> None:
        self._using_temp_dir = False
        
        if isinstance(params, tuple):
            model_dir, lang = params
            self._model_dir = model_dir if model_dir else os.path.expanduser("~/mms_models")
        else:
            self._model_dir = os.path.expanduser("~/mms_models")
            lang = params if isinstance(params, str) else 'eng'

        self.lang = lang

        if not os.path.exists(self._model_dir):
            try:
                os.makedirs(self._model_dir, exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Failed to create model directory {self._model_dir}: {str(e)}")

        if TTS is None or download is None:
            raise ModuleNotInstalled("ttsmms")

        self._initialize_tts(self.lang)

    def _initialize_tts(self, lang: str):
        try:
            model_path = os.path.join(self._model_dir, lang)
            self._tts = TTS(model_path)
        except Exception as e:
            # If TTS initialization fails, attempt to download the model
            try:
                download(lang, self._model_dir)
                new_model_path = os.path.join(self._model_dir, lang)
                self._tts = TTS(new_model_path)
            except Exception as download_error:
                raise ModelNotFound(lang, str(download_error))

    def synth(self, text: str, voice: str, lang: str, format: str) -> Dict[str, Any]:
        if format.lower() != "wav":
            raise UnsupportedFileFormat(format, "MMSClient")
        
        # Ensure the TTS model is initialized for the correct language
        self._initialize_tts(lang)

        # Use a temporary file for synthesis
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()

        try:
            # Perform the synthesis
            self._tts.synthesis(text, wav_path=temp_file.name)
            
            # Read the file using soundfile
            audio_data, sample_rate = sf.read(temp_file.name, dtype='float32')
            
            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Ensure the file has been written correctly
            if audio_data.size == 0:
                raise RuntimeError("Synthesis resulted in an empty file.")
            
            # Convert to bytes
            audio_bytes = audio_data.tobytes()
            
            return {
                "audio_content": audio_bytes,
                "sampling_rate": sample_rate
            }
        except Exception as e:
            raise RuntimeError(f"Synthesis failed: {str(e)}")
        finally:
            # Do not unlink the file for debugging purposes
            os.unlink(temp_file.name)
            
    def get_voices(self, ignore_cache: bool = False) -> List[Dict[str, Any]]:
        url = "https://dl.fbaipublicfiles.com/mms/tts/all-tts-languages.html"
        cache_file = os.path.join(tempfile.gettempdir(), "mms_voices_cache.json")
        
        if not ignore_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass

        try:
            response = requests.get(url)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            standardized_voices = []

            for line in lines:
                line = line.strip()
                if not line.startswith("<p>") or not line.endswith("</p>"):
                    continue
                line = line[3:-4].replace("&emsp;", "\t").strip()
                parts = line.split('\t')
                if len(parts) == 2:
                    iso_code, language = parts
                    iso_code = iso_code.strip()  # Remove leading/trailing spaces
                    language = language.strip()  # Remove leading/trailing spaces
                    if iso_code.lower() == "iso code" and language.lower() == "language name":
                        continue  # Skip the header
                    voice = {
                        'id': iso_code,
                        'language_codes': [iso_code],
                        'name': f"{language} ({iso_code})",
                        'gender': 'N'
                    }
                    standardized_voices.append(voice)

            with open(cache_file, 'w') as f:
                json.dump(standardized_voices, f)
            return standardized_voices
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch voices: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error processing voices data: {str(e)}")

            
    def __del__(self):
        if hasattr(self, '_using_temp_dir') and self._using_temp_dir and self._model_dir:
            # Clean up the temporary directory when the object is destroyed
            import shutil
            shutil.rmtree(self._model_dir, ignore_errors=True)
