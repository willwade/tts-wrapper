# The MS SpeechSDK can do a lot of our base class - and better. So lets overrride that
from __future__ import annotations

import logging
import threading
import time
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from . import MicrosoftClient
    from .ssml import MicrosoftSSML

try:
    import azure.cognitiveservices.speech as speechsdk
    from azure.cognitiveservices.speech import (
        AudioConfig,
        SpeechConfig,
        SpeechSynthesizer,
    )
except ImportError:
    speechsdk = None  # type: ignore[assignment]


class MicrosoftTTS(AbstractTTS):
    """High-level TTS interface for Microsoft Azure."""

    def __init__(
        self,
        client: MicrosoftClient,
        lang: str | None = None,
        voice: str | None = None,
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

        # Initialize timers list
        self.timers = []
        self._word_timings_processed = False
        self._word_timings = []  # Class variable to store word timings

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
            audio_config=None,  # No audio output config for raw PCM
        )

    def get_audio_duration(self) -> float:
        if self.timings:
            # Return the end time of the last word
            return self.timings[-1][1]
        return 0.0

    @property
    def ssml(self) -> MicrosoftSSML:
        """Get SSML handler."""
        return self._ssml

    def get_voices(self) -> list[dict[str, Any]]:
        """Get available voices."""
        return self._client.get_voices()

    def set_voice(self, voice_id: str, lang_id: str | None = None) -> None:
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
            if isinstance(rate, str) and rate.lower() in [
                "x-slow",
                "slow",
                "medium",
                "fast",
                "x-fast",
            ]:
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

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Convert text to speech."""
        text = str(text)
        # Initialize a list to store word timings
        self._word_timings = []
        logging.debug("Initialized word_timings: %s", self._word_timings)

        # Use voice_id if provided, otherwise use the default voice
        if voice_id and voice_id != self._voice:
            # Temporarily set the voice for this synthesis
            original_voice = self._voice
            self.set_voice(voice_id, self._lang)
            restore_voice = True
        else:
            restore_voice = False

        # Create a list to store word timings
        word_timings = []

        # Create a callback function to handle word boundary events
        def handle_word_boundary(evt):
            logging.debug(
                "Word boundary event: %s, offset: %s, duration: %s",
                evt.text,
                evt.audio_offset,
                evt.duration,
            )

            if evt.text and not evt.text.isspace():
                logging.debug("Condition met, adding word timing")
                # Convert to seconds, handling potential timedelta objects
                start_time = self._convert_to_seconds(evt.audio_offset)
                duration = self._convert_to_seconds(evt.duration)
                end_time = start_time + duration  # Calculate end time

                # Create the timing tuple
                timing = (start_time, end_time, evt.text)
                logging.debug("Created timing tuple: %s", timing)

                # Append to the list
                word_timings.append(timing)
                logging.debug(
                    "Added word timing: %s, start: %s, end: %s",
                    evt.text,
                    start_time,
                    end_time,
                )
                logging.debug("Current word_timings: %s", word_timings)
                logging.debug("Current word_timings length: %d", len(word_timings))

        try:
            # Create a new speech synthesizer for this specific synthesis
            speech_config = speechsdk.SpeechConfig(
                subscription=self._client._subscription_key,
                region=self._client._subscription_region,
            )
            speech_config.speech_synthesis_voice_name = self._voice
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=None
            )

            # Connect word boundary callback
            synthesizer.synthesis_word_boundary.connect(handle_word_boundary)

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
                    f"{inner_text}"
                    "</voice>"
                    "</speak>"
                )
                logging.debug("Final SSML: %s", text)

            # Use synchronous speak_ssml
            result = synthesizer.speak_ssml(text)

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data

                # Set word timings for callbacks
                logging.debug("Word timings collected: %s", word_timings)
                logging.debug("Word timings length: %d", len(word_timings))

                # Store the word timings directly in self.timings
                if word_timings:
                    self.timings = word_timings.copy()
                    logging.debug("Directly set self.timings: %s", self.timings)
                else:
                    logging.debug("No word timings collected, self.timings not set")

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
            if "synthesizer" in locals():
                synthesizer.synthesis_word_boundary.disconnect_all()
            if restore_voice:
                self.set_voice(original_voice, self._lang)

    def get_word_timings(self) -> list[tuple[float, float, str]]:
        """Get word timings directly from the synthesizer."""
        return self._word_timings

    def _is_ssml(self, text: str) -> bool:
        """Check if text contains SSML markup."""
        text = text.strip()
        # Check for both simple <speak> tags and those with namespaces
        return text.startswith("<speak") and text.endswith("</speak>")

    def _convert_to_seconds(self, value: int | float | timedelta) -> float:
        """
        Convert a value to seconds, handling different types.

        Parameters
        ----------
        value : Union[int, float, timedelta]
            The value to convert to seconds. Can be:
            - int/float: Assumed to be in 100-nanosecond units (Azure's format)
            - timedelta: A datetime.timedelta object

        Returns
        -------
        float
            The value converted to seconds
        """
        if isinstance(value, timedelta):
            return value.total_seconds()
        if isinstance(value, (int, float)):
            return value / 10000000  # Convert from 100-nanosecond units to seconds
        logging.warning(f"Unknown time value type: {type(value)}, value: {value}")
        # Try to convert to float as a fallback
        try:
            return float(value) / 10000000
        except (TypeError, ValueError):
            logging.error(f"Could not convert {value} to seconds")
            return 0.0

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """
        Start playback of the given text with callbacks triggered at each word.

        Parameters
        ----------
        text : str
            The text to be spoken.
        callback : Callable, optional
            A callback function to invoke at each word
            with arguments (word, start, end).
            If None, `self.on_word_callback` is used.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        """
        if callback is None:
            callback = self.on_word_callback

        # Synthesize the audio and collect word timings
        audio_data = self.synth_to_bytes(text, voice_id)

        # Load and play the audio
        self.load_audio(audio_data)
        self.play()

        start_time = time.time()

        # Use the word timings collected during synthesis
        try:
            logging.debug("Setting up callbacks for timings: %s", self.timings)
            for start, end, word in self.timings:
                delay = max(0, start - (time.time() - start_time))
                timer = threading.Timer(delay, callback, args=(word, start, end))
                timer.start()
                self.timers.append(timer)
        except (ValueError, TypeError):
            logging.exception("Error in start_playback_with_callbacks")

    def speak_streamed(self, text: str | SSML, voice_id: str | None = None) -> None:
        """
        Synthesize text to speech and stream it for playback.

        Parameters
        ----------
        text : str | SSML
            The text to synthesize and stream.
        voice_id : str | None, optional
            The ID of the voice to use for synthesis. If None, uses the voice set by set_voice.
        """
        # Override the speak_streamed method to use our word timings
        try:
            # Synthesize the audio and collect word timings
            audio_data = self.synth_to_bytes(text, voice_id)

            # Load and play the audio
            self.load_audio(audio_data)
            self.play()
        except Exception:
            logging.exception("Error in streaming synthesis")
