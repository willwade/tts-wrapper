import logging
import subprocess
import json
import base64
from typing import Any, Tuple, List, Generator
from pathlib import Path
import time


class AVSynthClient:
    """Client for macOS AVSpeechSynthesizer."""

    def __init__(self) -> None:
        """Initialize the AVSynth client."""
        self._check_swift_bridge()
        self.bridge_path = Path(__file__).parent / ".build/debug/SpeechBridge"
        if not self.bridge_path.exists():
            # Try to build if not exists
            self._build_bridge()

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
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            logging.error("Failed to build Swift bridge: %s", e.stderr)
            raise

    def get_voices(self) -> List[dict[str, Any]]:
        """Get available voices from AVSpeechSynthesizer."""
        try:
            result = subprocess.run(
                [str(self.bridge_path), "list-voices"],
                capture_output=True,
                text=True,
                check=True
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
                    "x-slow": 0.1,
                    "slow": 0.3,
                    "medium": 0.5,
                    "fast": 0.7,
                    "x-fast": 0.9
                }
                if value in rate_map:
                    return rate_map[value]
                try:
                    return float(value) / 100
                except ValueError:
                    return 0.5  # Default to medium rate
            elif prop == "volume":
                try:
                    return float(value) / 100
                except ValueError:
                    return 1.0  # Default to full volume
            elif prop == "pitch":
                pitch_map = {
                    "x-low": 0.5,
                    "low": 0.75,
                    "medium": 1.0,
                    "high": 1.25,
                    "x-high": 1.5
                }
                if value in pitch_map:
                    return pitch_map[value]
                try:
                    return float(value)
                except ValueError:
                    return 1.0  # Default to medium pitch
        return float(value)

    def synth(self, text: str, options: dict) -> Tuple[bytes, List[dict]]:
        """Synthesize text to speech using AVSpeechSynthesizer."""
        try:
            cmd = [str(self.bridge_path), "synth", text]
            
            # Convert and add options if provided
            if "voice" in options:
                cmd.extend(["--voice", options["voice"]])
            
            # Handle rate, volume, and pitch with shorter lines
            for prop in ["rate", "volume", "pitch"]:
                if prop in options:
                    val = str(self._convert_property_value(prop, options[prop]))
                    cmd.extend([f"--{prop}", val])
            
            # Run with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30  # Increased to 30 second timeout to match Swift
                )
            except subprocess.TimeoutExpired:
                logging.error("Speech synthesis timed out")
                raise RuntimeError("Speech synthesis timed out after 30 seconds")
                
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
        self, text: str, options: dict
    ) -> Tuple[Generator[bytes, None, None], List[dict]]:
        """Stream synthesized speech using AVSpeechSynthesizer."""
        try:
            cmd = [str(self.bridge_path), "stream", text]
            
            # Add voice and other properties
            if "voice" in options:
                cmd.extend(["--voice", options["voice"]])
            
            # Handle rate, volume, and pitch with shorter lines
            for prop in ["rate", "volume", "pitch"]:
                if prop in options:
                    val = str(self._convert_property_value(prop, options[prop]))
                    cmd.extend([f"--{prop}", val])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1024
            )
            
            if process.stdout is None:
                msg = "Failed to open subprocess stdout"
                raise RuntimeError(msg)
            
            # Read header with timeout
            header = b""
            start_time = time.time()
            while b"\n\n" not in header:
                if time.time() - start_time > 5:  # 5 second timeout for header
                    process.kill()
                    msg = "Timeout waiting for header"
                    raise RuntimeError(msg)
                
                chunk = process.stdout.read(1)
                if not chunk:
                    break
                header += chunk
            
            # Parse word timings from header
            try:
                header_str = header.decode().split("\n\n")[0]
                timings = json.loads(header_str)["word_timings"]
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                process.kill()
                logging.error("Failed to parse header: %s", e)
                raise RuntimeError("Failed to parse header from Swift bridge")
            
            def generate() -> Generator[bytes, None, None]:
                try:
                    assert process.stdout is not None
                    while True:
                        chunk = process.stdout.read(1024)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    process.kill()  # Ensure process is terminated
                    process.wait(timeout=1)  # Wait for process to end
            
            return generate(), timings
            
        except subprocess.CalledProcessError as e:
            logging.error("Streaming synthesis failed: %s", e.stderr)
            raise
        except json.JSONDecodeError as e:
            logging.error("Failed to parse synthesis response: %s", e)
            raise