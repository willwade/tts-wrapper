import base64
import json
import logging
import subprocess
from collections.abc import Generator
from importlib import resources
from pathlib import Path
from typing import IO, Any, Optional


class AVSynthClient:
    """Client for macOS AVSpeechSynthesizer."""

    def __init__(self) -> None:
        """Initialize the AVSynth client."""
        self._check_swift_bridge()
        self.bridge_path = self._get_bridge_path()
        if not self.bridge_path.exists():
            self._build_bridge()

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

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from AVSpeechSynthesizer."""
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

    def synth(self, text: str, options: dict) -> tuple[bytes, list[dict]]:
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

    def synth_streaming(
        self, text: str, options: Optional[dict[str, Any]] = None
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
