#The MS SpeechSDK can do a lot of our base class - and better. So lets overrride that
from typing import Any, List,Dict, Optional

from ...exceptions import UnsupportedFileFormat
from ...tts import AbstractTTS, FileFormat
from . import MicrosoftClient, MicrosoftSSML

from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import azure.cognitiveservices.speech as speechsdk
import logging

class MicrosoftTTS(AbstractTTS):
    def __init__(self, client: MicrosoftClient, lang: Optional[str] = None, voice: Optional[str] = None):
        super().__init__()
        self._client = client
        self.set_voice(voice or "en-US-JessaNeural", lang or "en-US")
        self._ssml = MicrosoftSSML(self._lang,self._voice) 
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._client.speech_config,
            audio_config=audio_config
        )

    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]
    
    def speak(self, ssml: str, format: Optional[FileFormat] = "wav"):
        format = self._client.FORMATS.get(format, "Riff24Khz16BitMonoPcm")
        self._client.speech_config.set_speech_synthesis_output_format(getattr(speechsdk.SpeechSynthesisOutputFormat, format))

        result = self.synthesizer.speak_ssml_async(str(ssml)).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logging.info("Speech synthesized for text [{}]".format(ssml))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.info("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.error("Error details: {}".format(cancellation_details.error_details))


    @property
    def ssml(self) -> MicrosoftSSML:
        return MicrosoftSSML(self._lang, self._voice)

    def get_voices(self) -> List[Dict[str, Any]]:
        return self._client.get_available_voices()

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

    def synth_to_bytes(self, ssml: str, format: Optional[FileFormat] = "wav") -> bytes:
        format = self._client.FORMATS.get(format, "Riff24Khz16BitMonoPcm")
        self._client.speech_config.set_speech_synthesis_output_format(getattr(speechsdk.SpeechSynthesisOutputFormat, format))
        self.audio_config = None
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._client.speech_config, 
            audio_config=self.audio_config
        )
        # Reset word timings
        self.word_timings = []
        # Subscribe to synthesis_word_boundary event
        self.synthesizer.synthesis_word_boundary.connect(lambda evt: self.word_timings.append((float(evt.audio_offset / 10000000),evt.text)))
        ssml_string = str(ssml)
        result = self.synthesizer.speak_ssml_async(ssml_string).get()  # Use speak_ssml_async for SSML input
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Store word timings
            self.set_timings(self.word_timings)
            return result.audio_data
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.error("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.error("Error details: {}".format(cancellation_details.error_details))
                raise Exception(f"Synthesis error: {cancellation_details.error_details}")
        else:
            raise Exception("Synthesis failed without detailed error message.")
    
    @property
    def ssml(self) -> MicrosoftSSML:
        return self._ssml

    @AbstractTTS.volume.setter
    def volume(self, value):
        self._volume = value
        self._ssml.volume = value

    @AbstractTTS.rate.setter
    def rate(self, value):
        self._rate = value
        self._ssml.rate = value
