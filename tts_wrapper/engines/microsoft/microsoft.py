# The MS SpeechSDK can do a lot of our base class - and better. So lets overrride that
from typing import Any, Optional

from tts_wrapper.tts import AbstractTTS

from . import MicrosoftClient
from .client import FORMATS

try:
    import azure.cognitiveservices.speech as speechsdk
    from azure.cognitiveservices.speech import (
        AudioConfig,
        SpeechConfig,
        SpeechSynthesizer,
    )
except ImportError:
    speechsdk = None  # type: ignore

import logging


class MicrosoftTTS(AbstractTTS):
    def __init__(
        self,
        client: MicrosoftClient,
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._client = client
        self.set_voice(voice or "en-US-JennyNeural", lang or "en-US")

        from .ssml import MicrosoftSSML
        self._ssml = MicrosoftSSML(self._lang, self._voice)

        # Ensure we're requesting word boundary information
        self._client.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps,
            "true",
        )

        # We'll create the synthesizer in synth_to_bytes to ensure it has the latest config
        self.synthesizer = None

    def get_audio_duration(self) -> float:
        if self.timings:
            # Return the end time of the last word
            return self.timings[-1][1]
        return 0.0

    @property
    def ssml(self) -> "MicrosoftSSML":
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        return self._client.get_available_voices()

    def set_voice(self, voice_id: str, lang_id: str) -> None:
        """Sets the voice for the TTS engine and updates the SSML configuration accordingly.

        @param voice_id: The ID of the voice to be used for synthesis.
        """
        super().set_voice(voice_id)
        self._voice = voice_id
        self._lang = lang_id or self._lang
        self._client.speech_config.speech_synthesis_voice_name = self._voice
        self._client.speech_config.speech_synthesis_language = self._lang

    def construct_prosody_tag(self, text: str) -> str:
        properties = []
        rate = self.get_property("rate")
        if rate != "":
            properties.append(f'rate="{rate}"')

        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')

        volume = self.get_property("volume")
        if volume != "":
            properties.append(f'volume="{volume}"')

        prosody_content = " ".join(properties)

        return f"<prosody {prosody_content}>{text}</prosody>"


    def synth_to_bytes(self, text: Any) -> bytes:
        ssml = self.ssml.add(str(text)) if not self._is_ssml(str(text)) else str(text)

        azure_format = FORMATS.get("wav", "Riff24Khz16BitMonoPcm")
        self._client.speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, azure_format),
        )

        # Ensure we're requesting word boundary information
        self._client.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps,
            "true",
        )

        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._client.speech_config, audio_config=None,
        )

        word_timings = []

        def word_boundary_callback(evt) -> None:
            start_time = evt.audio_offset / 10000000  # Convert to seconds
            duration = evt.duration.total_seconds()
            end_time = start_time + duration
            word_timings.append((start_time, end_time, evt.text))
            logging.debug(
                f"Word: {evt.text}, Start: {start_time:.3f}s, Duration: {duration:.3f}s",
            )

        self.synthesizer.synthesis_word_boundary.connect(word_boundary_callback)

        result = self.synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            self.set_timings(word_timings)
            logging.info("Captured %s word timings", len(word_timings))
            return result.audio_data
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.error("Speech synthesis canceled: %s", cancellation_details.reason)
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.error("Error details: %s", cancellation_details.error_details)
                msg = f"Synthesis error: {cancellation_details.error_details}"
                raise Exception(
                    msg,
                )
            return None
        msg = "Synthesis failed without detailed error message."
        raise Exception(msg)

    def get_audio_duration(self) -> float:
        if self.timings:
            # Return the end time of the last word
            return self.timings[-1][1]
        return 0.0

    def _is_ssml(self, ssml):
        return "<speak" in str(ssml)
