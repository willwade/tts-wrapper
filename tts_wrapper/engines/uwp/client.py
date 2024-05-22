from typing import List, Optional, Tuple
import os

try:
    import clr
except ImportError:
    clr = None  # type: ignore

try:
    from System import Array, Byte
    from Windows.Foundation.Metadata import ApiInformation
    from Windows.Media.SpeechSynthesis import SpeechSynthesizer
    import Windows.Storage.Streams
except ImportError:
    ApiInformation = None
    SpeechSynthesizer = None

from ...exceptions import ModuleNotInstalled

class UWPClient:
    def __init__(self) -> None:
        self._check_modules()
        if not self._is_api_contract_present():
            raise RuntimeError("Required UWP API contract is not present.")
        self._synthesizer = SpeechSynthesizer()

    def _check_modules(self) -> None:
        """Check if the required modules are installed."""
        if clr is None:
            raise ModuleNotInstalled("pythonnet")
        if ApiInformation is None or SpeechSynthesizer is None:
            raise ModuleNotInstalled("Windows Runtime APIs")

    def _is_api_contract_present(self) -> bool:
        """Check if the UniversalApiContract is present."""
        return ApiInformation.IsApiContractPresent("Windows.Foundation.UniversalApiContract", 1)
    
    
    def get_voices(self) -> List[Dict[str, Any]]:
        """Returns a list of available voices with standardized keys."""
        voices = self._synthesizer.AllVoices
        standardized_voices = []
        for voice in voices:
            standardized_voice = {
                'id': voice.Id,
                'language_codes': [voice.Language],
                'name': voice.DisplayName,
                'gender': voice.Gender.ToString()
            }
            standardized_voices.append(standardized_voice)
        return standardized_voices

    def synth(self, ssml: str) -> bytes:
        stream = self._synthesizer.SynthesizeSsmlToStreamAsync(ssml).GetResults()
        
        # Read the stream into a byte buffer
        input_stream = stream.GetInputStreamAt(0)
        data_reader = Windows.Storage.Streams.DataReader(input_stream)
        buffer_size = stream.Size
        data_reader.LoadAsync(buffer_size).GetResults()
        buffer = data_reader.ReadBuffer(buffer_size)
        
        # Convert to bytes
        byte_array = Array.CreateInstance(Byte, buffer.Length)
        Windows.Storage.Streams.DataReader.FromBuffer(buffer).ReadBytes(byte_array)

        # Convert to Python bytes
        bytes_data = bytes(byte_array)
        return bytes_data