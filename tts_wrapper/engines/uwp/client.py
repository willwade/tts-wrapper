import os
import clr
from typing import List

clr.AddReference('Windows')
from System import Array
from Windows.Media.SpeechSynthesis import SpeechSynthesizer, VoiceInformation

class UWPClient:
    def __init__(self) -> None:
        self._synthesizer = SpeechSynthesizer()

    def get_voices(self) -> List[str]:
        """Returns a list of available voices."""
        voices = self._synthesizer.AllVoices
        return [voice.DisplayName for voice in voices]

    def synth(self, text: str) -> bytes:
        stream = self._synthesizer.SynthesizeTextToStreamAsync(text).GetResults()
        
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


