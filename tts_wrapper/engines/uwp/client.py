import os
import clr
from typing import List

clr.AddReference('Windows')
from System import Array
from Windows.Foundation.Metadata import ApiInformation
from Windows.Media.SpeechSynthesis import SpeechSynthesizer

class UWPClient:
    def __init__(self) -> None:
        if not self.is_api_contract_present():
            raise RuntimeError("Required UWP API contract is not present.")
        self._synthesizer = SpeechSynthesizer()

    def is_api_contract_present(self) -> bool:
        """Check if the UniversalApiContract is present."""
        return ApiInformation.IsApiContractPresent("Windows.Foundation.UniversalApiContract", 1)
        
    def get_voices(self) -> List[str]:
        """Returns a list of available voices."""
        voices = self._synthesizer.AllVoices
        return [voice.DisplayName for voice in voices]

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