from ...tts import AbstractTTS, FileFormat
from . import WitAUClient, WitAISML
from ...engines.utils import estimate_word_timings  # Import the timing estimation function

class WitAiTTS(AbstractTTS):
    def __init__(self, client: WitAiClient, voice: Optional[str] = "Rebecca", lang: Optional[str] = "en-US"):
        super().__init__()
        self._client = client
        self._voice = voice
        self._lang = lang
        self.audio_rate = 24000  # Adjusted based on Wit.ai's 24kHz sample rate for PCM

    def synth_to_bytes(self, text: str, format: Optional[str] = "pcm") -> bytes:
        if format not in ["pcm", "mp3", "wav"]:
            raise UnsupportedFileFormat(format, self.__class__.__name__)
        word_timings = estimate_word_timings(text)
        self.set_timings(word_timings)
        return self._client.synth(text, self._voice, format)

    @property
    def ssml(self) -> WitSSML:
        """Returns an instance of the WitSSML class for constructing SSML strings."""
        return WitSSML()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Retrieves a list of available voices from the Wit.ai service."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str):
        """Sets the voice for the TTS engine."""
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id