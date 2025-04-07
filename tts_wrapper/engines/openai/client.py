"""OpenAI TTS client implementation."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Callable

from tts_wrapper.engines.openai.ssml import OpenAISSML
from tts_wrapper.ssml import AbstractSSMLNode
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient(AbstractTTS):
    """
    OpenAI TTS client implementation.

    This client uses the OpenAI API to generate speech from text.
    """

    def __init__(
        self,
        api_key: str | None = None,
        voice: str = "alloy",
        model: str = "gpt-4o-mini-tts",
        instructions: str | None = None,
    ) -> None:
        """
        Initialize the OpenAI TTS client.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable.
            voice: Voice to use. Default is "alloy".
            model: Model to use. Default is "gpt-4o-mini-tts".
            instructions: Additional instructions for the TTS model.
        """
        super().__init__()

        if not OPENAI_AVAILABLE:
            msg = "OpenAI package is not installed. Please install it with: pip install py3-tts-wrapper[openai]"
            raise ImportError(msg)

        # Use provided API key or get from environment
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            msg = "OpenAI API key is required. Provide it as an argument or set the OPENAI_API_KEY environment variable."
            raise ValueError(msg)

        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # Initialize SSML handler
        self.ssml = OpenAISSML()

        # Set default voice
        self.voice_id = None
        self.set_voice(voice)

        # Set default model using private method
        self._set_model(model)

        # Always use WAV format internally for best compatibility with AbstractTTS
        self._internal_format = "wav"

        # Set instructions using private method
        self._set_instructions(instructions)

        logging.debug(
            f"Initialized OpenAI TTS client with voice {voice} and model {model}"
        )

    def connect(self, event_name: str, callback: Callable) -> None:
        """Connect a callback function to an event."""
        super().connect(event_name, callback)

    def _get_voices(self) -> list[dict[str, Any]]:
        """
        Get available voices from OpenAI.

        Returns:
            List of voice dictionaries with id, name, and gender.
        """
        # List of languages supported by OpenAI TTS (based on Whisper model support)
        supported_languages = [
            "af",
            "ar",
            "hy",
            "az",
            "be",
            "bs",
            "bg",
            "ca",
            "zh",
            "hr",
            "cs",
            "da",
            "nl",
            "en",
            "et",
            "fi",
            "fr",
            "gl",
            "de",
            "el",
            "he",
            "hi",
            "hu",
            "is",
            "id",
            "it",
            "ja",
            "kn",
            "kk",
            "ko",
            "lv",
            "lt",
            "mk",
            "ms",
            "mr",
            "mi",
            "ne",
            "no",
            "fa",
            "pl",
            "pt",
            "ro",
            "ru",
            "sr",
            "sk",
            "sl",
            "es",
            "sw",
            "sv",
            "tl",
            "ta",
            "th",
            "tr",
            "uk",
            "ur",
            "vi",
            "cy",
        ]

        # OpenAI has a fixed set of voices
        return [
            {
                "id": "alloy",
                "name": "Alloy",
                "gender": "Neutral",
                "language_codes": supported_languages,
            },
            {
                "id": "ash",
                "name": "Ash",
                "gender": "Male",
                "language_codes": supported_languages,
            },
            {
                "id": "ballad",
                "name": "Ballad",
                "gender": "Male",
                "language_codes": supported_languages,
            },
            {
                "id": "coral",
                "name": "Coral",
                "gender": "Female",
                "language_codes": supported_languages,
            },
            {
                "id": "echo",
                "name": "Echo",
                "gender": "Male",
                "language_codes": supported_languages,
            },
            {
                "id": "fable",
                "name": "Fable",
                "gender": "Female",
                "language_codes": supported_languages,
            },
            {
                "id": "onyx",
                "name": "Onyx",
                "gender": "Male",
                "language_codes": supported_languages,
            },
            {
                "id": "nova",
                "name": "Nova",
                "gender": "Female",
                "language_codes": supported_languages,
            },
            {
                "id": "sage",
                "name": "Sage",
                "gender": "Neutral",
                "language_codes": supported_languages,
            },
            {
                "id": "shimmer",
                "name": "Shimmer",
                "gender": "Female",
                "language_codes": supported_languages,
            },
        ]

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """
        Set the voice to use for synthesis.

        Args:
            voice_id: The ID of the voice to use.
            lang: The language code (not used for OpenAI, as voices are language-specific).
        """
        # Verify the voice is valid
        available_voices = [voice["id"] for voice in self._get_voices()]
        if voice_id not in available_voices:
            msg = f"Invalid voice ID: {voice_id}. Available voices: {', '.join(available_voices)}"
            raise ValueError(msg)

        self.voice_id = voice_id
        logging.debug(f"Set voice to {voice_id}")

    def _is_ssml(self, text: str) -> bool:
        """
        Check if the text is SSML.

        Args:
            text: The text to check.

        Returns:
            True if the text is SSML, False otherwise.
        """
        return text.strip().startswith("<speak>") and text.strip().endswith("</speak>")

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """
        Transform written text to audio bytes.

        Args:
            text: The text to synthesize.
            voice_id: Optional voice ID to use for this synthesis.

        Returns:
            Raw audio bytes.
        """
        # Use provided voice_id or the one set with set_voice
        voice = voice_id or self.voice_id

        # Convert text to string safely
        try:
            if isinstance(text, AbstractSSMLNode):
                # If it's an SSML node, convert to string
                text_str = str(text)
            else:
                text_str = str(text)

            logging.debug(
                f"Text to synthesize: {text_str[:100]}{'...' if len(text_str) > 100 else ''}"
            )
        except Exception as e:
            logging.error(f"Failed to convert text to string: {e}")
            text_str = ""

        # Check if the text is SSML
        is_ssml = self._is_ssml(text_str)
        if is_ssml:
            # OpenAI doesn't support SSML, so strip the tags
            logging.debug("SSML detected, stripping tags")
            # Remove <speak> tags and convert to plain text
            text_str = str(text)

        try:
            # Update instructions from properties before synthesis
            self._update_instructions_from_properties()

            # Create speech using the OpenAI API
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text_str,
                response_format=self._internal_format,
                instructions=self.instructions,
            )

            # Get the audio content
            audio_bytes = response.content

            logging.debug(f"Synthesis successful, audio size: {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logging.error(f"Synthesis failed: {e}")
            return b""

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None
    ) -> Generator[bytes, None, None]:
        """
        Synthesize text to an in-memory bytestream and yield audio data chunks.

        Args:
            text: The text to synthesize.
            voice_id: Optional voice ID to use for this synthesis.

        Returns:
            A generator yielding bytes objects containing audio data.
        """
        # Use provided voice_id or the one set with set_voice
        voice = voice_id or self.voice_id

        # Convert text to string safely
        try:
            if isinstance(text, AbstractSSMLNode):
                # If it's an SSML node, convert to string
                text_str = str(text)
            else:
                text_str = str(text)
        except Exception as e:
            logging.error(f"Failed to convert text to string: {e}")
            text_str = ""

        # Check if the text is SSML
        is_ssml = self._is_ssml(text_str)
        if is_ssml:
            # OpenAI doesn't support SSML, so strip the tags
            logging.debug("SSML detected, stripping tags")
            # Remove <speak> tags and convert to plain text
            text_str = str(text)

        try:
            # Update instructions from properties before synthesis
            self._update_instructions_from_properties()

            # Create streaming response
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=voice,
                input=text_str,
                response_format=self._internal_format,
                instructions=self.instructions,
            ) as response:
                # Stream the response in chunks
                yield from response.iter_bytes(chunk_size=4096)
        except Exception as e:
            logging.error(f"Streaming synthesis failed: {e}")
            yield b""

    def synth(
        self,
        text: str | AbstractSSMLNode,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
        format: str | None = None,  # Added for compatibility
    ) -> None:
        """
        Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize.
            output_file: Path to save the audio file.
            output_format: Format to save as.
            voice_id: Optional voice ID to use for this synthesis.
            format: Alias for output_format (for compatibility).
        """
        # Use the parent class implementation which handles format conversion
        super().synth(text, output_file, output_format, voice_id, format)

    def _set_instructions(self, instructions: str | None) -> None:
        """
        Set instructions for the TTS model (private method).

        This is specific to OpenAI and can be used to control aspects of speech
        like accent, emotional range, intonation, etc.

        Args:
            instructions: Instructions for the TTS model. Can be None.
        """
        self.instructions = instructions
        if instructions:
            logging.debug(f"Set instructions: {instructions}")
        else:
            logging.debug("No instructions set")

    def _update_instructions_from_properties(self) -> None:
        """
        Update the instructions based on the current property values.

        This method combines the base instructions with any rate, volume, and pitch
        settings to create a comprehensive instruction for the OpenAI TTS model.
        """
        # Start with base instructions or empty string
        base_instructions = self.instructions or ""

        # Initialize a list to hold property-based instructions
        property_instructions = []

        # Add rate instruction if set
        rate = self.get_property("rate")
        if rate is not None:
            if isinstance(rate, (int, float)):
                # Convert numeric rate to descriptive term
                if rate < 0.8:
                    property_instructions.append("Speak very slowly.")
                elif rate < 0.95:
                    property_instructions.append("Speak slowly.")
                elif rate > 1.2:
                    property_instructions.append("Speak very quickly.")
                elif rate > 1.05:
                    property_instructions.append("Speak quickly.")
            elif isinstance(rate, str):
                # Use string rate directly
                property_instructions.append(f"Speak at a {rate} pace.")

        # Add volume instruction if set
        volume = self.get_property("volume")
        if volume is not None:
            if isinstance(volume, (int, float)):
                # Convert numeric volume to descriptive term
                if volume < 0.5:
                    property_instructions.append("Speak very quietly.")
                elif volume < 0.8:
                    property_instructions.append("Speak quietly.")
                elif volume > 1.5:
                    property_instructions.append("Speak very loudly.")
                elif volume > 1.2:
                    property_instructions.append("Speak loudly.")
            elif isinstance(volume, str):
                # Use string volume directly
                property_instructions.append(f"Speak at a {volume} volume.")

        # Add pitch instruction if set
        pitch = self.get_property("pitch")
        if pitch is not None:
            if isinstance(pitch, (int, float)):
                # Convert numeric pitch to descriptive term
                if pitch < 0.8:
                    property_instructions.append("Speak with a very low pitch.")
                elif pitch < 0.95:
                    property_instructions.append("Speak with a low pitch.")
                elif pitch > 1.2:
                    property_instructions.append("Speak with a very high pitch.")
                elif pitch > 1.05:
                    property_instructions.append("Speak with a high pitch.")
            elif isinstance(pitch, str):
                # Use string pitch directly
                property_instructions.append(f"Speak with a {pitch} pitch.")

        # Combine base instructions with property instructions
        if property_instructions:
            combined_instructions = base_instructions
            if combined_instructions and not combined_instructions.endswith("."):
                combined_instructions += ". "
            elif combined_instructions:
                combined_instructions += " "
            combined_instructions += " ".join(property_instructions)
            self.instructions = combined_instructions
            logging.debug(f"Updated instructions from properties: {self.instructions}")

    def _set_model(self, model: str) -> None:
        """
        Set the model to use for synthesis (private method).

        Args:
            model: The model to use (e.g., "gpt-4o-mini-tts", "tts-1", "tts-1-hd").
        """
        valid_models = ["gpt-4o-mini-tts", "tts-1", "tts-1-hd"]
        if model not in valid_models:
            logging.warning(
                f"Model {model} may not be supported. Valid models are: {', '.join(valid_models)}"
            )

        self.model = model
        logging.debug(f"Set model to {model}")

    def set_property(self, property_name: str, value: float | str) -> None:
        """
        Set a property for the TTS engine and update instructions accordingly.

        This overrides the AbstractTTS set_property method to update the instructions
        based on the property values, since OpenAI uses instructions to control speech.

        Parameters
        ----------
        property_name : str
            The name of the property to set ("rate", "volume", or "pitch").
        value : float | str
            The value to assign to the specified property.
        """
        # Call the parent method to set the property in the properties dictionary
        super().set_property(property_name, value)

        # Store the original instructions before updating
        original_instructions = self.instructions

        # Update instructions based on the new property values
        self._update_instructions_from_properties()

        # Log the change if instructions were updated
        if original_instructions != self.instructions:
            logging.debug(f"Updated instructions after setting {property_name}={value}")

    def get_property(self, property_name: str) -> Any:
        """
        Get a property value from the TTS engine.

        Parameters
        ----------
        property_name : str
            The name of the property to retrieve ("rate", "volume", or "pitch").

        Returns
        -------
        Any
            The value of the property, or None if not set.
        """
        return super().get_property(property_name)
