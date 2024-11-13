import json
from typing import Any, Optional

from tts_wrapper.engines.utils import process_wav
from tts_wrapper.exceptions import ModuleNotInstalled

Credentials = tuple[str, str, str]

FORMATS = {
    "wav": "pcm",
    "mp3": "mp3",
}


class PollyClient:
    def __init__(
        self,
        credentials: Optional[Credentials] = None,
        verify_ssl: bool = True,
    ) -> None:
        try:
            import boto3
        except ImportError:
            msg = "boto3"
            raise ModuleNotInstalled(msg)

        from boto3.session import Session

        if credentials is None:
            boto_session = Session()
        else:
            region, aws_key_id, aws_access_key = credentials
            boto_session = Session(
                aws_access_key_id=aws_key_id,
                aws_secret_access_key=aws_access_key,
                region_name=region,
            )
        self._client = boto_session.client("polly", verify=verify_ssl)

    def synth(self, ssml: str, voice: str) -> bytes:
        raw = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="pcm",
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
        )["AudioStream"].read()

        return process_wav(raw)

    def synth_with_timings(
        self, ssml: str, voice: str,
    ) -> tuple[bytes, list[tuple[float, str]]]:
        audio_data, word_timings = self._synth_with_marks(ssml, voice)
        return audio_data, word_timings

    def _synth_with_marks(
        self, ssml: str, voice: str,
    ) -> tuple[bytes, list[tuple[float, str]]]:
        # Get speech marks
        marks_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="json",
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
            SpeechMarkTypes=["word"],
        )

        speech_marks_str = marks_response["AudioStream"].read().decode("utf-8")
        speech_marks_lines = speech_marks_str.splitlines()
        speech_marks = [json.loads(line) for line in speech_marks_lines]
        word_timings = [
            (float(mark["time"]) / 1000, mark["value"])
            for mark in speech_marks
            if mark["type"] == "word"
        ]

        # Get audio data
        audio_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat="pcm",
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
        )

        audio_data = audio_response["AudioStream"].read()

        audio_data = process_wav(audio_data)

        return audio_data, word_timings

    def get_voices(self) -> list[dict[str, Any]]:
        """Fetches available voices from Amazon Polly."""
        response = self._client.describe_voices()
        voices = response.get("Voices", [])
        standardized_voices = []
        for voice in voices:
            voice["id"] = voice["Id"]
            voice["language_codes"] = [voice["LanguageCode"]]
            voice["name"] = voice["Name"]
            voice["gender"] = voice["Gender"]
            standardized_voices.append(voice)
        return standardized_voices
