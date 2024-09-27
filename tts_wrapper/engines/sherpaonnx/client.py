# client.py
from typing import Optional, List, Dict, Tuple
import os
import json
import logging
import threading

try:
    import numpy as np
except ImportError:
    logging.error("Please install numpy library to use the SherpaOnnxClient")
    np = None  # type: ignore

try:
    import queue
except ImportError:
    logging.error("Please install queue library to use the SherpaOnnxClient")
    queue = None  # type: ignore


class SherpaOnnxClient:
    VOICES_URL = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    CACHE_FILE = "languages-supported.json"

    def __init__(
        self,
        model_path: Optional[str] = None,
        tokens_path: Optional[str] = None,
        voice_id: Optional[str] = None,
    ):
        try:
            import sherpa_onnx
        except ImportError:
            logging.error(
                "Please install sherpa-onnx library to use the SherpaOnnxClient"
            )
            sherpa_onnx = None  # type: ignore

        try:
            import requests
        except ImportError:
            logging.error("Please install requests library to use the SherpaOnnxClient")
            requests = None

        try:
            import threading
        except ImportError:
            logging.error(
                "Please install threading library to use the SherpaOnnxClient"
            )
            threading = None  # type: ignore

        self.default_model_path = model_path
        self.default_tokens_path = (
            tokens_path
            if tokens_path
            else os.path.join(model_path, "tokens.txt") if model_path else None
        )
        self._model_dir = (
            model_path if model_path else os.path.expanduser("~/mms_models")
        )
        if not os.path.exists(self._model_dir):
            try:
                os.makedirs(self._model_dir, exist_ok=True)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create model directory {self._model_dir}: {str(e)}"
                )
        self.voices_cache = self._load_voices_cache()
        if voice_id:
            self.set_voice(voice_id)
        self.audio_queue = queue.Queue()
        self.tts = None
        self.sample_rate = None

    def _download_voices(self):
        try:
            try:
                import requests
            except ImportError:
                raise ImportError(
                    "Please install requests library to download voices JSON file"
                )
            logging.info(f"Downloading voices JSON file from {self.VOICES_URL}...")
            response = requests.get(self.VOICES_URL)
            response.raise_for_status()
            logging.info(f"Response status code: {response.status_code}")

            # Check if response is not empty
            if not response.content.strip():
                raise ValueError("Downloaded JSON is empty")

            # Write the response to the file
            cache_file_path = os.path.join(self._model_dir, self.CACHE_FILE)
            with open(cache_file_path, "w") as f:
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
            with open(cache_file_path, "r") as f:
                content = f.read()
                if not content.strip():  # Check if file is not empty
                    raise ValueError("Cache file is empty")
                return json.loads(content)
        except Exception as e:
            logging.info(f"Failed to load voices JSON file: {e}")
            raise

    def _download_file(self, url, destination):
        try:
            import requests
        except ImportError:
            raise ImportError("Please install requests library to download files")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, "wb") as f:
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
        voice = next((v for v in self.voices_cache if v["Iso Code"] == iso_code), None)
        if not voice:
            raise ValueError(
                f"Voice with ISO code {iso_code} not found in the voices cache"
            )

        model_dir = os.path.join(self._model_dir, iso_code)

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        model_path = os.path.join(model_dir, "model.onnx")
        tokens_path = os.path.join(model_dir, "tokens.txt")

        if not self._check_files_exist(model_path, tokens_path):
            logging.info(
                f"Downloading model and tokens for {iso_code} because we cant find it"
            )
            model_path, tokens_path = self._download_model_and_tokens(
                iso_code, model_dir
            )
            logging.info(f"Model and tokens downloaded to {model_dir}")
        else:
            logging.info(f"Model and tokens already exist for {iso_code}")

        return model_path, tokens_path

    def _init_onnx(self):
        if not self.tts:
            import sherpa_onnx as sherpa_onnx

            # Create the VITS model configuration
            vits_model_config = sherpa_onnx.OfflineTtsVitsModelConfig(
                model=self.default_model_path,  # Path to the ONNX model
                lexicon="",  # Empty string for lexicon if not used
                tokens=self.default_tokens_path,  # Path to the tokens file
                data_dir="",  # Empty string for data directory if not used
                dict_dir="",  # Empty string for dictionary directory if not used
            )

            # Wrap it inside an OfflineTtsModelConfig with additional parameters
            model_config = sherpa_onnx.OfflineTtsModelConfig(
                vits=vits_model_config,
                provider="cpu",  # Specify the provider, e.g., "cpu", "cuda", etc.
                debug=False,  # Set to True if you need debug information
                num_threads=1,  # Number of threads for computation
            )

            # Create the TTS configuration using OfflineTtsModelConfig
            tts_config = sherpa_onnx.OfflineTtsConfig(
                model=model_config,
                rule_fsts="",  # Set if using rule FSTs, else empty string
                max_num_sentences=1,  # Control how many sentences are processed at a time
            )

            self.tts = sherpa_onnx.OfflineTts(tts_config)
            self.sample_rate = self.tts.sample_rate

    def generate_stream(self, text: str, sid: int = 0, speed: float = 1.0):
        """Generate audio progressively and yield each chunk."""
        self._init_onnx()  # Ensure the ONNX model is loaded
        self.audio_queue = (
            queue.Queue()
        )  # Reset the queue for the new streaming session
        logging.info(f"Starting streaming synthesis for text: {text}")

        # Start generating audio and filling the queue
        threading.Thread(
            target=self._stream_audio_to_queue, args=(text, sid, speed)
        ).start()

        # Yield audio chunks as they are produced
        while True:
            logging.info("While true, process the samples")
            samples = self.audio_queue.get()
            logging.info(f"SAMPLE {samples}")
            if samples is None:  # End of stream signal
                break
            
            yield samples

    def _stream_audio_to_queue(self, text: str, sid: int = 0, speed: float = 1.0):
        """Internal method to generate audio and place chunks in the queue."""
        self.tts.generate(
            text, sid=sid, speed=speed, callback=self.generated_audio_callback
        )
        self.audio_queue.put(None)  # Signal the end of audio generation

    def generated_audio_callback(self, samples: np.ndarray, progress: float):
        """Callback function to handle audio generation."""
        self.audio_queue.put(samples)  # Place generated samples into the queue
        logging.info(f"Queue in generate_stream: {self.audio_queue.qsize()}")
        return 1  # Continue generating

    def synth_streaming(self, text: str, sid: int = 0, speed: float = 1.0):
        """Generate audio in a streaming fashion using callbacks."""
        self._init_onnx()
        self.audio_queue = queue.Queue()  # Reset the queue for new streaming session
        logging.info(f"Starting streaming synthesis for text: {text}")
        self.tts.generate(
            text, sid=sid, speed=speed, callback=self.generated_audio_callback
        )
        self.audio_queue.put(None)  # Signal the end of generation

    def synth(self, text: str, sid: int = 0, speed: float = 1.0) -> Tuple[bytes, int]:
        """Generate the full audio without streaming."""
        self._init_onnx()
        audio = self.tts.generate(text, sid=sid, speed=speed)
        if len(audio.samples) == 0:
            raise ValueError("Error in generating audio")
        audio_bytes = self._convert_samples_to_bytes(audio.samples)
        return audio_bytes, self.sample_rate

    def get_voices(self) -> List[Dict[str, str]]:
        return [
            {
                "id": voice["Iso Code"],
                "name": voice["Language Name"],
                "gender": "N",
                "language_codes": [voice["Iso Code"]],
            }
            for voice in self.voices_cache
        ]

    def set_voice(self, iso_code: str):
        model_path, tokens_path = self.check_and_download_model(iso_code)
        self.default_model_path = model_path
        self.default_tokens_path = tokens_path

        # Initialize the TTS model with the new voice settings
        self._init_onnx()

        # Ensure the sample rate is set after initializing the TTS engine
        if self.tts:
            self.sample_rate = self.tts.sample_rate
            logging.info(f"Sample rate set to {self.sample_rate}")
        else:
            raise RuntimeError(
                "Failed to initialize TTS engine with the specified voice."
            )

    def _convert_samples_to_bytes(self, samples: np.ndarray) -> bytes:
        samples = np.array(samples)
        return (samples * 32767).astype(np.int16).tobytes()
