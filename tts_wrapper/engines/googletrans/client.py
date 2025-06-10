# client.py
from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.exceptions import UnsupportedFileFormat
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path

try:
    from gtts import gTTS
    from gtts.lang import tts_langs
except ImportError:
    gTTS = None  # type: ignore[assignment]
    tts_langs = None  # type: ignore[assignment]

try:
    import mp3
except ImportError:
    mp3 = None  # type: ignore[assignment]

FORMATS = {"mp3": "mp3", "wav": "wav"}


class GoogleTransClient(AbstractTTS):
    """Client for Google Translate TTS API."""

    def __init__(self, voice_id="en-co.uk") -> None:
        super().__init__()

        # Check if required dependencies are available
        if gTTS is None:
            msg = (
                "gTTS is required for GoogleTrans TTS. "
                "Install it with: pip install gtts"
            )
            raise ImportError(msg)
        if mp3 is None:
            msg = (
                "pymp3 is required for GoogleTrans TTS. "
                "Install it with: pip install pymp3"
            )
            raise ImportError(msg)

        self.lang, self.tld = self._parse_voice_id(voice_id)
        self.audio_rate = 22050  # Default sample rate for gTTS

    def _mp3_to_wav(self, mp3_fp: BytesIO) -> bytes:
        """Converts MP3 data to WAV using pymp3 by decoding PCM and writing WAV headers."""
        mp3_fp.seek(0)  # Reset the file pointer
        output = BytesIO()

        # Initialize the MP3 decoder
        decoder = mp3.Decoder(mp3_fp)

        # Ensure that the MP3 file has valid frames
        if not decoder.is_valid():
            msg = "Invalid MP3 file: No valid MPEG frames found."
            raise ValueError(msg)

        # Retrieve MP3 properties
        sample_rate = decoder.get_sample_rate()
        nchannels = decoder.get_channels()

        # Create and write the WAV header
        wav_header = self._create_wav_header(output, sample_rate, nchannels)
        output.write(wav_header)

        # Decode and write PCM data to WAV file
        while True:
            pcm_data = decoder.read(4096)  # Read a chunk of PCM data
            if not pcm_data:
                break  # End of file
            output.write(pcm_data)

        # Finalize the output
        output.seek(0)
        return output.read()

    def _create_wav_header(
        self,
        output: BytesIO,
        sample_rate: int,
        nchannels: int,
    ) -> bytes:
        """Creates a WAV header based on the MP3 properties (sample rate, channels, etc.)."""
        # Set WAV format constants
        num_samples = output.tell() // (
            nchannels * 2
        )  # Calculate number of samples based on current size
        wav_header = BytesIO()

        # Write WAV header
        wav_header.write(b"RIFF")
        wav_header.write(
            (36 + num_samples * nchannels * 2).to_bytes(4, "little"),
        )  # Chunk size
        wav_header.write(b"WAVE")
        wav_header.write(b"fmt ")  # Subchunk 1 ID
        wav_header.write((16).to_bytes(4, "little"))  # Subchunk 1 size
        wav_header.write((1).to_bytes(2, "little"))  # Audio format (1 for PCM)
        wav_header.write(nchannels.to_bytes(2, "little"))  # Number of channels
        wav_header.write(sample_rate.to_bytes(4, "little"))  # Sample rate
        byte_rate = sample_rate * nchannels * 2
        wav_header.write(byte_rate.to_bytes(4, "little"))  # Byte rate
        block_align = nchannels * 2
        wav_header.write(block_align.to_bytes(2, "little"))  # Block align
        wav_header.write((16).to_bytes(2, "little"))  # Bits per sample (16-bit PCM)
        wav_header.write(b"data")  # Subchunk 2 ID
        wav_header.write(
            (num_samples * nchannels * 2).to_bytes(4, "little"),
        )  # Subchunk 2 size

        return wav_header.getvalue()

    def _parse_voice_id(self, voice_id: str):
        parts = voice_id.split("-")
        lang = parts[0]
        tld = parts[1] if len(parts) > 1 else "com"
        return lang, tld

    @property
    def voice(self) -> str:
        """Returns the current voice ID (combination of lang and tld)."""
        return f"{self.lang}-{self.tld}"

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use (e.g., "en-us", "fr-fr")
            lang: Optional language code (not used in GoogleTrans)
        """
        self.lang, self.tld = self._parse_voice_id(voice_id)

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes in WAV format
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        # Synthesize to MP3 first
        tts = gTTS(str(text), lang=self.lang, tld=self.tld)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)

        # Convert to WAV for consistent output
        return self._mp3_to_wav(mp3_fp)

    def synth_to_file(
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
            output_format: Format to save as ("wav" or "mp3")
            voice_id: Optional voice ID to use for this synthesis
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        if output_format == "mp3":
            # Direct MP3 output
            tts = gTTS(str(text), lang=self.lang, tld=self.tld)
            tts.save(str(output_file))
        elif output_format == "wav":
            # Convert to WAV
            audio_bytes = self.synth_to_bytes(text, voice_id)
            from pathlib import Path
            Path(output_file).write_bytes(audio_bytes)
        else:
            msg = f"Unsupported format: {output_format}"
            raise UnsupportedFileFormat(msg, "GoogleTrans")

    # Alias for backward compatibility
    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Alias for synth_to_file for backward compatibility."""
        return self.synth_to_file(text, output_file, output_format, voice_id)

    def synth_raw(self, text: str, target_format: str = "mp3") -> bytes:
        """Synthesizes text to MP3 or WAV audio bytes (legacy method)."""
        tts = gTTS(text, lang=self.lang, tld=self.tld)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)

        if target_format == "mp3":
            return mp3_fp.getvalue()

        if target_format == "wav":
            # Convert MP3 to WAV (using pymp3 for MP3 and manual WAV writing)
            mp3_fp.seek(0)
            return self._mp3_to_wav(mp3_fp)

        msg = f"Unsupported format: {target_format}"
        raise UnsupportedFileFormat(msg, "GoogleTrans")

    def _get_voices(self) -> list[dict[str, Any]]:
        """Get available voices from the GoogleTrans TTS service.

        Returns:
            List of voice dictionaries with raw language information
        """
        # Retrieve available languages from gtts
        languages = tts_langs()
        voices = []
        accents = {
            "en": ["com.au", "co.uk", "us", "ca", "co.in", "ie", "co.za", "com.ng"],
            "fr": ["ca", "fr"],
            "zh-CN": ["any"],
            "zh-TW": ["any"],
            "pt": ["com.br", "pt"],
            "es": ["com.mx", "es", "us"],
        }

        for lang_code, lang_name in languages.items():
            if lang_code in accents:
                voices.extend([
                    {
                        "id": f"{lang_code}-{accent}",
                        "language_codes": [lang_code],
                        "name": f"{lang_name} ({accent})",
                        "gender": "Unknown",
                    }
                    for accent in accents[lang_code]
                ])
            else:
                voices.append(
                    {
                        "id": lang_code,
                        "language_codes": [lang_code],
                        "name": lang_name,
                        "gender": "Unknown",
                    },
                )

        return voices

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        # If text is SSML, extract plain text
        plain_text = text
        if hasattr(text, "__str__") and "<speak" in str(text):
            # Very basic SSML stripping - just get the text content
            import re

            plain_text = re.sub(r"<[^>]+>", "", str(text))

        # Trigger onStart callback
        if (
            hasattr(self, "callbacks")
            and "onStart" in self.callbacks
            and self.callbacks["onStart"]
        ):
            self.callbacks["onStart"]()

        # Estimate word timings based on text length
        words = str(plain_text).split()
        total_duration = len(words) * 0.3  # Rough estimate: 0.3 seconds per word

        # Call the callback for each word if provided
        if callback is not None:
            time_per_word = total_duration / len(words) if words else 0
            current_time = 0.0
            for word in words:
                end_time = current_time + time_per_word
                callback(word, current_time, end_time)
                current_time = end_time

        # Synthesize and play audio
        audio_bytes = self.synth_to_bytes(plain_text, voice_id)
        self.load_audio(audio_bytes)
        self.play()

        # Trigger onEnd callback
        if (
            hasattr(self, "callbacks")
            and "onEnd" in self.callbacks
            and self.callbacks["onEnd"]
        ):
            self.callbacks["onEnd"]()
