from typing import Optional, Tuple, Dict, List, Any

from ...engines.utils import process_wav
from ...exceptions import ModuleNotInstalled
import json
import io

Credentials = Tuple[str, str, str]

FORMATS = {
    "wav": "pcm",
    "mp3": "mp3",
}


class PollyClient:
    def __init__(
        self,
        credentials: Optional[Credentials] = None,
    ) -> None:
        try:
            import boto3
        except ImportError:
            boto3 = None  # type: ignore
            raise ModuleNotInstalled("boto3")

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
        self._client = boto_session.client("polly")

    def synth(self, ssml: str, voice: str, format: str) -> bytes:
        raw = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat=FORMATS[format],
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
        )["AudioStream"].read()

        if format == "wav":
            return process_wav(raw)
        else:
            return raw

    def synth_with_timings(self, ssml: str, voice: str, format: str) -> Tuple[bytes, List[Tuple[float, str]]]:
            audio_data, word_timings = self._synth_with_marks(ssml, voice, format)
            return audio_data, word_timings

    def _synth_with_marks(self, ssml: str, voice: str, format: str) -> Tuple[bytes, List[Tuple[float, str]]]:
        # Get speech marks
        marks_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat='json',
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
            SpeechMarkTypes=['word']
        )
        
        speech_marks_str = marks_response['AudioStream'].read().decode('utf-8')
        speech_marks_lines = speech_marks_str.splitlines()
        speech_marks = [json.loads(line) for line in speech_marks_lines]
        word_timings = [(float(mark['time']) / 1000, mark['value']) for mark in speech_marks if mark['type'] == 'word']

        # Get audio data
        audio_response = self._client.synthesize_speech(
            Engine="neural",
            OutputFormat=FORMATS[format],
            VoiceId=voice,
            TextType="ssml",
            Text=ssml,
        )
        
        audio_data = audio_response["AudioStream"].read()
        
        if format == "wav":
            audio_data = process_wav(audio_data)

        return audio_data, word_timings


    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Amazon Polly."""
        response = self._client.describe_voices()
        voices = response.get('Voices', [])
        standardized_voices = []
        for voice in voices:
            voice['id'] = voice['Id']
            voice['language_codes'] = [voice['LanguageCode']]
            voice['name'] = voice['Name']
            voice['gender'] = voice['Gender']
            standardized_voices.append(voice)
        return standardized_voices
