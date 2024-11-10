# client.py
from __future__ import annotations

import bz2
import json
import logging
import os
import tarfile
import threading
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError:
    logging.exception("Please install numpy library to use the SherpaOnnxClient")
    np = None  # type: ignore

try:
    import queue
except ImportError:
    logging.exception("Please install queue library to use the SherpaOnnxClient")
    queue = None  # type: ignore


class SherpaOnnxClient:
    VOICES_URL = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    CACHE_FILE = "languages-supported.json"

    def __init__(
        self,
        model_path: str | None = None,
        tokens_path: str | None = None,

        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> None:
        try:
            import sherpa_onnx
        except ImportError:
            logging.exception(
                "Please install sherpa-onnx library to use the SherpaOnnxClient",
            )

        try:
            import requests
        except ImportError:
            logging.exception("Please install requests library to use the SherpaOnnxClient")

        try:
            import threading
        except ImportError:
            logging.exception(
                "Please install threading library to use the SherpaOnnxClient",
            )

        self.default_model_path = model_path
        self.default_tokens_path = (
            tokens_path
            if tokens_path
            else os.path.join(model_path, "tokens.txt") if model_path else None
        )

        self.default_lexicon_path = ""
        self.default_dict_dir_path = ""

        self._model_dir = (
            model_path if model_path else os.path.expanduser("~/mms_models")
        )
        self._model_id = model_id
        if model_id:
            self._model_dir = os.path.join(self._model_dir, model_id)

        if not os.path.exists(self._model_dir):
            try:
                os.makedirs(self._model_dir, exist_ok=True)
            except Exception as e:
                msg = f"Failed to create model directory {self._model_dir}: {e!s}"
                raise RuntimeError(
                    msg,
                )
        self.voices_cache = self._load_voices_cache()
        if voice_id:
            self.set_voice(voice_id)
        self.audio_queue = queue.Queue()
        self.tts = None
        self.sample_rate = None

    def _download_voices(self) -> None:
        try:
            try:
                import requests
            except ImportError:
                msg = "Please install requests library to download voices JSON file"
                raise ImportError(
                    msg,
                )
            logging.info("Downloading voices JSON file from (%s)...", self.VOICES_URL)
            response = requests.get(self.VOICES_URL)
            response.raise_for_status()
            logging.info("Response status code: %s", response.status_code)

            # Check if response is not empty
            if not response.content.strip():
                msg = "Downloaded JSON is empty"
                raise ValueError(msg)

            # Write the response to the file
            cache_file_path = os.path.join(self._model_dir, self.CACHE_FILE)
            with open(cache_file_path, "w") as f:
                f.write(response.text)
                logging.info("Voices JSON file written to %s,", cache_file_path)
        except Exception as e:
            logging.info(f"Failed to download voices JSON file: {e}")
            raise

    def _load_voices_cache(self) -> list[dict[str, Any]]:
        cache_file_path = os.path.join(self._model_dir, self.CACHE_FILE)
        if not os.path.exists(cache_file_path):
            self._download_voices()

        try:
            logging.info("Loading voices JSON file...")
            with open(cache_file_path) as f:
                content = f.read()
                if not content.strip():  # Check if file is not empty
                    msg = "Cache file is empty"
                    raise ValueError(msg)
                return json.loads(content)
        except Exception as e:
            logging.info(f"Failed to load voices JSON file: {e}")
            raise

    def _download_file(self, url, destination) -> None:
        try:
            import requests
        except ImportError:
            msg = "Please install requests library to download files"
            raise ImportError(msg)
        logging.info(f"Downloading model files from {url} to {destination}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        logging.debug(f"Response status: {response.status_code}")
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def _check_files_exist(self, model_path, tokens_path, model_id):
        if not model_id :
            logging.info("Model Id not defined, using default model\n")
            model_exists = os.path.exists(model_path) and os.path.getsize(model_path) > 0
            tokens_exists = os.path.exists(tokens_path) and os.path.getsize(tokens_path) > 0
        else:
            logging.debug(f"Checking model with model Id: {model_id} in {model_path} \n")
            model_file = self._find_file(model_path, "onnx")
            model_file = os.path.join(model_path, model_file)

            token_file = self._find_file(model_path, "tokens.txt")
            logging.debug (f"token file: {token_file}")
            token_file = os.path.join(model_path, token_file)
            logging.debug (f"model file: {model_file}")

            model_exists = os.path.exists(model_file) and os.path.getsize(model_file) > 0
            tokens_exists = os.path.exists(token_file) and os.path.getsize(token_file) > 0
            logging.debug (f"model exist: {model_exists}")
            logging.debug (f"token exist: {tokens_exists}")
        return model_exists and tokens_exists

    def _find_file (self, destination_dir, extension):
        for root, _dirs, files in os.walk(destination_dir):
            for file in files:
                if file.endswith(extension):
                    file_path = os.path.join(root, file)
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024*1024 and "onnx" in file:
                        return file_path
                    if "tokens.txt" in file:
                        return file_path
                    if file_size > 1024*1024 and "lexicon.txt" in file:
                        return file_path
        return ""


    def _download_model_and_tokens(self, iso_code: str, destination_dir: Path, model_id: str | None) -> tuple[Path, Path, str, str]:
        lexicon_path = ""
        dict_dir = ""

        if model_id:
            json_models = self._load_models()
            model_url = json_models[model_id]["url"]
            filename = Path(model_url).name
            logging.info("Downloading model from %s", model_url)

            download_path = destination_dir / filename

            self._download_file(model_url, download_path)
            logging.info("Model downloaded to %s", destination_dir)

            logging.info("Extracting model and token to %s", destination_dir)

            with bz2.open(download_path, "rb") as bz2_file, tarfile.open(fileobj=bz2_file, mode="r:") as tar_file:
                tar_file.extractall(destination_dir)

            extracted_dir = filename.split(".tar.bz2")[0]
            destination_dir = destination_dir / extracted_dir

            logging.info("Find onnx file in extracted directory: %s", destination_dir)
            model_file = self._find_file(destination_dir, "onnx")

            model_path = destination_dir / model_file
            logging.info("model_path in download: %s", model_path)
            tokens_path = destination_dir / "tokens.txt"
            lexicon_path = destination_dir / "lexicon.txt"
            dict_dir = self.get_dict_dir(destination_dir)

            if not model_path:
                msg = f"Model for model id {model_id} not found in the downloaded file"
                raise ValueError(msg)
        else:
            # Default URL if model is not defined
            model_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/{iso_code}/model.onnx?download=true"
            tokens_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/{iso_code}/tokens.txt"

            model_path = destination_dir / "model.onnx"
            tokens_path = destination_dir / "tokens.txt"

            logging.info("Downloading model from %s", model_url)
            self._download_file(model_url, model_path)
            logging.info("Model downloaded to %s", model_path)

            logging.info("Downloading tokens from %s", tokens_url)
            self._download_file(tokens_url, tokens_path)
            logging.info("Tokens downloaded to %s", tokens_path)

        return model_path, tokens_path, str(lexicon_path), dict_dir

    def get_dict_dir(self, destination_dir: str):
        # Walk through directory tree
        for root, _dirs, files in os.walk(destination_dir):
            # Check if any file in current directory has .dict extension
            if any("dict" in file.lower() for file in files):
                return root

        # Return None if no matching directory is found
        return ""

    #def check_and_download_model(self, iso_code: str) -> Tuple[str, str]:
    def check_and_download_model(self, iso_code:str, model_id: str) -> tuple[str, str, str, str]:
        lexicon_path = ""
        dict_dir = ""
        voice = next((v for v in self.voices_cache if v["Iso Code"] == iso_code), None)
        if not voice:
            msg = f"Voice with ISO code {iso_code} not found in the voices cache"
            raise ValueError(
                msg,
            )

        if not model_id:
            model_dir = os.path.join(self._model_dir, iso_code)

            if not os.path.exists(model_dir):
                os.makedirs(model_dir)

            model_path = os.path.join(model_dir, "model.onnx")
            tokens_path = os.path.join(model_dir, "tokens.txt")
        else:
            model_dir = self._model_dir
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            model_path = model_dir
            tokens_path = model_dir

        if not self._check_files_exist(model_path, tokens_path, model_id):
            logging.info(
                f"Downloading model and tokens for {iso_code} because we can't find it",
            )
            model_path, tokens_path, lexicon_path, dict_dir = self._download_model_and_tokens(
                iso_code, model_dir, model_id,
            )
            logging.info(f"Model and tokens downloaded to {model_dir}")

        else:
            lexicon_path = self._find_file(model_dir, "lexicon.txt")
            lexicon_path = os.path.join(model_dir, lexicon_path)

            dict_dir = self.get_dict_dir(model_dir)
            model_path = self._find_file(model_dir, "onnx")
            tokens_path = self._find_file(model_dir, "tokens.txt")
            logging.info(f"Model and tokens already exist for {iso_code}")

        return model_path, tokens_path, lexicon_path, dict_dir

    def _init_onnx(self) -> None:
        if not self.tts:
            import sherpa_onnx

            # Create the VITS model configuration
            logging.debug(f"default dict dir {self.default_dict_dir_path}")

            vits_model_config = sherpa_onnx.OfflineTtsVitsModelConfig(
                model=self.default_model_path,  # Path to the ONNX model
                lexicon=self.default_lexicon_path,  # Empty string for lexicon if not used
                tokens=self.default_tokens_path,  # Path to the tokens file
                data_dir="",  # Empty string for data directory if not used
                dict_dir=self.default_dict_dir_path,  # Empty string for dictionary directory if not used
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
        logging.info("Starting streaming synthesis for text: %s", text)

        # Start generating audio and filling the queue
        threading.Thread(
            target=self._stream_audio_to_queue, args=(text, sid, speed),
        ).start()

        # Yield audio chunks as they are produced
        while True:
            logging.info("While true, process the samples")
            samples = self.audio_queue.get()
            logging.info(f"SAMPLE {samples}")
            if samples is None:  # End of stream signal
                break

            yield samples

    def _stream_audio_to_queue(self, text: str, sid: int = 0, speed: float = 1.0) -> None:
        """Generate audio and place chunks in the queue."""
        self.tts.generate(
            text, sid=sid, speed=speed, callback=self.generated_audio_callback,
        )
        self.audio_queue.put(None)  # Signal the end of audio generation

    def generated_audio_callback(self, samples: np.ndarray, progress: float) -> int:
        """Callback function to handle audio generation."""
        self.audio_queue.put(samples)  # Place generated samples into the queue
        logging.info(f"Queue in generate_stream: {self.audio_queue.qsize()}")
        return 1  # Continue generating

    def synth_streaming(self, text: str, sid: int = 0, speed: float = 1.0) -> None:
        """Generate audio in a streaming fashion using callbacks."""
        self._init_onnx()
        self.audio_queue = queue.Queue()  # Reset the queue for new streaming session
        logging.info(f"Starting streaming synthesis for text: {text}")
        self.tts.generate(
            text, sid=sid, speed=speed, callback=self.generated_audio_callback,
        )
        self.audio_queue.put(None)  # Signal the end of generation

    def synth(self, text: str, sid: int = 0, speed: float = 1.0) -> tuple[bytes, int]:
        """Generate the full audio without streaming."""
        self._init_onnx()
        audio = self.tts.generate(text, sid=sid, speed=speed)
        if len(audio.samples) == 0:
            msg = "Error in generating audio"
            raise ValueError(msg)
        audio_bytes = self._convert_samples_to_bytes(audio.samples)
        return audio_bytes, self.sample_rate

    def get_voices(self) -> list[dict[str, str]]:
        return [
            {
                "id": voice["Iso Code"],
                "name": voice["Language Name"],
                "gender": "N",
                "language_codes": [voice["Iso Code"]],
            }
            for voice in self.voices_cache
        ]

    def set_voice(self, iso_code: str) -> None:
        model_path, tokens_path, lexicon_path, dict_dir = self.check_and_download_model(iso_code, self._model_id)
        self.default_model_path = model_path
        self.default_tokens_path = tokens_path
        self.default_lexicon_path = lexicon_path
        self.default_dict_dir_path = dict_dir

        # Initialize the TTS model with the new voice settings
        self._init_onnx()

        # Ensure the sample rate is set after initializing the TTS engine
        if self.tts:
            self.sample_rate = self.tts.sample_rate
            logging.info("Sample rate set to %s", self.sample_rate)
        else:
            msg = "Failed to initialize TTS engine with the specified voice."
            raise RuntimeError(
                msg,
            )

    def _convert_samples_to_bytes(self, samples: np.ndarray) -> bytes:
        samples = np.array(samples)
        return (samples * 32767).astype(np.int16).tobytes()


    def _load_models(self) -> list[dict[str, Any]]:
        models_file_path = Path(self._model_dir) / self.MODELS_FILE
        try:
            with models_file_path.open() as file:
                return json.load(file)
        except FileNotFoundError:
            logging.exception(f"Models file {self.MODELS_FILE} not found.")
            return []
        except json.JSONDecodeError:
            logging.exception("Failed to decode JSON in models file.")
            return []
