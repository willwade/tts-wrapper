# The MS SpeechSDK can do a lot of our base class - and better. So lets overrride that
from typing import Any, Optional
import logging
import threading
from queue import Queue

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

class MicrosoftTTS(AbstractTTS):
    """High-level TTS interface for Microsoft Azure."""

    def __init__(
        self,
        client: "MicrosoftClient",
        lang: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        """Initialize the Microsoft TTS interface."""
        super().__init__()
        self._client = client
        self._lang = lang or "en-US"
        # Set default neural voice if none specified
        self._voice = voice or "en-US-JennyMultilingualNeural"
        
        from .ssml import MicrosoftSSML
        self._ssml = MicrosoftSSML(self._lang, self._voice)
        
        # Set audio rate to match Microsoft's output (16kHz)
        self.audio_rate = 16000
        self.channels = 1
        self.sample_width = 2  # 16-bit audio
        
        # Configure synthesizer for streaming
        self._setup_synthesizer()
    
    def _setup_synthesizer(self) -> None:
        """Set up the speech synthesizer with proper configuration."""
        # Configure word boundary tracking
        self._client.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps,
            "true",
        )
        
        # Configure audio output format
        self._client.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
        )
        
        # Set voice and language
        self._client.speech_config.speech_synthesis_voice_name = self._voice
        self._client.speech_config.speech_synthesis_language = self._lang
        
        # Create synthesizer
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._client.speech_config,
            audio_config=None  # No audio output config for raw PCM
        )

    def get_audio_duration(self) -> float:
        if self.timings:
            # Return the end time of the last word
            return self.timings[-1][1]
        return 0.0

    @property
    def ssml(self) -> "MicrosoftSSML":
        """Get SSML handler."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_available_voices()

    def set_voice(self, voice_id: str, lang_id: Optional[str] = None) -> None:
        """Set voice and update Azure configuration."""
        super().set_voice(voice_id, lang_id or "en-US")
        self._voice = voice_id
        self._lang = lang_id or self._lang
        self._client.speech_config.speech_synthesis_voice_name = self._voice
        self._client.speech_config.speech_synthesis_language = self._lang
        
        # Recreate synthesizer with new voice
        self._setup_synthesizer()

    def construct_prosody_tag(self, text: str) -> str:
        properties = []
        rate = self.get_property("rate")
        if rate != "":
            # Handle predefined values
            if isinstance(rate, str) and rate.lower() in ["x-slow", "slow", "medium", "fast", "x-fast"]:
                properties.append(f'rate="{rate.lower()}"')
                logging.debug("Using predefined rate: %s", rate.lower())
            else:
                # Convert numeric rate to percentage (0-100 to 25%-400%)
                try:
                    rate_float = float(rate)
                    # Map 50 to 100% (normal speed)
                    # Below 50: 25%-100%
                    # Above 50: 100%-400%
                    if rate_float == 50:
                        rate_percent = 100
                    elif rate_float < 50:
                        # Map 0-49 to 25%-99%
                        rate_percent = 25 + (rate_float * 1.5)
                    else:
                        # Map 51-100 to 101%-400%
                        rate_percent = 100 + (rate_float - 50) * 6
                    properties.append(f'rate="{rate_percent}%"')
                    logging.debug("Converted rate %s to %s%%", rate, rate_percent)
                except ValueError:
                    # If not numeric and not predefined, use medium
                    properties.append('rate="medium"')
                    logging.debug("Invalid rate value, using medium")

        pitch = self.get_property("pitch")
        if pitch != "":
            properties.append(f'pitch="{pitch}"')

        volume = self.get_property("volume")
        if volume != "":
            # Convert numeric volume (0-100) to relative values
            try:
                vol_float = float(volume)
                # Map 0-100 to -100% to +100%
                vol_percent = (vol_float - 50) * 2
                properties.append(f'volume="{vol_percent:+.0f}%"')
            except ValueError:
                properties.append(f'volume="{volume}"')

        prosody_content = " ".join(properties)
        ssml = f"<prosody {prosody_content}>{text}</prosody>"
        logging.debug("Generated prosody tag: %s", ssml)
        return ssml

    def synth_to_bytes(self, text: Any) -> bytes:
        """Convert text to speech."""
        text = str(text)
        word_timings = []
        
        def handle_word_boundary(evt):
            if evt.text and not evt.text.isspace():
                word_timings.append((
                    evt.audio_offset / 10000000,  # Convert to seconds
                    evt.duration / 10000000,      # Convert to seconds
                    evt.text
                ))
        
        # Connect word boundary callback
        self.synthesizer.synthesis_word_boundary.connect(handle_word_boundary)
        
        try:
            # Check if text already contains SSML
            if not self._is_ssml(text):
                # Check for prosody properties
                has_properties = any(
                    self.get_property(prop) != ""
                    for prop in ["rate", "volume", "pitch"]
                )
                
                inner_text = text
                if has_properties:
                    # Wrap text in prosody tag with properties
                    inner_text = self.construct_prosody_tag(text)
                
                # Always wrap in speak and voice tags
                text = (
                    '<speak xmlns="http://www.w3.org/2001/10/synthesis" '
                    'version="1.0" xml:lang="en-US">'
                    f'<voice name="{self._voice}">'
                    f'{inner_text}'
                    '</voice>'
                    '</speak>'
                )
                logging.debug("Final SSML: %s", text)
            
            # Always use speak_ssml_async
            result = self.synthesizer.speak_ssml_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                # Set word timings for callbacks
                self.set_timings(word_timings)
                return audio_data
            
            if result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                msg = f"Speech synthesis canceled: {cancellation_details.reason}"
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    msg = f"Error details: {cancellation_details.error_details}"
                raise RuntimeError(msg)
            
            msg = "Synthesis failed without detailed error message"
            raise RuntimeError(msg)
            
        finally:
            # Disconnect event handlers
            self.synthesizer.synthesis_word_boundary.disconnect_all()

    def _is_ssml(self, text: str) -> bool:
        """Check if text contains SSML markup."""
        text = text.strip()
        return text.startswith("<speak>") and text.endswith("</speak>")
