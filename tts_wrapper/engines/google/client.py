from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Any, Callable

try:
    from google.cloud import texttospeech_v1beta1 as texttospeech
    from google.oauth2 import service_account
except ImportError:
    texttospeech = None  # type: ignore
    service_account = None  # type: ignore

from tts_wrapper.exceptions import ModuleNotInstalled
from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path


class GoogleClient(AbstractTTS):
    def __init__(self, credentials: str | dict) -> None:
        """Initialize the GoogleClient with credentials. Accepts either a file path or a dictionary.

        Args:
            credentials: The credentials for Google Cloud, can be a file path (str) or a dictionary.
        """
        super().__init__()
        self._credentials = credentials
        self._client = None
        self._voice = None
        self._lang = None
        self.audio_rate = 24000  # Default sample rate for Google TTS

    def _initialize_client(self) -> None:
        self.texttospeech = texttospeech
        self.service_account = service_account
        if self._client is None:
            try:
                if isinstance(self._credentials, str):
                    # Credentials provided as a file path
                    self._client = self.texttospeech.TextToSpeechClient(
                        credentials=self.service_account.Credentials.from_service_account_file(
                            self._credentials,
                        ),
                    )
                elif isinstance(self._credentials, dict):
                    # Credentials provided as a dictionary
                    self._client = self.texttospeech.TextToSpeechClient(
                        credentials=self.service_account.Credentials.from_service_account_info(
                            self._credentials,
                        ),
                    )
                else:
                    msg = "Credentials must be a file path (str) or a dictionary"
                    raise ValueError(
                        msg,
                    )

            except ImportError:
                msg = "google-cloud-texttospeech"
                raise ModuleNotInstalled(msg)

        if not self._credentials:
            msg = "Credentials are required"
            raise ValueError(msg)

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Sets the voice and language for the client.

        Args:
            voice_id: The name of the voice to use.
            lang: The language code (e.g., 'en-US').
        """
        self._voice = voice_id
        if lang:
            self._lang = lang

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes in WAV format
        """
        self._initialize_client()

        # Determine if the text is SSML
        text_str = str(text)
        if text_str.strip().startswith("<speak>"):
            s_input = self.texttospeech.SynthesisInput(ssml=text_str)
        else:
            s_input = self.texttospeech.SynthesisInput(text=text_str)

        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else self._voice

        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=self._lang or "en-US",
            name=voice,
        )

        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.audio_rate,
        )

        resp = self._client.synthesize_speech(
            request=self.texttospeech.SynthesizeSpeechRequest(
                input=s_input,
                voice=voice_params,
                audio_config=audio_config,
            ),
        )

        return resp.audio_content

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

    def synth_raw(
        self,
        ssml: str,
        voice: str | None = None,
        lang: str | None = None,
        include_timepoints: bool = False,
    ) -> dict[str, Any]:
        self._initialize_client()

        s_input = self.texttospeech.SynthesisInput(ssml=ssml)
        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=lang or self._lang,
            name=voice or self._voice,
        )
        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
        )

        if include_timepoints:
            timepoints = [
                self.texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK,
            ]
        else:
            timepoints = []

        resp = self._client.synthesize_speech(
            request=self.texttospeech.SynthesizeSpeechRequest(
                input=s_input,
                voice=voice_params,
                audio_config=audio_config,
                enable_time_pointing=timepoints,
            ),
        )

        result = {
            "audio_content": resp.audio_content,
        }

        if include_timepoints:
            result["timepoints"] = [
                {"markName": tp.mark_name, "timeSeconds": tp.time_seconds}
                for tp in resp.timepoints
            ]

        return result

    def get_audio_duration(self) -> float:
        """Get the duration of the loaded audio in seconds.

        Returns:
            Duration in seconds
        """
        if not hasattr(self, "_audio_bytes") or not self._audio_bytes:
            return 0.0

        return self._get_audio_duration(self._audio_bytes)

    def _get_audio_duration(self, audio_content: bytes) -> float:
        """Parse WAV header to get audio duration.

        Args:
            audio_content: Raw WAV audio bytes

        Returns:
            Duration in seconds
        """
        # Parse WAV header to get sample rate and number of samples
        riff, size, fformat = struct.unpack("<4sI4s", audio_content[:12])
        if riff != b"RIFF" or fformat != b"WAVE":
            msg = "Not a WAV file"
            raise ValueError(msg)

        subchunk1, subchunk1_size = struct.unpack("<4sI", audio_content[12:20])
        if subchunk1 != b"fmt ":
            msg = "Not a valid WAV file"
            raise ValueError(msg)

        aformat, channels, sample_rate, byte_rate, block_align, bits_per_sample = (
            struct.unpack("HHIIHH", audio_content[20:36])
        )

        subchunk2, subchunk2_size = struct.unpack("<4sI", audio_content[36:44])
        if subchunk2 != b"data":
            msg = "Not a valid WAV file"
            raise ValueError(msg)

        num_samples = subchunk2_size // (channels * (bits_per_sample // 8))
        return num_samples / sample_rate

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable[[], None]]] = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Trigger onStart callbacks
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Synthesize with timepoints if possible
        self._initialize_client()

        # Determine if the text is SSML
        text_str = str(text)
        if text_str.strip().startswith("<speak>"):
            s_input = self.texttospeech.SynthesisInput(ssml=text_str)
        else:
            s_input = self.texttospeech.SynthesisInput(text=text_str)

        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else self._voice

        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=self._lang or "en-US",
            name=voice,
        )

        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.audio_rate,
        )

        # Try to get timepoints if available
        try:
            timepoints = [
                self.texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK
            ]
            resp = self._client.synthesize_speech(
                request=self.texttospeech.SynthesizeSpeechRequest(
                    input=s_input,
                    voice=voice_params,
                    audio_config=audio_config,
                    enable_time_pointing=timepoints,
                ),
            )

            # Store audio bytes
            self._audio_bytes = resp.audio_content

            # Call the callback for each word timing if provided
            if callback is not None:
                # Check if we have timepoints
                if hasattr(resp, "timepoints") and resp.timepoints:
                    for tp in resp.timepoints:
                        # Estimate end time as start time + 0.3 seconds
                        callback(tp.mark_name, tp.time_seconds, tp.time_seconds + 0.3)
                else:
                    # Fallback to word-by-word estimation
                    words = text_str.split()
                    total_duration = self._get_audio_duration(resp.audio_content)
                    time_per_word = total_duration / len(words) if words else 0

                    current_time = 0.0
                    for word in words:
                        end_time = current_time + time_per_word
                        callback(word, current_time, end_time)
                        current_time = end_time
        except Exception:
            # Fallback to regular synthesis without timepoints
            audio_bytes = self.synth_to_bytes(text, voice_id)
            self._audio_bytes = audio_bytes

            # Estimate word timings based on text length
            if callback is not None:
                words = text_str.split()
                total_duration = self._get_audio_duration(audio_bytes)
                time_per_word = total_duration / len(words) if words else 0

                current_time = 0.0
                for word in words:
                    end_time = current_time + time_per_word
                    callback(word, current_time, end_time)
                    current_time = end_time

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Google Cloud Text-to-Speech service.

        Returns:
            List of voice dictionaries with raw language information
        """
        self._initialize_client()

        response = self._client.list_voices()
        voices = response.voices  # Assuming this returns a list of voice objects
        standardized_voices = []

        for voice in voices:
            voice_data = {
                "id": voice.name,
                "name": voice.name,
                "language_codes": voice.language_codes,
                "gender": voice.ssml_gender.name,  # 'MALE', 'FEMALE', 'NEUTRAL'
            }
            standardized_voices.append(voice_data)

        return standardized_voices
