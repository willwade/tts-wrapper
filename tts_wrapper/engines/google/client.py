from typing import List, Dict, Any, Tuple
from ...exceptions import ModuleNotInstalled
import struct

class GoogleClient:
    def __init__(self, credentials: str) -> None:
        self._credentials_file = credentials
        self._client = None

    def _initialize_client(self):
        if self._client is None:
            try:
                from google.cloud import texttospeech_v1beta1 as texttospeech
                from google.oauth2 import service_account
                self.texttospeech = texttospeech
                self.service_account = service_account

                self.FORMATS = {
                    "wav": texttospeech.AudioEncoding.LINEAR16,
                    "mp3": texttospeech.AudioEncoding.MP3,
                }

                self._client = texttospeech.TextToSpeechClient(
                    credentials=self.service_account.Credentials.from_service_account_file(
                        self._credentials_file
                    )
                )
            except ImportError:
                raise ModuleNotInstalled("google-cloud-texttospeech")

            if not self._credentials_file:
                raise ValueError("credentials file is required")

    def synth(self, ssml: str, voice: str, lang: str, format: str, include_timepoints: bool = False) -> Dict[str, Any]:
        self._initialize_client()

        s_input = self.texttospeech.SynthesisInput(ssml=ssml)
        voice_params = self.texttospeech.VoiceSelectionParams(language_code=lang, name=voice)
        audio_config = self.texttospeech.AudioConfig(audio_encoding=self.FORMATS[format])

        if include_timepoints:
            timepoints = [self.texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
        else:
            timepoints = []

        resp = self._client.synthesize_speech(
            request=self.texttospeech.SynthesizeSpeechRequest(
                input=s_input,
                voice=voice_params,
                audio_config=audio_config,
                enable_time_pointing=timepoints,
            )
        )

        result = {
            "audio_content": resp.audio_content,
        }
        
        if include_timepoints:
            result["timepoints"] = [{"markName": tp.mark_name, "timeSeconds": tp.time_seconds} for tp in resp.timepoints]

        return result

    def get_audio_duration(self, audio_content: bytes, format: str) -> float:
        if format == "wav":
            # Parse WAV header to get sample rate and number of samples
            riff, size, fformat = struct.unpack('<4sI4s', audio_content[:12])
            if riff != b'RIFF' or fformat != b'WAVE':
                raise ValueError("Not a WAV file")
            
            subchunk1, subchunk1_size = struct.unpack('<4sI', audio_content[12:20])
            if subchunk1 != b'fmt ':
                raise ValueError("Not a valid WAV file")
            
            aformat, channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack('HHIIHH', audio_content[20:36])
            
            subchunk2, subchunk2_size = struct.unpack('<4sI', audio_content[36:44])
            if subchunk2 != b'data':
                raise ValueError("Not a valid WAV file")
            
            num_samples = subchunk2_size // (channels * (bits_per_sample // 8))
            duration = num_samples / sample_rate
            
            return duration
        elif format == "mp3":
            # For MP3, we'd need to use a library like mutagen to get the duration
            # For simplicity, we'll estimate based on file size and bitrate
            # Assume a bitrate of 128 kbps
            bitrate = 128 * 1024
            duration = len(audio_content) * 8 / bitrate
            return duration
        else:
            raise ValueError(f"Unsupported format: {format}")

        
    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from Google Cloud Text-to-Speech service."""
        self._initialize_client()

        response = self._client.list_voices()
        voices = response.voices  # Assuming this returns a list of voice objects
        standardized_voices = []
        for voice in voices:
            voice_data = voice.__dict__  # or convert to dict if not already one
            voice_data['id'] = voice.name
            voice_data['language_codes'] = voice.language_codes
            voice_data['name'] = voice.name
            voice_data['gender'] = voice.ssml_gender
            if voice.ssml_gender == 1:
                voice_data['gender'] = "Male"
            elif voice.ssml_gender == 2:
                voice_data['gender'] = "Female"
            elif voice.ssml_gender == 3:
                voice_data['gender'] = "Neutral"
            else:
                voice_data['gender'] = "Unknown"
            standardized_voices.append(voice_data)
        return standardized_voices
