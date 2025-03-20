import json
import logging
import struct
import threading
from typing import Any

from tts_wrapper.exceptions import ModuleNotInstalled

Credentials = tuple[str, str, str]  # api_key, region, instance_id

# FORMATS = {"wav": "audio/wav", "mp3": "audio/mp3"}


class WatsonClient:
    def __init__(
        self,
        credentials: Credentials,
        disableSSLVerification: bool = False,
    ) -> None:
        self.api_key, self.region, self.instance_id = credentials
        self.disableSSLVerification = disableSSLVerification

        self._client = None
        self.iam_token = None
        self.ws_url = None
        self.word_timings = []

        self._initialize_ibm_watson()

    def _initialize_ibm_watson(self) -> None:
        if self._client is None:
            try:
                import requests
                from ibm_cloud_sdk_core.authenticators import (
                    IAMAuthenticator,  # type: ignore
                )
                from ibm_watson import TextToSpeechV1  # type: ignore

                self.IAMAuthenticator = IAMAuthenticator
                self.TextToSpeechV1 = TextToSpeechV1
                self.requests = requests
            except ImportError:
                msg = "ibm-watson"
                raise ModuleNotInstalled(msg)

            authenticator = self.IAMAuthenticator(self.api_key)
            self._client = self.TextToSpeechV1(authenticator=authenticator)
            api_url = f"https://api.{self.region}.text-to-speech.watson.cloud.ibm.com/"
            self._client.set_service_url(api_url)
            if self.disableSSLVerification:
                self._client.set_disable_ssl_verification(True)
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Get IAM token
            response = self.requests.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "apikey": self.api_key,
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self.iam_token = response.json()["access_token"]

            # Construct the WebSocket URL
            self.ws_url = f"wss://api.{self.region}.text-to-speech.watson.cloud.ibm.com/instances/{self.instance_id}/v1/synthesize"

    def synth(self, ssml: str, voice: str) -> bytes:
        self._initialize_ibm_watson()
        return (
            self._client.synthesize(text=str(ssml), voice=voice, accept="audio/wav")
            .get_result()
            .content
        )

    def synth_with_timings(self, ssml: str, voice: str) -> bytes:
        self._initialize_ibm_watson()
        audio_data = []
        self.word_timings = []

        def on_message(ws, message) -> None:
            if isinstance(message, bytes):
                audio_data.append(message)
            else:
                data = json.loads(message)
                if "words" in data:
                    self.word_timings.extend(
                        [(float(timing[2]), timing[0]) for timing in data["words"]],
                    )

        def on_open(ws) -> None:
            message = {
                "text": ssml,
                "accept": "audio/wav",
                "voice": voice,
                "timings": ["words"],
            }
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logging.exception("Error sending message: %s", e)

        def on_error(ws, error) -> None:
            logging.error("WebSocket error: %s", error)

        def on_close(ws, status_code, reason) -> None:
            logging.info(
                f"WebSocket closed with status code: {status_code}, reason: {reason}",
            )

        import websocket

        ws = websocket.WebSocketApp(
            self.ws_url + f"?access_token={self.iam_token}&voice={voice}",
            on_message=on_message,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close,
        )

        wst = threading.Thread(target=ws.run_forever)
        try:
            wst.daemon = True
            wst.start()
            wst.join()
            return b"".join(audio_data)

        except Exception as e:
            logging.exception("Error in WebSocket thread: %s", e)
            return b""
        finally:
            ws.close()

    def get_audio_duration(self, audio_content: bytes) -> float:
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

    def get_voices(self) -> list[dict[str, Any]]:
        self._initialize_ibm_watson()
        voice_data = self._client.list_voices().get_result()
        voices = voice_data["voices"]
        standardized_voices = []
        for voice in voices:
            standardized_voice = {
                "id": voice["name"],
                "language_codes": [voice["language"]],
                "name": voice["name"].split("_")[1].replace("V3Voice", ""),
                "gender": voice["gender"],
            }
            standardized_voices.append(standardized_voice)
        return standardized_voices
