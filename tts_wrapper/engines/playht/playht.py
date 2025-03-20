import logging
from typing import Any, Optional

from tts_wrapper.engines.utils import estimate_word_timings
from tts_wrapper.tts import AbstractTTS

from .client import PlayHTClient
from .ssml import PlayHTSSML


class PlayHTTTS(AbstractTTS):
    """High-level TTS interface for Play.HT.

    Inherits from AbstractTTS which provides:
        - pause()
        - resume()
        - stop()
        - speak()
        - speak_streamed()
    """

    def __init__(
        self,
        client: PlayHTClient,
        voice: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> None:
        """Initialize the Play.HT TTS interface."""
        super().__init__()
        self._client = client
        self._voice = voice
        self.audio_rate = 44100  # Standard audio rate
        self._ssml = PlayHTSSML()
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        self.chunk_size = 1024

    def synth_to_bytes(self, text: Any, voice_id: Optional[str] = None) -> bytes:
        """Convert text to speech and return raw PCM data."""
        text = str(text)
        options = {}

        # Strip SSML tags if present - PlayHTSSML will return just the text content
        if text.startswith("<speak>") and text.endswith("</speak>"):
            text = str(text)  # PlayHTSSML.__str__ strips SSML tags

        # Add voice if provided as parameter or set in the instance
        voice_to_use = voice_id or self._voice
        if voice_to_use:
            options["voice"] = voice_to_use

        # Add any set properties
        for prop in ["speed", "quality", "voice_engine"]:
            value = self.get_property(prop)
            if value is not None:
                options[prop] = str(value)

        # Estimate word timings since Play.HT doesn't provide them
        timings = estimate_word_timings(text)
        self.set_timings(timings)  # type: ignore

        # Get WAV data from API
        wav_data = self._client.synth(text, options)

        # Always strip WAV header if present to return clean PCM data
        if wav_data[:4] == b"RIFF":
            return self._strip_wav_header(wav_data)
        return wav_data

    def speak_streamed(
        self,
        text: str,
        save_to_file_path: Optional[str] = None,
        audio_format: Optional[str] = "wav",
    ) -> None:
        """Synthesize text and stream it for playback.

        Optionally save the audio to a file after playback completes.
        """
        try:
            # Get clean PCM data
            audio_bytes = self.synth_to_bytes(text)

            # Load the audio into the player
            self.load_audio(audio_bytes)

            # Start playback
            self.play()

            # Optionally save to file
            if save_to_file_path:
                if audio_format == "mp3":
                    # Get original MP3 data from client
                    mp3_data = self._client.synth(text, {"output_format": "mp3"})
                    with open(save_to_file_path, "wb") as f:
                        f.write(mp3_data)
                else:
                    # For WAV, we need to get the original WAV data with header
                    wav_data = self._client.synth(text, {})
                    with open(save_to_file_path, "wb") as f:
                        f.write(wav_data)

        except Exception as e:
            logging.exception("Error in speak_streamed: %s", e)
            raise

    @property
    def ssml(self) -> PlayHTSSML:
        """Returns an instance of the PlayHTSSML class for constructing SSML strings."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Retrieves a list of available voices from the Play.HT service."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Sets the voice for the TTS engine."""
        super().set_voice(voice_id, lang_id or "en-US")
        self._voice = voice_id
        if lang_id:
            self._lang = lang_id
