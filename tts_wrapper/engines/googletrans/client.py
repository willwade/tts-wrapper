# client.py
from io import BytesIO
from typing import Any

import mp3

from tts_wrapper.exceptions import UnsupportedFileFormat

try:
    from gtts import gTTS
    from gtts.lang import tts_langs
except ImportError:
    gtts = None  # type: ignore

FORMATS = {"mp3": "mp3", "wav": "wav"}


class GoogleTransClient:
    def __init__(self, voice_id="en-co.uk") -> None:
        self.lang, self.tld = self._parse_voice_id(voice_id)

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

    def set_voice(self, voice_id: str) -> None:
        self.lang, self.tld = self._parse_voice_id(voice_id)

    def synth(self, text: str, target_format: str = "mp3") -> bytes:
        """Synthesizes text to MP3 or WAV audio bytes."""
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
        raise UnsupportedFileFormat(msg)

    def get_voices(self) -> list[dict[str, Any]]:
        # Retrieve available languages from gtts
        languages = tts_langs()
        standardized_voices = []
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
                for accent in accents[lang_code]:
                    standardized_voices.append(
                        {
                            "id": f"{lang_code}-{accent}",
                            "language_codes": [lang_code],
                            "name": f"{lang_name} ({accent})",
                            "gender": "Unknown",
                        },
                    )
            else:
                standardized_voices.append(
                    {
                        "id": lang_code,
                        "language_codes": [lang_code],
                        "name": lang_name,
                        "gender": "Unknown",
                    },
                )

        return standardized_voices
