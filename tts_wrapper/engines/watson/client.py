from typing import Tuple, List, Dict, Any
import requests
import websocket
import threading
import json
import logging

from ...exceptions import ModuleNotInstalled

try:
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator  # type: ignore
    from ibm_watson import TextToSpeechV1  # type: ignore
except ImportError:
    IAMAuthenticator = None
    TextToSpeechV1 = None

Credentials = Tuple[str, str, str, str]  # api_key, api_url, region, instance_id

FORMATS = {"wav": "audio/wav", "mp3": "audio/mp3"}


class WatsonClient:
    def __init__(self, credentials: Credentials) -> None:
        if IAMAuthenticator is None or TextToSpeechV1 is None:
            raise ModuleNotInstalled("ibm-watson")
        api_key, region, instance_id = credentials
        client = TextToSpeechV1(authenticator=IAMAuthenticator(api_key))
        api_url = f"https://api.{region}.text-to-speech.watson.cloud.ibm.com/"
        client.set_service_url(api_url)
        self._client = client
        # Now websocket part
        response = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "apikey": api_key,
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.iam_token = response.json()["access_token"]
        # Construct the WebSocket URL
        self.ws_url = f"wss://api.{region}.text-to-speech.watson.cloud.ibm.com/instances/{instance_id}/v1/synthesize"
        self.word_timings = []

    # The old method
    def synth(self, ssml: str, voice: str, format: str) -> bytes:
        return (
            self._client.synthesize(text=str(ssml), voice=voice, accept=FORMATS[format])
            .get_result()
            .content
        )
    # The new method. gets timings. Only for websockets. Sadly we need both systems because you cant get voices with websockets
    def synth_with_timings(self, ssml: str, voice: str, format: str) -> bytes:
        audio_data = []

        def on_message(ws, message):
            if isinstance(message, bytes):
                # This is a part of the audio data
                audio_data.append(message)
            else:
                # This is a JSON message with the word timings
                data = json.loads(message)
                if 'words' in data:
                    self.word_timings.extend([(timing[2], timing[0]) for timing in data['words']])

        def on_open(ws):
            message = {
                'text': ssml,
                'accept': FORMATS[format],
                'voice': voice,
                'timings': ['words']
            }
            try:
                ws.send(json.dumps(message))
            except Exception as e:
                logging.error(f"Error sending message: {e}")

        def on_error(ws, error):
            logging.error(f"WebSocket error: {error}")

        def on_close(ws, status_code, reason):
            logging.info(f"WebSocket closed with status code: {status_code}, reason: {reason}")

        ws = websocket.WebSocketApp(self.ws_url + f"?access_token={self.iam_token}&voice={voice}", on_message=on_message, on_open=on_open, on_error=on_error, on_close=on_close)

        wst = threading.Thread(target=ws.run_forever)
        try:
            wst.daemon = True
            wst.start()
            # Wait for the WebSocket thread to finish
            wst.join()
            # Join the audio data parts together to get the complete audio data
            return b''.join(audio_data)
        except Exception as e:
            logging.error(f"Error in WebSocket thread: {e}")
            return b''
        finally:
            ws.close()

    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from IBM Watson TTS service."""
        voice_data = self._client.list_voices().get_result()
        voices = voice_data["voices"]
        standardized_voices = []
        for voice in voices:
            standardized_voice = {}
            standardized_voice['id'] = voice['name']
            standardized_voice['language_codes'] = [voice['language']]
            standardized_voice['name'] = voice['name'].split('_')[1].replace('V3Voice', '')
            standardized_voice['gender'] = voice['gender']
            standardized_voices.append(standardized_voice)
        return standardized_voices
