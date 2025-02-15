import logging
from typing import Any, Optional, List
import time

from tts_wrapper.tts import AbstractTTS, WordTiming

from .client import AVSynthClient
from .ssml import AVSynthSSML


class AVSynthTTS(AbstractTTS):
    """High-level TTS interface for AVSynth (macOS AVSpeechSynthesizer)."""

    def __init__(self, client: AVSynthClient, voice: Optional[str] = None) -> None:
        """Initialize the AVSynth TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self.audio_rate = 22050  # Lower audio rate for more natural speech
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.chunk_size = 1024
        self.timings: List[WordTiming] = []
        self._callbacks = {
            "onStart": None,
            "onEnd": None
        }
        self._stream = None
        self._audio_data = None
        # Initialize properties with default string values
        self.properties = {
            "volume": "100",
            "rate": "medium",
            "pitch": "medium"
        }
        # Initialize SSML support
        self.ssml = AVSynthSSML()

    def _is_ssml(self, text: str) -> bool:
        """Check if the text contains SSML markup."""
        text = text.strip()
        return text.startswith("<speak>") and text.endswith("</speak>")

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to speech."""
        text = str(text)
        options = {}

        # Add voice if set and text is not SSML
        if self._voice and not self._is_ssml(text):
            options["voice"] = self._voice

        # Add any set properties (only for non-SSML text)
        if not self._is_ssml(text):
            for prop in ["rate", "volume", "pitch"]:
                value = self.get_property(prop)
                if value is not None:
                    options[prop] = str(value)

        # Call the client for synthesis
        audio_data, word_timings = self._client.synth(text, options)
        timings = self._process_word_timings(word_timings)
        self.set_timings(timings)
        return audio_data

    def speak_streamed(
        self,
        text: str,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
    ) -> None:
        """Synthesize text and stream it for playback."""
        try:
            # Get synthesis options
            options = {}
            if self._voice:
                options["voice"] = self._voice
            
            # Add properties
            for prop in ["rate", "volume", "pitch"]:
                value = self.get_property(prop)
                if value is not None:
                    options[prop] = str(value)

            # Get audio stream and word timings
            audio_stream, word_timings = self._client.synth_streaming(text, options)
            timings = self._process_word_timings(word_timings)
            self.set_timings(timings)

            try:
                # Load audio into player
                audio_bytes = b"".join(list(audio_stream))
                self.load_audio(audio_bytes)
                
                # Start playback
                self.play()

                # Save to file if requested
                if save_to_file_path:
                    with open(save_to_file_path, "wb") as f:
                        f.write(audio_bytes)

            except Exception as audio_error:
                if "PortAudio" in str(audio_error):
                    logging.info("Audio device error (non-critical): %s", audio_error)
                else:
                    raise

        except Exception as e:
            logging.exception("Error in speak_streamed: %s", e)
            raise

    def stop(self) -> None:
        """Stop audio playback."""
        try:
            super().stop()
        except Exception as e:
            # Ignore common PortAudio cleanup errors
            if (
                "Stream already closed" not in str(e)
                and "Internal PortAudio error" not in str(e)
            ):
                raise

    def pause(self, duration: float | None = None) -> None:
        """
        Pause audio playback.
        
        Args:
            duration: Optional duration to pause for before resuming.
        """
        try:
            if self._stream and self._stream.is_active():
                self._stream.stop_stream()
                if duration is not None:
                    time.sleep(duration)
                    self.resume()
        except Exception as e:
            if "PortAudio" in str(e):
                logging.info("Audio device error (non-critical): %s", e)
            else:
                raise

    def resume(self) -> None:
        """Resume audio playback."""
        try:
            super().resume()
        except Exception as e:
            # Ignore common PortAudio cleanup errors
            if (
                "Stream already closed" not in str(e)
                and "Internal PortAudio error" not in str(e)
            ):
                raise

    def start_playback_with_callbacks(
        self, text: str, callback: Any = None
    ) -> None:
        """Start playback with word timing callbacks."""
        try:
            audio_bytes = self.synth_to_bytes(text)
            self.load_audio(audio_bytes)
            
            try:
                # Call onStart callback if registered
                if self._callbacks["onStart"]:
                    self._callbacks["onStart"]()
                
                # Start playback
                self.play()
                
                # Process word timings
                if callback and hasattr(self, 'timings'):
                    for timing in self.timings:
                        if len(timing) >= 3:
                            start_time, end_time, word = timing
                            callback(word, start_time, end_time)
                            time.sleep(end_time - start_time)
                
                # Call onEnd callback if registered
                if self._callbacks["onEnd"]:
                    self._callbacks["onEnd"]()
                    
            except Exception as audio_error:
                if "PortAudio" in str(audio_error):
                    logging.info("Audio device error (non-critical): %s", audio_error)
                else:
                    raise
                    
        except Exception as e:
            logging.exception("Error in start_playback_with_callbacks: %s", e)
            raise

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang: str = "en-US") -> None:
        """Set the voice for synthesis."""
        self._voice = voice_id
        self._lang = lang

    def _process_word_timings(
        self, word_timings: list[dict]
    ) -> List[WordTiming]:
        """Convert word timings into the format (start_time, end_time, word)."""
        return [
            (timing["start"], timing["end"], timing["word"])
            for timing in word_timings
        ]