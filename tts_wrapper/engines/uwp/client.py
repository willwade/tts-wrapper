from typing import List, Dict, Any, Optional
from ...exceptions import ModuleNotInstalled

try:
    import winrt.windows.media.speechsynthesis as sstts
    import winrt.windows.storage.streams as streams
except ImportError:
    raise ModuleNotInstalled("winrt-runtime")


class UWPClient:
    def __init__(self) -> None:
        self._check_modules()
        self._synthesizer = sstts.SpeechSynthesizer()
        voice = None  # Define the variable "voice"
        lang = None  # Define the variable "lang"
        if voice:
            self.set_voice(voice, lang)

    def _check_modules(self) -> None:
        """Check if the required modules are installed."""
        try:
            import winrt.windows.media.speechsynthesis as sstts
            import winrt.windows.storage.streams as streams
        except ImportError:
            raise ModuleNotInstalled("winrt-runtime")


    def get_voices(self) -> List[Dict[str, Any]]:
        """Returns a list of available voices with standardized keys."""
        voices = self._synthesizer.all_voices
        standardized_voices = []
        for voice in voices:
            standardized_voice = {
                'id': voice.id,
                'language_codes': [voice.language],
                'name': voice.display_name,
                'gender': voice.gender.value
            }
            standardized_voices.append(standardized_voice)
        return standardized_voices

    def synth(self, ssml: str) -> bytes:
        stream = self._synthesizer.synthesize_ssml_to_stream_async(ssml).get()
        
        # Read the stream into a byte buffer
        input_stream = stream.get_input_stream_at(0)
        data_reader = streams.DataReader(input_stream)
        buffer_size = stream.size
        data_reader.load_async(buffer_size).get()
        buffer = data_reader.read_buffer(buffer_size)
        
        # Convert to bytes
        byte_array = bytearray(buffer.length)
        data_reader.read_bytes(byte_array)
        
        # Get word timings
        markers = []
        for marker in stream.markers:
            markers.append({
                'timing': marker.time.total_seconds,
                'word': marker.text
            })

        # Set the timings on the parent abstracted class
        self.set_timings(markers)
        return bytes(byte_array)
        
    def set_voice(self, voice_id: str, lang_id: Optional[str] = None):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        selected_voice = next((voice for voice in self._synthesizer.all_voices if voice.id == voice_id), None)
        if selected_voice:
            self._synthesizer.voice = selected_voice
        if lang_id:
            self._synthesizer.options.speaking_language = lang_id
