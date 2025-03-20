"""SherpaOnnxClient class for TTS."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
from pathlib import Path
from typing import Any

import numpy as np
import requests


class SherpaOnnxClient:
    """Client for Sherpa-ONNX TTS engine. Client class."""

    MODELS_FILE = "merged_models.json"

    def __init__(
        self,
        model_path: str | None = None,
        tokens_path: str | None = None,
        model_id: str | None = None,
        no_default_download: bool = False,
    ) -> None:
        """Initialize the Sherpa-ONNX client.

        Args:
            model_path: Path to model file or directory
            tokens_path: Path to tokens file
            model_id: Voice model ID
            no_default_download: If True, skip automatic download of default model
        """
        # Initialize instance variables
        self._model_path = model_path
        self._tokens_path = tokens_path
        self._model_id = model_id
        self._base_dir = Path(model_path) if model_path else Path.cwd()

        # Initialize paths
        self.default_model_path = ""
        self.default_tokens_path = ""
        self.default_lexicon_path = ""
        self.default_dict_dir_path = ""

        # Initialize ONNX components
        self.tts = None
        self.sample_rate = 16000  # Default sample rate
        self.audio_queue: queue.Queue = queue.Queue()

        # Load model configuration
        self.json_models = self._load_models_and_voices()

        # Only set up voice if we have a model_id or auto-download is enabled
        if self._model_id or not no_default_download:
            self._model_id = (
                self._model_id or "mms_eng"
            )  # Default to English if not specified
            self.set_voice()
        else:
            logging.info("Skipping automatic model download (no_default_download=True)")

    def _download_file(self, url: str, destination: Path) -> None:
        """Download a file from a URL to a destination path."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        destination.write_bytes(response.content)

    def _check_files_exist(
        self, model_path: str, tokens_path: str, model_id: str
    ) -> bool:
        """Check if model and token files exist.

        Args:
            model_path: Path to model file
            tokens_path: Path to tokens file
            model_id: Voice model ID

        Returns:
            True if both files exist
        """
        # Convert paths to Path objects
        model_file = Path(model_path)
        tokens_file = Path(tokens_path)

        # Check that both files exist and are not empty
        if not model_file.exists() or not tokens_file.exists():
            return False

        return not (model_file.stat().st_size == 0 or tokens_file.stat().st_size == 0)

    def get_dict_dir(self, destination_dir: Path) -> str:
        """Get dict_dir from extracted model."""
        # Walk through directory tree
        for root, _dirs, files in os.walk(str(destination_dir)):
            if any(f.endswith(".txt") for f in files):
                return str(Path(root))
        return ""

    def _download_model_and_tokens(
        self, destination_dir: Path, model_id: str | None
    ) -> tuple[Path, Path, str, str]:
        """Download model and token files to voice-specific directory.

        Args:
            destination_dir: Base directory for model files
            model_id: Voice model ID

        Returns:
            Tuple of (model_path, tokens_path, lexicon_path, dict_dir)
        """
        lexicon_path = ""
        dict_dir = ""

        # Handle None model_id
        safe_model_id = model_id or "default"

        # Get model URL from JSON config
        models = self._load_models_and_voices()
        if safe_model_id not in models:
            msg = f"Model ID {safe_model_id} not found in configuration"
            raise ValueError(msg)

        base_url = models[safe_model_id]["url"]
        model_url = f"{base_url}/model.onnx?download=true"
        tokens_url = f"{base_url}/tokens.txt"

        # Set paths in voice directory
        model_path = destination_dir / "model.onnx"
        tokens_path = destination_dir / "tokens.txt"

        # Download model file
        logging.info("Downloading model from %s", base_url)
        self._download_file(model_url, model_path)
        logging.info("Model downloaded to %s", model_path)

        # Download tokens file
        logging.info("Downloading tokens from %s", tokens_url)
        self._download_file(tokens_url, tokens_path)
        logging.info("Tokens downloaded to %s", tokens_path)

        # Set additional paths
        lexicon_path = str(destination_dir / "lexicon.txt")
        dict_dir = self.get_dict_dir(destination_dir)

        return model_path, tokens_path, lexicon_path, dict_dir

    def check_and_download_model(self, model_id: str) -> tuple[str, str, str, str]:
        """Check if model exists and download if not.

        Args:
            model_id: Voice model ID

        Returns:
            Tuple of (model_path, tokens_path, lexicon_path, dict_dir)
        """
        # Create voice-specific directory
        base_dir = Path(self._model_path or "")
        voice_dir = base_dir / model_id
        voice_dir.mkdir(exist_ok=True)

        # Expected paths for this voice
        model_path = str(voice_dir / "model.onnx")
        tokens_path = str(voice_dir / "tokens.txt")

        # Check if files exist in voice directory
        if not self._check_files_exist(model_path, tokens_path, model_id):
            logging.info(
                f"Downloading model and tokens languages for {model_id} because we can't find it"
            )

            # Download to voice-specific directory
            _, _, lexicon_path, dict_dir = self._download_model_and_tokens(
                voice_dir, model_id
            )

            # Verify files were downloaded correctly
            if not self._check_files_exist(model_path, tokens_path, model_id):
                msg = f"Failed to download model files for {model_id}"
                raise RuntimeError(msg)
        else:
            lexicon_path = str(voice_dir / "lexicon.txt")
            dict_dir = self.get_dict_dir(voice_dir)

        return model_path, tokens_path, lexicon_path, dict_dir

    def _init_onnx(self) -> None:
        """Initialize the ONNX runtime with current configuration."""
        try:
            import sherpa_onnx
        except ImportError as e:
            msg = "Please install sherpa-onnx library to use the SherpaOnnxClient"
            raise ImportError(msg) from e

        if not self.default_model_path or not self.default_tokens_path:
            msg = "Model and tokens paths must be set before initializing ONNX"
            raise ValueError(msg)

        # Create the VITS model configuration
        logging.debug("default dict dir %s", self.default_dict_dir_path)

        vits_model_config = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=self.default_model_path,
            lexicon=self.default_lexicon_path,
            tokens=self.default_tokens_path,
            data_dir="",
            dict_dir=self.default_dict_dir_path,
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
            target=self._stream_audio_to_queue,
            args=(text, sid, speed),
        ).start()

        # Yield audio chunks as they are produced
        while True:
            logging.info("While true, process the samples")
            samples = self.audio_queue.get()
            if samples is None:  # End of stream signal
                break

            yield samples

    def _stream_audio_to_queue(
        self, text: str, sid: int = 0, speed: float = 1.0
    ) -> None:
        """Generate audio and place chunks in the queue."""
        self.tts.generate(
            text,
            sid=sid,
            speed=speed,
            callback=self.generated_audio_callback,
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
            text,
            sid=sid,
            speed=speed,
            callback=self.generated_audio_callback,
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
        if not self._model_id:
            msg = "No model ID specified for voice setup"
            raise ValueError(msg)

        model_path, tokens_path, lexicon_path, dict_dir = self.check_and_download_model(
            self._model_id
        )
        self.default_model_path = model_path
        self.default_tokens_path = tokens_path

        # if mms language model set lexicon path and dict dir path to empty string
        if self._model_id.startswith("mms_"):
            self.default_lexicon_path = ""
            self.default_dict_dir_path = ""
        else:
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
            raise RuntimeError(msg)

    def _convert_samples_to_bytes(self, samples: np.ndarray) -> bytes:
        samples = np.array(samples)
        return (samples * 32767).astype(np.int16).tobytes()

    def _load_models_and_voices(self) -> dict[str, Any]:
        root_dir = Path(__file__).parent
        config_path = root_dir / "merged_models.json"

        with config_path.open() as file:
            models_json = json.load(file)
        file.close()

        return models_json
