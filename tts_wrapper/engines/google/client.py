import struct
from typing import Any, Dict, List, Optional, Union

from google.cloud import texttospeech_v1beta1 as texttospeech
from google.oauth2 import service_account

from tts_wrapper.exceptions import ModuleNotInstalled


class GoogleClient:
    def __init__(self, credentials: Union[str, Dict]) -> None:
        """Initialize the GoogleClient with credentials. Accepts either a file path or a dictionary.

        :param credentials: The credentials for Google Cloud, can be a file path (str) or a dictionary.
        """
        self._credentials = credentials
        self._client = None
        self._voice = None
        self._lang = None

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

    def set_voice(self, voice: str, lang: str) -> None:
        """Sets the voice and language for the client.

        :param voice: The name of the voice to use.
        :param lang: The language code (e.g., 'en-US').
        """
        self._voice = voice
        self._lang = lang

    def synth(
        self,
        ssml: str,
        voice: Optional[str] = None,
        lang: Optional[str] = None,
        include_timepoints: bool = False,
    ) -> Dict[str, Any]:
        self._initialize_client()

        s_input = self.texttospeech.SynthesisInput(ssml=ssml)
        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=lang or self._lang, name=voice or self._voice,
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

    def get_audio_duration(self, audio_content: bytes) -> float:
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


    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Google Cloud Text-to-Speech service."""
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
