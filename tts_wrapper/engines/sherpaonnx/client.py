"""SherpaOnnxClient class for TTS."""

from __future__ import annotations

import bz2
import importlib
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
    """Class for sherpaonnx client."""

    #VOICES_URL = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    #CACHE_FILE = "languages-supported.json"
    MODELS_FILE = "merged_models.json"

    def __init__(
            self,
            model_path: str | None = None,
            tokens_path: str | None = None,
            model_id: str | None = None,
        ) -> None:
            """Initiate class."""
            if importlib.util.find_spec("sherpa_onnx") is None:
                logging.exception("Please install sherpa-onnx library to use the SherpaOnnxClient")

            if importlib.util.find_spec("requests") is None:
                logging.exception("Please install requests library to use the SherpaOnnxClient")

            if importlib.util.find_spec("threading") is None:
                logging.exception("Please install threading library to use the SherpaOnnxClient")

            self.default_model_path = model_path
            self.default_tokens_path = (
                tokens_path
                if tokens_path
                else Path(model_path) / "tokens.txt" if model_path else None
            )

            self._model_dir = model_path if model_path else Path("~/mms_models").expanduser()
            self._model_id = model_id
            if model_id:
                self._model_dir = Path(self._model_dir) / model_id
            if not Path(self._model_dir).exists():
                try:
                    Path(self._model_dir).mkdir(parents=True)
                except OSError as e:
                    msg = f"Failed to create model directory {self._model_dir}: {e!s}"
                    raise RuntimeError(msg) from e

            self.tts = None
            print (f"tts: {self.tts}")
            self.json_models = self._load_models_and_voices()
            #print ("Available voices\n")
            #print(self.voices_cache)


            self.set_voice()
            self.audio_queue = queue.Queue()  # Ensure `queue` is imported

            self.sample_rate = None
            
    def _download_file(self, url:str, destination:str) -> None:
        try:
            import requests
        except ImportError:
            msg = "Please install requests library to download files"
            raise ImportError(msg)
        logging.info("Downloading model files from %s to %s", url, destination)
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        logging.debug("Response status: %s", response.status_code)
        with Path(destination).open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    
    def _check_files_exist(self, model_path: str, tokens_path: str, model_id: str) -> bool:
        if not model_id :
            logging.info("Model Id not defined, using default model\n")
            model_exists = Path(model_path).exists() and Path(model_path).stat().st_size > 0
            tokens_exists = Path(tokens_path).exists() and Path(tokens_path).stat().st_size > 0
        else:
            logging.debug("Checking model with model Id: %s in %s", model_id, model_path)
            model_file = self._find_file(model_path, "onnx")
            model_file = Path(model_path) / model_file

            token_file = self._find_file(model_path, "tokens.txt")
            token_file = Path(model_path) / token_file

            model_exists = Path(model_file).exists() and Path(model_file).stat().st_size > 0
            tokens_exists = Path(token_file).exists() and Path(token_file).stat().st_size > 0

        return model_exists and tokens_exists

    def _find_file (self, destination_dir: str, extension: str) -> str:
        for root, _dirs, files in os.walk(destination_dir):
            for file in files:
                if file.endswith(extension):
                    file_path = Path(root) / file
                    # Get file size
                    file_size = file_path.stat().st_size
                    if file_size > 1024*1024 and "onnx" in file:
                        return str(file_path)
                    if "tokens.txt" in file:
                        return str(file_path)
                    if file_size > 1024*1024 and "lexicon.txt" in file:
                        return str(file_path)
        return ""


    def _download_model_and_tokens(self, destination_dir: Path, model_id: str | None) -> tuple[Path, Path, str, str]:
        lexicon_path = ""
        dict_dir = ""
        model_url = self.json_models[model_id]["url"]
        print (f"MODEL URL: {model_url}")
        if not model_id.startswith("mms_"):
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
            # Default URL if model is not defined or iso code is not found
            print (f"MODEL URL2: {model_url}")
            if not model_url:
                model_onnx_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/eng/model.onnx?download=true"
                tokens_url = f"https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/resolve/main/eng/tokens.txt"
            else:
                print ("voice model id found")
                print (f"MODEL URL3: {model_url}")
                model_onnx_url = f"{model_url}/model.onnx?download=true"
                tokens_url = f"{model_url}/tokens.txt"
            
            print (f"model url: {model_onnx_url}")
            print(f"token url: {tokens_url}")
            
            model_path = Path(destination_dir) / "model.onnx"
            tokens_path = Path(destination_dir) / "tokens.txt"

            print (f"model path: {model_path}")
            print(f"tokens path: {tokens_path}")

            logging.info("Downloading model from %s", model_url)
            self._download_file(model_onnx_url, model_path)
            logging.info("Model downloaded to %s", model_path)

            logging.info("Downloading tokens from %s", tokens_url)
            self._download_file(tokens_url, tokens_path)
            logging.info("Tokens downloaded to %s", tokens_path)

        return model_path, tokens_path, str(lexicon_path), dict_dir

    def get_dict_dir(self, destination_dir: str) -> str:
        """Get dict_dir from extracted model."""
        # Walk through directory tree
        for root, _dirs, files in os.walk(destination_dir):
            # Check if any file in current directory has .dict extension
            if any("dict" in file.lower() for file in files):
                return root

        # Return None if no matching directory is found
        return ""

    def check_and_download_model(self, model_id: str) -> tuple[str, str, str, str]:
        """Check if model and tokens exist, and download if not.

        Parameters
        ----------
        model_id : str
            The model ID to download.

        """
        lexicon_path = ""
        dict_dir = ""

        if model_id.startswith("mms_"):
            model_dir = Path(self._model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir / "model.onnx"
            tokens_path = model_dir / "tokens.txt"
        else:
            model_dir = Path(self._model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            model_path = model_dir
            tokens_path = model_dir


        if not self._check_files_exist(model_path, tokens_path, model_id):
            logging.info(
                "Downloading model and tokens languages for %s because we can't find it", model_id,
            )
            model_path, tokens_path, lexicon_path, dict_dir = self._download_model_and_tokens(
                model_dir, model_id,
            )
            logging.info("Model and tokens downloaded to %s", model_dir)

        else:
            lexicon_path = self._find_file(model_dir, "lexicon.txt")
            lexicon_path_obj = Path(model_dir) / lexicon_path
            lexicon_path = str(lexicon_path_obj)

            dict_dir = self.get_dict_dir(model_dir)
            model_path = self._find_file(model_dir, "onnx")
            tokens_path = self._find_file(model_dir, "tokens.txt")
            logging.info("Model and tokens already exist for %s", model_id)

        return str(model_path), str(tokens_path), lexicon_path, dict_dir

    def _init_onnx(self) -> None:
        if not self.tts:
            import sherpa_onnx

            # Create the VITS model configuration
            logging.debug("default dict dir %s", self.default_dict_dir_path)

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
        """Generate audio using callback function."""
        self.audio_queue.put(samples)  # Place generated samples into the queue
        logging.info("Queue in generate_stream: %d", self.audio_queue.qsize())
        return 1  # Continue generating

    def synth_streaming(self, text: str, sid: int = 0, speed: float = 1.0) -> None:
        """Generate audio in a streaming fashion using callbacks."""
        self._init_onnx()
        self.audio_queue = queue.Queue()  # Reset the queue for new streaming session
        logging.info("Starting streaming synthesis for text: %s", text)
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
        """Get available voices."""
        return [
            {
                "id": voice["id"],
                "name": voice["language"][0]["Language Name"],
                "gender": "N",
                "language_codes": [voice["language"][0]["Iso Code"]],
            }
            for key, voice in self.json_models.items()
            if voice["id"].startswith("mms_")                
        ]

    def set_voice(self) -> None:
        """Set voice using model data."""
        if (not self._model_id):
            self._model_id = "mms_eng"
        model_path, tokens_path, lexicon_path, dict_dir = self.check_and_download_model(self._model_id)
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


    def _load_models_and_voices(self) -> (dict[str, Any]):
        root_dir = Path(__file__).parent
        config_path = root_dir / 'merged_models.json'
        
        with config_path.open() as file:
            models_json = json.load(file)
        file.close()
        
        return models_json
