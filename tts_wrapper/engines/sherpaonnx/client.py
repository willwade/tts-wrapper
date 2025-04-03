"""SherpaOnnxClient class for TTS."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import requests

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator


class SherpaOnnxClient(AbstractTTS):
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
        super().__init__()

        # Initialize instance variables
        self._model_path = model_path
        self._tokens_path = tokens_path
        self._model_id = model_id

        # Use a dedicated models directory if model_path is not provided
        if model_path:
            self._base_dir = Path(model_path)
        else:
            # Create a models directory that works with PyInstaller too
            try:
                # First try to use the package directory approach
                package_dir = Path(__file__).parent
                models_dir = package_dir / "models"
            except (AttributeError, NameError):
                # If that fails (e.g., in PyInstaller), use a directory relative to the executable
                import sys

                if getattr(sys, "frozen", False):
                    # Running in a PyInstaller bundle
                    base_path = Path(sys.executable).parent
                else:
                    # Running in normal Python environment
                    base_path = Path.cwd()
                models_dir = base_path / "models"

            # Create the models directory if it doesn't exist
            models_dir.mkdir(exist_ok=True)
            self._base_dir = models_dir
            logging.info(f"Using default models directory: {models_dir}")

        # Initialize paths
        self.default_model_path = ""
        self.default_tokens_path = ""
        self.default_lexicon_path = ""
        self.default_dict_dir_path = ""

        # Initialize ONNX components
        self.tts = None
        self.sample_rate = 16000  # Default sample rate
        self.audio_rate = 16000  # Default audio rate for playback
        self.audio_queue: queue.Queue = queue.Queue()

        # Load model configuration
        self.json_models = self._load_models_and_voices()

        # Only set up voice if we have a model_id or auto-download is enabled
        if self._model_id or not no_default_download:
            self._model_id = (
                self._model_id or "mms_eng"
            )  # Default to English if not specified
            self.set_voice(voice_id=self._model_id)
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
        voice_dir = self._base_dir / model_id
        voice_dir.mkdir(exist_ok=True)
        logging.info(f"Using voice directory: {voice_dir}")

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

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Parameters
        ----------
        text : Any
            The text to synthesize, can be plain text or SSML.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.

        Returns
        -------
        bytes
            Raw PCM data with no headers for sounddevice playback.
        """
        self._init_onnx()

        # If voice_id is provided, use it
        if voice_id:
            self.set_voice(voice_id)

        # Extract sid from the current model
        sid = 0  # Default speaker ID

        # Store the text for word timing estimation
        self._last_text = str(text)

        # Generate audio
        audio = self.tts.generate(str(text), sid=sid, speed=1.0)
        if len(audio.samples) == 0:
            msg = "Error in generating audio"
            raise ValueError(msg)

        # Convert to bytes
        audio_bytes = self._convert_samples_to_bytes(audio.samples)

        # Set audio rate for playback
        self.audio_rate = self.sample_rate

        return audio_bytes

    def get_word_timings(self) -> list[tuple[float, float, str]]:
        """Get word timings for the synthesized speech.

        SherpaOnnx doesn't provide word timings, so we estimate them based on the text.

        Returns:
            List of word timing tuples (start_time, end_time, word)
        """
        # If we don't have any audio yet, return an empty list
        if not hasattr(self, "_last_text") or not self._last_text:
            return []

        # Split the text into words
        words = self._last_text.split()
        if not words:
            return []

        # Get the audio duration if available, otherwise estimate it
        try:
            duration = self.get_audio_duration()
        except (AttributeError, ValueError):
            # Fallback: estimate duration based on word count (3 words per second)
            duration = len(words) / 3.0

        # Calculate word duration
        word_duration = duration / len(words)

        # Create evenly spaced word timings
        word_timings = []
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration if i < len(words) - 1 else duration
            word_timings.append((start_time, end_time, word))

        return word_timings

    def start_playback_with_callbacks(
        self, text: str, callback: callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Callback function for word timing events
            voice_id: Optional voice ID to use for this synthesis
        """
        # Trigger onStart callback
        self._trigger_callback("onStart")

        # Set the callback if provided
        if callback is not None:
            self.on_word_callback = callback

        # Synthesize and play the audio
        self.speak_streamed(text, voice_id, trigger_callbacks=False)

        # Process word timings
        if self.timings:
            for start_time, end_time, word in self.timings:
                # Schedule word callback
                timer = threading.Timer(
                    start_time,
                    self._trigger_callback,
                    args=["onWord", word, start_time],
                )
                timer.daemon = True
                timer.start()
                self.timers.append(timer)

                # Also call the callback directly if provided
                if callback is not None:
                    callback(word, start_time, end_time)

            # Schedule onEnd callback
            if self.timings:
                last_timing = self.timings[-1]
                end_time = last_timing[1]  # End time of the last word
                timer = threading.Timer(
                    end_time, self._trigger_callback, args=["onEnd"]
                )
                timer.daemon = True
                timer.start()
                self.timers.append(timer)
        else:
            # If no timings, trigger onEnd after a short delay
            timer = threading.Timer(0.5, self._trigger_callback, args=["onEnd"])
            timer.daemon = True
            timer.start()
            self.timers.append(timer)

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None, format: str = "wav"
    ) -> Generator[bytes, None, None]:
        """Synthesizes text to an in-memory bytestream and yields audio data chunks.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis
            format: The desired audio format (e.g., 'wav', 'mp3', 'flac')

        Returns:
            A generator yielding bytes objects containing audio data
        """
        import io

        # Store the text for word timing estimation
        self._last_text = str(text)

        # Generate the full audio content
        audio_content = self.synth_to_bytes(text, voice_id)

        # Create a BytesIO object from the audio content
        audio_stream = io.BytesIO(audio_content)

        # Define chunk size (adjust as needed)
        chunk_size = 4096  # 4KB chunks

        # Yield chunks of audio data
        while True:
            chunk = audio_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesizes text to audio and saves it to a file.

        Parameters
        ----------
        text : Any
            The text to synthesize.
        output_file : str | Path
            The path to save the audio file to.
        output_format : str
            The format to save the audio file as. Default is "wav".
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        """
        import soundfile as sf

        # Convert text to audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Convert bytes to numpy array for soundfile
        import numpy as np

        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

        # Save to file
        sf.write(output_file, audio_array, self.audio_rate, format=output_format)

    def synth_raw(
        self, text: str, sid: int = 0, speed: float = 1.0
    ) -> tuple[bytes, int]:
        """Generate the full audio without streaming (legacy method)."""
        self._init_onnx()
        audio = self.tts.generate(text, sid=sid, speed=speed)
        if len(audio.samples) == 0:
            msg = "Error in generating audio"
            raise ValueError(msg)
        audio_bytes = self._convert_samples_to_bytes(audio.samples)
        return audio_bytes, self.sample_rate

    def _get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from the SherpaOnnx TTS service.

        Returns:
            List of voice dictionaries with raw language information
        """
        voices = []

        for voice in self.json_models.values():
            if voice["id"].startswith("mms_"):
                voices.append(
                    {
                        "id": voice["id"],
                        "name": voice["language"][0]["Language Name"],
                        "language_codes": [voice["language"][0]["Iso Code"]],
                        "gender": "N",
                    }
                )

        return voices

    def set_voice(
        self, voice_id: str | None = None, lang_id: str | None = None
    ) -> None:
        """
        Set voice using model data.

        Parameters
        ----------
        voice_id : str | None, optional
            The ID of the voice to use. If provided, this overrides the model_id set during initialization.
        lang_id : str | None, optional
            The language ID. Currently not used by SherpaOnnx but included for interface compatibility.
        """
        # If voice_id is provided, use it instead of the model_id set during initialization
        model_id_to_use = voice_id or self._model_id

        if not model_id_to_use:
            msg = "No model ID specified for voice setup"
            raise ValueError(msg)

        # Store the model_id for future reference
        self._model_id = model_id_to_use

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
