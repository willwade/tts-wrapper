from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, Callable, Optional

from tts_wrapper.exceptions import ModuleNotInstalled
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None  # type: ignore


Credentials = tuple[str, Optional[str]]

FORMATS = {"wav": "Riff24Khz16BitMonoPcm"}


class MicrosoftClient(AbstractTTS):
    """Client for Microsoft Azure TTS service."""

    def __init__(
        self,
        credentials: Credentials | None = None,
    ) -> None:
        """Initialize the client with credentials.

        Args:
            credentials: Tuple of (subscription_key, region)
        """
        super().__init__()

        if speechsdk is None:
            msg = "speechsdk"
            raise ModuleNotInstalled(msg)

        if not credentials or not credentials[0]:
            msg = "subscription_key is required"
            raise ValueError(msg)

        self._subscription_key = credentials[0]
        self._subscription_region = credentials[1] or "eastus"

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self._subscription_key,
            region=self._subscription_region,
        )

        # Default audio rate for playback
        self.audio_rate = 16000

        # Initialize word timings list
        self._word_timings: list[tuple[float, float, str]] = []

        # Set default voice
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyMultilingualNeural"

    def check_credentials(self) -> bool:
        """Verifies that the provided credentials are valid by initializing SpeechConfig."""
        try:
            # Attempt to create a synthesizer using the speech config
            # This checks if the subscription key and region are accepted without any API call.
            speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
            )
            return True
        except Exception:
            return False

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Microsoft Azure TTS service.

        Returns:
            List of voice dictionaries with raw language information
        """
        if requests is None:
            msg = "requests module is required to fetch voices"
            raise ModuleNotInstalled(msg)

        # Extract the subscription key and region from the speech_config
        subscription_key = self.speech_config.subscription_key
        region = self.speech_config.region

        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}

        try:
            # Use a Session to reuse the connection
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.get(url)
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.exception("Error fetching voices: %s", e)
            msg = f"Failed to fetch voices; error details: {e}"
            raise Exception(msg)

        voices = response.json()
        standardized_voices = []

        for voice in voices:
            voice_dict = {
                "id": voice["ShortName"],
                "language_codes": [voice["Locale"]],
                "name": voice["LocalName"],
                "gender": voice["Gender"],  # 'Gender' is already a string
            }
            standardized_voices.append(voice_dict)

        return standardized_voices

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use (e.g., "en-US-AriaNeural")
            lang: Optional language code (not used in Microsoft)
        """
        self.speech_config.speech_synthesis_voice_name = voice_id

    def _convert_to_seconds(self, time_value) -> float:
        """Convert a time value to seconds.

        Args:
            time_value: Time value to convert (can be int, float, or timedelta)

        Returns:
            Time value in seconds as a float
        """
        if hasattr(time_value, "total_seconds"):
            # It's a timedelta object
            return time_value.total_seconds()
        # It's a numeric value in 100-nanosecond units (1 second = 10,000,000 units)
        return float(time_value) / 10000000.0

    def _is_ssml(self, text: str) -> bool:
        """Check if the text is SSML.

        Args:
            text: Text to check

        Returns:
            True if the text is SSML, False otherwise
        """
        return text.strip().startswith("<speak")

    def construct_prosody_tag(self, text: str) -> str:
        """Construct a prosody tag with the current properties.

        Args:
            text: Text to wrap in prosody tag

        Returns:
            Text wrapped in prosody tag with current properties
        """
        attrs = {}
        for prop in ["rate", "volume", "pitch"]:
            value = self.get_property(prop)
            if value:
                attrs[prop] = value

        if not attrs:
            return text

        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f"<prosody {attr_str}>{text}</prosody>"

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes in WAV format
        """
        text = str(text)
        # Initialize a list to store word timings
        self._word_timings = []
        logging.debug("Initialized word_timings: %s", self._word_timings)

        # Use voice_id if provided, otherwise use the default voice
        original_voice = None
        restore_voice = False
        if voice_id:
            # Temporarily set the voice for this synthesis
            original_voice = self.speech_config.speech_synthesis_voice_name
            self.set_voice(voice_id)
            restore_voice = True

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
            # Create a synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)

            # Connect word boundary callback
            synthesizer.synthesis_word_boundary.connect(handle_word_boundary)

            # Check if text already contains SSML
            if self._is_ssml(text):
                # Check if it has the required Microsoft SSML attributes
                if (
                    'xmlns="http://www.w3.org/2001/10/synthesis"' not in text
                    and "xml:lang=" not in text
                ):
                    # Extract the content between <speak> and </speak>
                    import re

                    match = re.search(r"<speak>(.*?)</speak>", text, re.DOTALL)
                    if match:
                        inner_content = match.group(1)
                        # Wrap in proper Microsoft SSML
                        voice_name = self.speech_config.speech_synthesis_voice_name
                        text = (
                            '<speak xmlns="http://www.w3.org/2001/10/synthesis" '
                            'version="1.0" xml:lang="en-US">'
                            f'<voice name="{voice_name}">'
                            f"{inner_content}"
                            "</voice>"
                            "</speak>"
                        )
                    else:
                        # If we can't extract the content, use the original text
                        # but add the required attributes
                        text = text.replace(
                            "<speak>",
                            '<speak xmlns="http://www.w3.org/2001/10/synthesis" '
                            'version="1.0" xml:lang="en-US">',
                        )
                # Use speak_ssml for SSML text
                logging.debug("Using SSML: %s", text)
                result = synthesizer.speak_ssml(text)
            else:
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
                voice_name = self.speech_config.speech_synthesis_voice_name
                text = (
                    '<speak xmlns="http://www.w3.org/2001/10/synthesis" '
                    'version="1.0" xml:lang="en-US">'
                    f'<voice name="{voice_name}">'
                    f"{inner_text}"
                    "</voice>"
                    "</speak>"
                )
                logging.debug("Final SSML: %s", text)
                # Use speak_ssml for SSML text
                result = synthesizer.speak_ssml(text)

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data

                # Set word timings for callbacks
                logging.debug("Word timings collected: %s", word_timings)
                logging.debug("Word timings length: %d", len(word_timings))

                # Store the word timings directly in self.timings
                if word_timings:
                    self.timings = word_timings.copy()
                    self._word_timings = word_timings.copy()
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
            if restore_voice and original_voice:
                self.set_voice(original_voice)

    def get_word_timings(self) -> list[tuple[float, float, str]]:
        """Get word timings directly from the synthesizer.

        Returns:
            List of word timing tuples (start_time, end_time, word)
        """
        return self._word_timings

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis
            callback: Callback function for word timing events
        """
        # Trigger onStart callback
        self._trigger_callback("onStart")

        # Set the callback if provided
        if callback is not None:
            self.on_word_callback = callback

        # Synthesize and play the audio
        self.speak_streamed(text, voice_id, trigger_callbacks=False)

        # Process word timings
        if self.timings:
            for start_time, end_time, word in self.timings:
                # Schedule word callback
                timer = threading.Timer(
                    start_time,
                    self._trigger_callback,
                    args=["onWord", word, start_time],
                )
                timer.daemon = True
                timer.start()
                self.timers.append(timer)

                # Also call the callback directly if provided
                if callback is not None:
                    try:
                        callback(word, start_time, end_time)
                    except Exception as e:
                        logging.error(f"Error in word callback: {e}")

            # Schedule onEnd callback
            if self.timings:
                last_timing = self.timings[-1]
                end_time = last_timing[1]  # End time of the last word
                timer = threading.Timer(
                    end_time, self._trigger_callback, args=["onEnd"]
                )
                timer.daemon = True
                timer.start()
                self.timers.append(timer)
        else:
            # If no timings, trigger onEnd after a short delay
            timer = threading.Timer(0.5, self._trigger_callback, args=["onEnd"])
            timer.daemon = True
            timer.start()
            self.timers.append(timer)

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None, format: str = "wav"
    ) -> Generator[bytes, None, None]:
        """Synthesizes text to an in-memory bytestream and yields audio data chunks.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis
            format: The desired audio format (e.g., 'wav', 'mp3', 'flac')

        Returns:
            A generator yielding bytes objects containing audio data
        """
        import io

        # Generate the full audio content
        audio_content = self.synth_to_bytes(text, voice_id)

        # Create a BytesIO object from the audio content
        audio_stream = io.BytesIO(audio_content)

        # Define chunk size (adjust as needed)
        chunk_size = 4096  # 4KB chunks

        # Yield chunks of audio data
        while True:
            chunk = audio_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
