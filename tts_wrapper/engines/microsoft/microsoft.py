from typing import Any, List,Dict, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MicrosoftClient, MicrosoftSSML

from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import azure.cognitiveservices.speech as speechsdk

class MicrosoftTTS(AbstractTTS):
    def __init__(self, client: MicrosoftClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()  # This is crucial
        self._client = client
        # this below will change depending on streaming or playing direct
        self.initsynth('Device')
        self.set_voice(voice or "en-US-JessaNeural", lang or "en-US")
        self.audio_rate = 24000

    def initsynth(self, output='Device'):
        if output == 'Device':
            # Configure the synthesizer to play audio through the default speaker
            self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        else:
            # Configure the synthesizer to generate audio data without playing it
            self.audio_config = None  # This setup tells the SDK to not play the audio automatically.
        
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._client.speech_config, 
            audio_config=self.audio_config
        )
        
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    @property
    def ssml(self) -> MicrosoftSSML:
        return MicrosoftSSML(self._lang, self._voice)

    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service."""
        return self._client.get_available_voices()
        
    def synth_to_bytes(self, ssml: str, format: Optional[FileFormat] = "wav") -> bytes:
        self.initsynth(None)  # Ensure synthesizer is set to generate bytes without playing them
        ssml_string = str(ssml)
        result = self.synthesizer.speak_ssml_async(ssml_string).get()  # Use speak_ssml_async for SSML input
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
                raise Exception(f"Synthesis error: {cancellation_details.error_details}")
        else:
            raise Exception("Synthesis failed without detailed error message.")

    
    # ovwrrides base class. More efficient
    def speak(self, ssml: str, format: FileFormat) -> bytes:
        self.initsynth('Device')
        self._client.speech_config.set_speech_synthesis_output_format(getattr(speechsdk.SpeechSynthesisOutputFormat, format))

        result = synthesizer.speak_text_async(str(ssml)).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized for text [{}]".format(text))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
        return result.audio_data
        
    def set_voice(self, voice_id: str, lang_id: str):
        """
        Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or self._lang
        self._client.speech_config.speech_synthesis_voice_name = self._voice
        self._client.speech_config.speech_synthesis_language = self._lang 
        
