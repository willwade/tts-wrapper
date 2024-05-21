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
        temp_filename = create_temp_filename(".wav")
        
        stream = self._synthesizer.SynthesizeTextToStreamAsync(text).GetResults()

        with open(temp_filename, "wb") as f:
            stream.GetInputStreamAt(0).AsStream().copy_to(f)

        with open(temp_filename, "rb") as temp_f:
            content = temp_f.read()
        os.remove(temp_filename)
        return content

def create_temp_filename(extension: str) -> str:
    return os.path.join(os.getcwd(), f"temp{extension}")

# Example usage:
if __name__ == "__main__":
    client = UWPClient()
    print("Available voices:", client.get_voices())
    audio_data = client.synth("Hello, this is a test of the UWP TTS engine.")
    with open("output.wav", "wb") as f:
        f.write(audio_data)