from __future__ import annotations

import base64
import json
import logging
import subprocess
from importlib import resources
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Callable

from tts_wrapper.engines.avsynth.ssml import AVSynthSSML
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator


class AVSynthClient(AbstractTTS):
    """Client for macOS AVSpeechSynthesizer."""

    def __init__(self) -> None:
        """Initialize the AVSynth client."""
        super().__init__()
        self._check_swift_bridge()
        self.bridge_path = self._get_bridge_path()
        if not self.bridge_path.exists():
            self._build_bridge()
        self.ssml = AVSynthSSML()
        self.audio_rate = 16000  # Default sample rate for AVSynth

        # Set default voice
        self.voice_id = "com.apple.speech.synthesis.voice.Alex"  # Default to Alex voice

    def _get_bridge_path(self) -> Path:
        """Get the path to the Swift bridge executable."""
        # First try the package resources
        try:
            with resources.path(
                "tts_wrapper.engines.avsynth", "SpeechBridge"
            ) as bridge_path:
                return bridge_path
        except Exception:
            # Fall back to local build directory
            return Path(__file__).parent / ".build/debug/SpeechBridge"

    def _check_swift_bridge(self) -> None:
        """Check if Swift is available and we're on macOS."""
        import platform

        if platform.system() != "Darwin":
            msg = "AVSynth is only supported on macOS"
            raise RuntimeError(msg)

        try:
            subprocess.run(["swift", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            msg = "Swift is not installed. AVSynth requires macOS with Swift installed."
            raise RuntimeError(msg)

    def _build_bridge(self) -> None:
        """Build the Swift bridge package."""
        try:
            subprocess.run(
                ["swift", "build"],
                cwd=Path(__file__).parent,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            logging.error("Failed to build Swift bridge: %s", e.stderr)
            raise

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in AVSynth)
        """
        self.voice_id = voice_id

    def _get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from AVSpeechSynthesizer.

        Returns:
            List of voice dictionaries with raw language information
        """
        try:
            result = subprocess.run(
                [str(self.bridge_path), "list-voices"],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error("Failed to get voices: %s", e.stderr)
            return []
        except json.JSONDecodeError as e:
            logging.error("Failed to parse voices JSON: %s", e)
            return []

    def _convert_property_value(self, prop: str, value: Any) -> float:
        """Convert property values to the format expected by AVSpeechSynthesizer."""
        if value is None:
            return 0.5 if prop == "rate" else 1.0  # Default values

        if isinstance(value, str):
            value = value.lower()
            if prop == "rate":
                rate_map = {
                    "x-slow": 0.1,  # Very slow
                    "slow": 0.25,  # Slow
                    "medium": 0.4,  # Normal speed (slightly slower than default)
                    "fast": 0.5,  # Default AVSpeech rate
                    "x-fast": 0.6,  # Fast but not too fast
                }
                if value in rate_map:
                    return rate_map[value]
                try:
                    # Convert percentage to rate value (50 = normal speed)
                    # Scale to a reasonable range (0.1 to 0.6)
                    percentage = float(value)
                    return 0.1 + (percentage / 100.0) * 0.5
                except ValueError:
                    return 0.4  # Default to medium rate
            elif prop == "volume":
                try:
                    # Convert string value to float, keeping it between 0.0 and 1.0
                    vol = float(value)
                    if vol > 1.0:  # If value is given as percentage
                        vol = vol / 100.0
                    return min(max(vol, 0.0), 1.0)
                except ValueError:
                    return 1.0  # Default to full volume
            elif prop == "pitch":
                pitch_map = {
                    "x-low": 0.5,
                    "low": 0.75,
                    "medium": 1.0,
                    "high": 1.25,
                    "x-high": 1.5,
                }
                if value in pitch_map:
                    return pitch_map[value]
                try:
                    return float(value)
                except ValueError:
                    return 1.0  # Default to medium pitch
        return float(value)

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        # Create options dictionary
        options = {}

        # Use provided voice_id or the one set with set_voice
        if voice_id:
            options["voice"] = voice_id
        elif hasattr(self, "voice_id") and self.voice_id:
            options["voice"] = self.voice_id

        # Get audio data with word timings
        audio_bytes, _ = self.synth_raw(str(text), options)
        return audio_bytes

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

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

    def synth_raw(self, text: str, options: dict) -> tuple[bytes, list[dict]]:
        """Synthesize text to speech using AVSpeechSynthesizer."""
        try:
            cmd = [str(self.bridge_path), "synth", text]

            # Check if text contains SSML markup
            text = text.strip()
            is_ssml = text.startswith("<speak>") and text.endswith("</speak>")
            if is_ssml:
                logging.debug("Detected SSML text: %s", text)
                cmd.extend(["--is-ssml", "true"])
            else:
                logging.debug("Using plain text with options: %s", options)

            # Only add these options for non-SSML text
            if not is_ssml:
                # Convert and add options if provided
                if "voice" in options:
                    logging.debug("Setting voice: %s", options["voice"])
                    cmd.extend(["--voice", options["voice"]])

                # Handle rate, volume, and pitch with shorter lines
                for prop in ["rate", "volume", "pitch"]:
                    if prop in options:
                        val = str(self._convert_property_value(prop, options[prop]))
                        logging.debug("Setting %s: %s", prop, val)
                        cmd.extend([f"--{prop}", val])

            logging.debug("Running command: %s", " ".join(cmd))

            # Run with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,  # Increased to 30 second timeout to match Swift
                )
            except subprocess.TimeoutExpired:
                logging.error("Speech synthesis timed out")
                msg = "Speech synthesis timed out after 30 seconds"
                raise RuntimeError(msg)

            response = json.loads(result.stdout)

            # Convert audio data from base64 if needed
            audio_data = response["audio_data"]
            if isinstance(audio_data, str):
                audio_data = base64.b64decode(audio_data)
            elif isinstance(audio_data, list):
                audio_data = bytes(audio_data)

            return audio_data, response["word_timings"]

        except subprocess.CalledProcessError as e:
            logging.error("Speech synthesis failed: %s", e.stderr)
            raise
        except json.JSONDecodeError as e:
            logging.error("Failed to parse synthesis response: %s", e)
            raise

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable[[], None]]] = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Trigger onStart callbacks
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Create options dictionary
        options = {}

        # Use provided voice_id or the one set with set_voice
        if voice_id:
            options["voice"] = voice_id
        elif hasattr(self, "voice_id") and self.voice_id:
            options["voice"] = self.voice_id

        # Synthesize with word timings
        try:
            audio_bytes, word_timings = self.synth_raw(str(text), options)

            # Call the callback for each word timing if provided
            if callback is not None and word_timings:
                for timing in word_timings:
                    if "start" in timing and "end" in timing and "word" in timing:
                        # Convert start and end times to float if they're integers
                        start_time = float(timing["start"])
                        end_time = float(timing["end"])
                        callback(timing["word"], start_time, end_time)
        except Exception:
            # Fallback to regular synthesis without timings
            self.synth_to_bytes(text, voice_id)

            # Estimate word timings based on text length
            if callback is not None:
                words = str(text).split()
                total_duration = 2.0  # Estimate 2 seconds for the audio
                time_per_word = total_duration / len(words) if words else 0

                current_time = 0.0
                for word in words:
                    end_time = current_time + time_per_word
                    callback(word, current_time, end_time)
                    current_time = end_time

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()

    def synth_streaming(
        self, text: str, options: dict[str, Any] | None = None
    ) -> tuple[Generator[bytes, None, None], list[dict[str, Any]]]:
        """Stream synthesized speech and word timings."""
        if options is None:
            options = {}

        # Build command
        cmd = [str(self.bridge_path), "stream", text]
        for key, value in options.items():
            cmd.extend([f"--{key}", str(value)])

        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        if process.stdout is None:
            msg = "Failed to open subprocess stdout"
            raise RuntimeError(msg)

        stdout: IO[bytes] = process.stdout

        # Read format info first
        format_info = ""
        while True:
            line = stdout.readline()
            if not line:
                msg = "Unexpected end of stream"
                raise RuntimeError(msg)
            line_str = line.decode("utf-8").strip()
            if line_str == "---AUDIO_START---":
                break
            format_info += line_str

        try:
            format_data = json.loads(format_info)
            logging.debug("Audio format: %s", format_data)
            word_timings = format_data.get("word_timings", [])
        except json.JSONDecodeError:
            logging.error("Failed to parse format info: %s", format_info)
            format_data = {}
            word_timings = []

        def stream_generator():
            while True:
                # Read a chunk of data
                chunk = stdout.read(4096)
                if not chunk:
                    break
                yield chunk

        return stream_generator(), word_timings
