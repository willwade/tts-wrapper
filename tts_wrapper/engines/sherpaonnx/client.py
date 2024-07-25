# client.py
from typing import Optional, List, Dict, Tuple
import os
import json
import logging

try:
    import sherpa_onnx as sherpa_onnx
    import requests
except ImportError:
    sherpa_onnx = None  # type: ignore

class SherpaOnnxClient:
    VOICES_URL = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    CACHE_FILE = "languages-supported.json"

    def __init__(self, model_path: Optional[str] = None, tokens_path: Optional[str] = None, voice_id: Optional[str] = None):
        self.default_model_path = model_path
        self.default_tokens_path = tokens_path if tokens_path else os.path.join(model_path, 'tokens.txt') if model_path else None
        self._model_dir = os.path.expanduser("~/mms_models")
        if not os.path.exists(self._model_dir):
            try:
                os.makedirs(self._model_dir, exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Failed to create model directory {self._model_dir}: {str(e)}")
        self.voices_cache = self._load_voices_cache()
        if voice_id:
            self.set_voice(voice_id)

    def _download_voices(self):
        try:
            logging.info(f"Downloading voices JSON file from {self.VOICES_URL}...")
            response = requests.get(self.VOICES_URL)
            response.raise_for_status()
            logging.info(f"Response status code: {response.status_code}")

            # Check if response is not empty
            if not response.content.strip():
                raise ValueError("Downloaded JSON is empty")

            # Write the response to the file
            cache_file_path = os.path.join(self._model_dir, self.CACHE_FILE)
            with open(cache_file_path, 'w') as f:
                f.write(response.text)
                logging.info(f"Voices JSON file written to {cache_file_path}.")
        except Exception as e:
            logging.info(f"Failed to download voices JSON file: {e}")
            raise

    def _load_voices_cache(self):
        cache_file_path = os.path.join(self._model_dir, self.CACHE_FILE)
        if not os.path.exists(cache_file_path):
            self._download_voices()

        try:
            logging.info("Loading voices JSON file...")
            with open(cache_file_path, 'r') as f:
                content = f.read()
                if not content.strip():  # Check if file is not empty
                    raise ValueError("Cache file is empty")
                return json.loads(content)
        except Exception as e:
            logging.info(f"Failed to load voices JSON file: {e}")
            raise

    def _download_file(self, url, destination):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def _check_files_exist(self, model_path, tokens_path):
        model_exists = os.path.exists(model_path) and os.path.getsize(model_path) > 0
        tokens_exists = os.path.exists(tokens_path) and os.path.getsize(tokens_path) > 0
        return model_exists and tokens_exists

    def _download_model_and_tokens(self, iso_code, destination_dir):
        model_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/{iso_code}/model.onnx?download=true"
        tokens_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/{iso_code}/tokens.txt"

        model_path = os.path.join(destination_dir, "model.onnx")
        tokens_path = os.path.join(destination_dir, "tokens.txt")

        logging.info(f"Downloading model from {model_url}")
        self._download_file(model_url, model_path)
        logging.info(f"Model downloaded to {model_path}")

        logging.info(f"Downloading tokens from {tokens_url}")
        self._download_file(tokens_url, tokens_path)
        logging.info(f"Tokens downloaded to {tokens_path}")

        return model_path, tokens_path

    def check_and_download_model(self, iso_code: str) -> Tuple[str, str]:
        voice = next((v for v in self.voices_cache if v['Iso Code'] == iso_code), None)
        if not voice:
            raise ValueError(f"Voice with ISO code {iso_code} not found in the voices cache")

        model_dir = os.path.join(self._model_dir, iso_code)

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        model_path = os.path.join(model_dir, "model.onnx")
        tokens_path = os.path.join(model_dir, "tokens.txt")
        
        if not self._check_files_exist(model_path, tokens_path):
            logging.info(f"Downloading model and tokens for {iso_code} because we cant find it")
            model_path, tokens_path = self._download_model_and_tokens(iso_code, model_dir)
            logging.info(f"Model and tokens downloaded to {model_dir}")
        else:
            logging.info(f"Model and tokens already exist for {iso_code}")

        return model_path, tokens_path

    def synth(self, text: str, sid: int = 0, speed: float = 1.0) -> Tuple[bytes, int]:
        logging.info(f"Using model path: {self.default_model_path}")
        logging.info(f"Using tokens path: {self.default_tokens_path}")
        
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=self.default_model_path,
                    tokens=self.default_tokens_path,
                    lexicon='',  # Provide default empty string
                    data_dir='',  # Provide default empty string
                    #dict_dir=''
                )
            #provider=args.provider,
            #debug=args.debug,
            #num_threads=args.num_threads,
            ),
            #rule_fsts=args.tts_rule_fsts,
            #max_num_sentences=args.max_num_sentences,
        )
        logging.info(f"Configured TTS: {tts_config}")

        tts = sherpa_onnx.OfflineTts(tts_config)
        audio = tts.generate(text, sid=sid, speed=speed)

        if len(audio.samples) == 0:
            raise ValueError("Error in generating audio")

        audio_bytes = self._convert_audio_to_bytes(audio.samples)
        return audio_bytes, audio.sample_rate

    def get_voices(self) -> List[Dict[str, str]]:
        return [{"id": voice["Iso Code"], "name": voice["Language Name"], "gender":"N", "language_codes":[voice['Iso Code']]} for voice in self.voices_cache]

    def set_voice(self, iso_code: str):
        model_path, tokens_path = self.check_and_download_model(iso_code)
        self.default_model_path = model_path
        self.default_tokens_path = tokens_path


    def _convert_audio_to_bytes(self, audio_samples: List[float]) -> bytes:
        import struct
        return b''.join(struct.pack('<h', int(sample * 32767)) for sample in audio_samples)