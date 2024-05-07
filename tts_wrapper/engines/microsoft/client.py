from typing import List, Dict, Any, Optional

from tts_wrapper.tts import FileFormat

from ...exceptions import ModuleNotInstalled

try:
    import requests
except ImportError:
    requests = None  # type: ignore

FORMATS = {
    "wav": "riff-24khz-16bit-mono-pcm",
    "mp3": "audio-24khz-160kbitrate-mono-mp3",
}

# Other formats from MS
# amr-wb-16000hz
# audio-16khz-16bit-32kbps-mono-opus
# audio-16khz-32kbitrate-mono-mp3
# audio-16khz-64kbitrate-mono-mp3
# audio-16khz-128kbitrate-mono-mp3
# audio-24khz-16bit-24kbps-mono-opus
# audio-24khz-16bit-48kbps-mono-opus
# audio-24khz-48kbitrate-mono-mp3
# audio-24khz-96kbitrate-mono-mp3
# audio-24khz-160kbitrate-mono-mp3
# audio-48khz-96kbitrate-mono-mp3
# audio-48khz-192kbitrate-mono-mp3
# ogg-16khz-16bit-mono-opus
# ogg-24khz-16bit-mono-opus
# ogg-48khz-16bit-mono-opus
# raw-8khz-8bit-mono-alaw
# raw-8khz-8bit-mono-mulaw
# raw-8khz-16bit-mono-pcm
# raw-16khz-16bit-mono-pcm
# raw-16khz-16bit-mono-truesilk
# raw-22050hz-16bit-mono-pcm
# raw-24khz-16bit-mono-pcm
# raw-24khz-16bit-mono-truesilk
# raw-44100hz-16bit-mono-pcm
# raw-48khz-16bit-mono-pcm
# webm-16khz-16bit-mono-opus
# webm-24khz-16bit-24kbps-mono-opus
# webm-24khz-16bit-mono-opus

class MicrosoftClient:
    @property
    @classmethod
    def supported_formats(cls) -> List[FileFormat]:
        return ["wav", "mp3"]

    def __init__(
        self, credentials: str, region: Optional[str] = None, verify_ssl=True
    ) -> None:
        if requests is None:
            raise ModuleNotInstalled("requests")

        self._credentials = credentials
        self._region = region or "eastus"

        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._session.headers["Content-Type"] = "application/ssml+xml"

    def _fetch_access_token(self) -> str:
        fetch_token_url = (
            f"https://{self._region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        )
        headers = {"Ocp-Apim-Subscription-Key": self._credentials}
        response = requests.post(fetch_token_url, headers=headers)
        return str(response.text)

    def synth(self, ssml: str, format: FileFormat) -> bytes:
        self._session.headers["X-Microsoft-OutputFormat"] = FORMATS[format]

        if "Authorization" not in self._session.headers:
            access_token = self._fetch_access_token()
            self._session.headers["Authorization"] = "Bearer " + access_token

        response = self._session.post(
            f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1",
            data=ssml.encode("utf-8"),
        )

        if response.status_code != 200:
            error_message = f"Failed to synthesize speech: {response.status_code} - {response.reason}"
            if response.content:
                error_details = response.json().get('error', {}).get('message', 'No error details available.')
                error_message += f" Details: {error_details}"
            print(error_message)
            raise Exception(error_message)
        return response.content

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Makes an API call to retrieve available voices."""
        url = f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        response = self._session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch voices, status code: {response.status_code}")