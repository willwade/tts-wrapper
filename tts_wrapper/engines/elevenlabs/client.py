import base64
import json

import requests

from tts_wrapper.exceptions import ModuleNotInstalled

audio_format = ("pcm_22050",)


class ElevenLabsClient:
    def __init__(self, credentials) -> None:
        if not credentials:
            msg = "An API key for ElevenLabs must be provided"
            raise ValueError(msg)
        # Extract the API key from credentials tuple
        self.api_key = credentials[0] if isinstance(credentials, tuple) else credentials
        self.base_url = "https://api.elevenlabs.io"

    def synth(
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
