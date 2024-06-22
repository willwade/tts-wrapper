import requests
import tempfile
import os
import json
from typing import List, Dict, Any, Optional
from ...exceptions import ModuleNotInstalled, UnsupportedFileFormat, ModelNotFound

try:
    from ttsmms import TTS, download
except ImportError:
    TTS = None
    download = None

class MMSClient:
    def __init__(self, model_dir: str) -> None:
        self._using_temp_dir = False
        self._model_dir = None
        self._tts = None
        
        if TTS is None or download is None:
            raise ModuleNotInstalled("ttsmms")
        if model_dir is None:
            self._model_dir = tempfile.mkdtemp(prefix="mms_models_")
            self._using_temp_dir = True
        else:
            self._model_dir = model_dir
            self._using_temp_dir = False
        

        self._tts = None

    def _initialize_tts(self, lang: str):
        try:
            model_path = os.path.join(self._model_dir, lang)
            self._tts = TTS(model_path)
        except Exception as e:
            # If TTS initialization fails, attempt to download the model
            try:
                download(lang, model_path)
                self._tts = TTS(model_path)
            except Exception as download_error:
                raise ModelNotFound(f"Failed to initialize or download model for {lang}: {str(download_error)}")


    def synth(self, text: str, voice: str, lang: str, format: str) -> Dict[str, Any]:
        # Check for supported format
        if format.lower() != "wav":
            raise UnsupportedFileFormat(format, "MMSClient")

        # Initialize TTS for the requested language if needed
        if self._tts is None or self._tts.language != lang:
            self._initialize_tts(lang)

        # Use a temporary file for synthesis
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()

        try:
            self._tts.synthesis(text, wav_path=temp_file.name)
            
            with open(temp_file.name, "rb") as f:
                audio_content = f.read()
            
            return {
                "audio_content": audio_content,
                "sampling_rate": 16000  # MMS uses a fixed sampling rate of 16kHz
            }
        except Exception as e:
            raise RuntimeError(f"Synthesis failed: {str(e)}")
        finally:
            os.unlink(temp_file.name)

    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from MMS TTS."""
        
        url = "https://dl.fbaipublicfiles.com/mms/tts/all-tts-languages.html"
        cache_file = os.path.join(tempfile.gettempdir(), "mms_voices_cache.json")
        
        # Check if cached data exists
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # If the cache is corrupted, we'll fetch the data again
                pass

        try:
            # Fetch data from URL
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the content
            lines = response.text.strip().split('\n')
            standardized_voices = []
            
            for line in lines:
                iso_code, language = line.strip().split('\t')
                voice = {
                    'id': iso_code,
                    'language_codes': [iso_code],
                    'name': f"{language} ({iso_code})",
                    'gender': 'N'  # Neutral gender as per requirement
                }
                standardized_voices.append(voice)
            
            # Cache the data
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