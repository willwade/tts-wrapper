from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any, Callable

import requests

from tts_wrapper.tts import AbstractTTS

if TYPE_CHECKING:
    from pathlib import Path

audio_format = ("pcm_22050",)


class ElevenLabsClient(AbstractTTS):
    def __init__(self, credentials) -> None:
        super().__init__()
        if not credentials:
            msg = "An API key for ElevenLabs must be provided"
            raise ValueError(msg)
        # Extract the API key from credentials tuple
        self.api_key = credentials[0] if isinstance(credentials, tuple) else credentials
        self.base_url = "https://api.elevenlabs.io"
        self.audio_rate = 22050  # Default sample rate for ElevenLabs

    def check_credentials(self) -> bool:
        """Check if the ElevenLabs credentials are valid.

        Returns:
            True if the credentials are valid, False otherwise
        """
        try:
            # Try to get voices to check if credentials are valid
            url = f"{self.base_url}/v1/voices"
            headers = {"xi-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Check if the response contains voices
            voices = response.json().get("voices", [])
            return len(voices) > 0
        except Exception as e:
            # Check for specific error messages that indicate invalid credentials
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                print(f"ElevenLabs credentials are invalid: {e}")
                return False
            if "quota_exceeded" in error_str:
                print(f"ElevenLabs quota exceeded: {e}")
                return False
            # For other errors, log but still return False to skip the test
            print(f"ElevenLabs error (not credential-related): {e}")
            return False

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """Set the voice to use for synthesis.

        Args:
            voice_id: The voice ID to use
            lang: Optional language code (not used in ElevenLabs)
        """
        self.voice_id = voice_id

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        if not voice:
            # Use a default voice if none is set
            voices = self._get_voices()
            if voices:
                voice = voices[0]["id"]
            else:
                msg = "No voice ID provided and no default voice available"
                raise ValueError(msg)

        # Get audio data with word timings
        audio_bytes, _ = self.synth_raw(str(text), voice)
        return audio_bytes

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
        text: str,
        voice_id: str,
    ) -> tuple[bytes, list[tuple[float, float, str]]]:
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}/stream/with-timestamps"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }
        params = {
            "output_format": audio_format,
            "optimize_streaming_latency": 0,
            "enable_logging": False,
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            params=params,
            stream=True,
        )

        if response.status_code != 200:
            error_message = f"[Elevenlabs.Client.Synth] Failed to synthesize speech: {response.status_code} - {response.reason}"
            try:
                json_response = response.json()
                if "detail" in json_response:
                    status = json_response["detail"].get(
                        "status",
                        "No status available",
                    )
                    message = json_response["detail"].get(
                        "message",
                        "No message provided",
                    )
                    error_message += f" Status: {status}. Message: {message}"
                else:
                    error_details = json_response.get("error", {}).get(
                        "message",
                        "No error details available.",
                    )
                    error_message += f" Details: {error_details}"
            except ValueError:
                error_message += " Error details not in JSON format."
            raise Exception(error_message)

        audio_bytes = b""
        characters = []
        character_start_times = []
        character_end_times = []

        for line in response.iter_lines():
            if line:
                json_string = line.decode("utf-8")
                response_dict = json.loads(json_string)
                audio_bytes += base64.b64decode(response_dict["audio_base64"])

                if response_dict.get("alignment") is not None:
                    characters.extend(response_dict["alignment"]["characters"])
                    character_start_times.extend(
                        response_dict["alignment"]["character_start_times_seconds"],
                    )
                    character_end_times.extend(
                        response_dict["alignment"]["character_end_times_seconds"],
                    )

        # Process character timings into word timings
        word_timings = self._process_word_timings(
            characters,
            character_start_times,
            character_end_times,
        )
        return audio_bytes, word_timings

    def _process_word_timings(self, characters, start_times, end_times):
        word_timings = []
        current_word = ""
        word_start = 0

        for char, start, end in zip(characters, start_times, end_times):
            if char.isspace() or char in [",", ".", "!", "?"]:  # Include punctuation
                if current_word:
                    word_timings.append((word_start, end, current_word))
                    current_word = ""
            else:
                if not current_word:
                    word_start = start
                current_word += char

        # Add the last word if there is one
        if current_word:
            word_timings.append((word_start, end_times[-1], current_word))

        return word_timings

    def get_voices(self):
        url = f"{self.base_url}/v1/voices"
        response = requests.get(url)
        if response.ok:
            voices_data = response.json()
            voices = voices_data["voices"]
            standardized_voices = []
            accent_to_language_code = {
                "american": "en-US",
                "british": "en-GB",
                "british-essex": "en-GB",
                "american-southern": "en-US",
                "australian": "en-AU",
                "irish": "en-IE",
                "english-italian": "en-IT",
                "english-swedish": "en-SE",
                "american-irish": "en-IE-US",
                "chinese": "zh-CN",
                "korean": "ko-KR",
                "dutch": "nl-NL",
                "turkish": "tr-TR",
                "swedish": "sv-SE",
                "indonesian": "id-ID",
                "filipino": "fil-PH",
                "japanese": "ja-JP",
                "ukrainian": "uk-UA",
                "greek": "el-GR",
                "czech": "cs-CZ",
                "finnish": "fi-FI",
                "romanian": "ro-RO",
                "danish": "da-DK",
                "bulgarian": "bg-BG",
                "malay": "ms-MY",
                "slovak": "sk-SK",
                "croatian": "hr-HR",
                "classic-arabic": "ar-SA",
                "tamil": "ta-IN",
            }
            supported_languages_v1 = {
                "en-US": "English",
                "pl-PL": "Polish",
                "de-DE": "German",
                "es-ES": "Spanish",
                "fr-FR": "French",
                "it-IT": "Italian",
                "hi-IN": "Hindi",
                "pt-BR": "Portuguese",
            }
            supported_languages_v2 = {
                "en-US": "English",
                "pl-PL": "Polish",
                "de-DE": "German",
                "es-ES": "Spanish",
                "fr-FR": "French",
                "it-IT": "Italian",
                "hi-IN": "Hindi",
                "pt-BR": "Portuguese",
                "zh-CN": "Chinese",
                "ko-KR": "Korean",
                "nl-NL": "Dutch",
                "tr-TR": "Turkish",
                "sv-SE": "Swedish",
                "id-ID": "Indonesian",
                "fil-PH": "Filipino",
                "ja-JP": "Japanese",
                "uk-UA": "Ukrainian",
                "el-GR": "Greek",
                "cs-CZ": "Czech",
                "fi-FI": "Finnish",
                "ro-RO": "Romanian",
                "da-DK": "Danish",
                "bg-BG": "Bulgarian",
                "ms-MY": "Malay",
                "sk-SK": "Slovak",
                "hr-HR": "Croatian",
                "ar-SA": "Classic Arabic",
                "ta-IN": "Tamil",
            }
            for voice in voices:
                voice["id"] = voice["voice_id"]
                accent = voice["labels"].get("accent", "american")
                accent_to_language_code.get(
                    accent,
                    "en-US",
                )  # Default to 'en-US'
                if voice["high_quality_base_model_ids"] == "eleven_multilingual_v1":
                    voice["language_codes"] = list(supported_languages_v1.keys())
                else:
                    voice["language_codes"] = list(supported_languages_v2.keys())
                voice["name"] = voice["name"]
                voice["gender"] = "Unknown"
                standardized_voices.append(voice)
            return standardized_voices
        response.raise_for_status()
        return None

    def _get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from ElevenLabs.

        Returns:
            List of voice dictionaries with raw language information
        """
        url = f"{self.base_url}/v1/voices"
        headers = {"xi-api-key": self.api_key}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            voices_data = response.json()["voices"]
            standardized_voices = []

            for voice in voices_data:
                standardized_voice = {
                    "id": voice["voice_id"],
                    "language_codes": ["en-US"],  # Default to English
                    "name": voice["name"],
                    "gender": "unknown",  # ElevenLabs doesn't provide gender info
                }
                standardized_voices.append(standardized_voice)

            return standardized_voices
        return []

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

        # Use provided voice_id or the one set with set_voice
        voice = voice_id if voice_id else getattr(self, "voice_id", None)

        if not voice:
            # Use a default voice if none is set
            voices = self._get_voices()
            if voices:
                voice = voices[0]["id"]
            else:
                msg = "No voice ID provided and no default voice available"
                raise ValueError(msg)

        # Synthesize with word timings
        try:
            audio_bytes, word_timings = self.synth_raw(str(text), voice)
            self._audio_bytes = audio_bytes

            # Call the callback for each word timing if provided
            if callback is not None and word_timings:
                for start_time, end_time, word in word_timings:
                    callback(word, start_time, end_time)
        except Exception:
            # Fallback to regular synthesis without timings
            self._audio_bytes = self.synth_to_bytes(text, voice)

            # Estimate word timings based on text length
            if callback is not None:
                words = str(text).split()
                total_duration = 0.0  # We don't know the duration

                # Try to get duration from the audio bytes
                try:
                    # Estimate 10 words per second as a fallback
                    total_duration = len(words) / 10.0
                except Exception:
                    pass

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
