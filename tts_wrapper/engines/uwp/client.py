import asyncio
from typing import List, Dict, Any, Optional
from ...exceptions import ModuleNotInstalled

try:
    from winrt.windows.media.speechsynthesis import SpeechSynthesizer
    from winrt.windows.storage.streams import DataReader
except ImportError:
    winrt = None
    SpeechSynthesizer = None
    SpeechSynthesizer = None


class UWPClient:
    def __init__(self) -> None:
        print("Initializing UWPClient...")
        self._synthesizer = SpeechSynthesizer()
        voice = None  # Define the variable "voice"
        lang = None  # Define the variable "lang"
        if voice:
            self.set_voice(voice, lang)

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        selected_voice = next(
            (voice for voice in self._synthesizer.all_voices if voice.id == voice_id),
            None,
        )
        if selected_voice:
            self._synthesizer.voice = selected_voice
        if lang_id:
            self._synthesizer.options.speaking_language = lang_id

    def get_voices(self) -> List[Dict[str, Any]]:
        """Returns a list of available voices with standardized keys."""
        voices = self._synthesizer.all_voices
        standardized_voices = []
        for voice in voices:
            standardized_voice = {
                "id": voice.id,
                "language_codes": [voice.language],
                "name": voice.display_name,
                "gender": voice.gender.value,
            }
            standardized_voices.append(standardized_voice)
        return standardized_voices

    def synth(self, ssml: str) -> bytes:
        stream = asyncio.run(self._synthesizer.synthesize_ssml_to_stream_async(ssml))

        # Read the stream into a byte buffer
        input_stream = stream.get_input_stream_at(0)
        data_reader = DataReader(input_stream)
        asyncio.run(data_reader.load_async(stream.size))

        # Read the buffer in chunks
        byte_array = bytearray()
        while data_reader.unconsumed_buffer_length > 0:
            bytes_to_read = min(data_reader.unconsumed_buffer_length, 1024)
            byte_array.extend(data_reader.read_bytes(bytes_to_read))

        # Get word timings
        markers = []
        for marker in stream.markers:
            markers.append({"timing": marker.time.total_seconds, "word": marker.text})

        # Set the timings on the parent abstracted class
        self.set_timings(markers)
        return bytes(byte_array)
