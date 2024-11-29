import asyncio
import requests
import certifi
import logging
from typing import Any, List
import ssl
import aiohttp
import time

from ._constants import SEC_MS_GEC_VERSION, VOICE_LIST, WSS_HEADERS, WSS_URL
from ._drm import DRM
from ._typing import TTSChunk, Voice
import uuid


class EdgeTTSClient:
    """Client for Microsoft Edge TTS API."""

    def __init__(
        self,
        proxy: str | None = None,
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
    ):
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        if proxy is not None and not isinstance(proxy, str):
            raise TypeError(f"proxy must be a string or None, got {type(proxy).__name__}")
        self.proxy = proxy

    def _connect_id(self) -> str:
        """
        Generate a unique connection ID as a UUID without dashes.

        Returns:
            str: A unique connection ID.
        """
        return str(uuid.uuid4()).replace("-", "")

    def date_to_string(self) -> str:
        """
        Return Javascript-style date string.

        Returns:
            str: Javascript-style date string.
        """
        # %Z is not what we want, but it's the only way to get the timezone
        # without having to use a library. We'll just use UTC and hope for the best.
        # For example, right now %Z would return EEST when we need it to return
        # Eastern European Summer Time.
        return time.strftime(
            "%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)", time.gmtime()
        )


    def ssml_headers_plus_data(self,request_id: str, timestamp: str, ssml: str) -> str:
        """
        Returns the headers and data to be used in the request.

        Returns:
            str: The headers and data to be used in the request.
        """

        return (
            f"X-RequestId:{request_id}\r\n"
            "Content-Type:application/ssml+xml\r\n"
            f"X-Timestamp:{timestamp}Z\r\n"  # This is not a mistake, Microsoft Edge bug.
            "Path:ssml\r\n\r\n"
            f"{ssml}"
        )

    def split_text_by_byte_length(self, text: str, max_size: int) -> List[str]:
        """Splits text into chunks that fit within the specified byte size."""
        text_bytes = text.encode("utf-8")
        chunks = []
        while len(text_bytes) > max_size:
            split_at = text_bytes.rfind(b" ", 0, max_size)
            if split_at == -1:
                split_at = max_size
            chunks.append(text_bytes[:split_at].decode("utf-8"))
            text_bytes = text_bytes[split_at:].lstrip()
        chunks.append(text_bytes.decode("utf-8"))
        return chunks

    def calc_max_mesg_size(self, voice: str) -> int:
        """
        Calculates the maximum message size for the given voice, rate, pitch, and volume.

        Args:
            voice (str): The voice ID.
            rate (str): The speaking rate.
            volume (str): The volume level.
            pitch (str): The pitch level.
        
        Returns:
            int: The maximum message size in bytes.
        """
        websocket_max_size = 2 ** 16  # Example WebSocket size limit: 64KB
        ssml_example = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{voice}">
                    <prosody pitch="{self.pitch}" rate="{self.rate}" volume="{self.volume}">
                        Hello, this is a sample message to calculate size.
                    </prosody>
                </voice>
            </speak>
        """
        overhead_per_message = len(
            f"X-RequestId:{uuid.uuid4().hex}\r\n"
            f"Content-Type:application/ssml+xml\r\n"
            f"X-Timestamp:{time.strftime('%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)', time.gmtime())}Z\r\n"
            f"Path:ssml\r\n\r\n"
            f"{ssml_example}"
        )
        return websocket_max_size - overhead_per_message

    async def synth(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech using WebSocket via aiohttp."""
        if not isinstance(ssml, str):
            ssml = str(ssml)

        max_size = self.calc_max_mesg_size(voice)
        chunks = self.split_text_by_byte_length(ssml, max_size)
        
        url = f"{WSS_URL}&Sec-MS-GEC={DRM.generate_sec_ms_gec()}&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}&ConnectionId={self._connect_id()}"
        logging.info("Starting WebSocket synthesis...")
        logging.debug(f"WebSocket URL: {url}")

        audio_data = bytearray()
        metadata = []

        try:
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url, headers=WSS_HEADERS, ssl=ssl_ctx) as websocket:
                    logging.info("WebSocket connection established.")

                    # Command Request
                    command_request = (
                        f"X-Timestamp:{self.date_to_string()}\r\n"
                        "Content-Type:application/json; charset=utf-8\r\n"
                        "Path:speech.config\r\n\r\n"
                        '{"context":{"synthesis":{"audio":{"metadataoptions":{'
                        '"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"},'
                        '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}\r\n'
                    )
                    await websocket.send_str(command_request)
                    logging.info("Command request sent.")

                    # Send SSML Chunks
                    for chunk in chunks:
                        logging.debug(f"Sending chunk: {chunk[:50]}... ({len(chunk.encode('utf-8'))} bytes)")
                        ssml_request = self.ssml_headers_plus_data(
                            self._connect_id(), self.date_to_string(), chunk
                        )
                        await websocket.send_str(ssml_request)

                    # Receive Responses
                    async for message in websocket:
                        if message.type == aiohttp.WSMsgType.TEXT:
                            logging.debug(f"Text message: {message.data}")
                            # Handle metadata if applicable
                        elif message.type == aiohttp.WSMsgType.BINARY:
                            audio_data.extend(message.data)
                        elif message.type == aiohttp.WSMsgType.CLOSE:
                            logging.warning("WebSocket connection closed.")
                            break
                        else:
                            logging.warning(f"Unexpected message type: {message.type}")

            logging.info("WebSocket synthesis complete.")
        except Exception as e:
            logging.exception("Error during WebSocket synthesis")
            raise

        return bytes(audio_data), metadata


    def get_voices(self) -> List[dict[str, Any]]:
            """Synchronously retrieve a list of available voices."""
            url = f"{VOICE_LIST}&Sec-MS-GEC={DRM.generate_sec_ms_gec()}&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}"
            headers = WSS_HEADERS
            proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

            logging.info("Fetching voices synchronously...")
            logging.debug(f"Request URL: {url}")
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
                logging.info(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    logging.error(f"Failed to fetch voices: {response.status_code} {response.reason}")
                    response.raise_for_status()

                voices = response.json()
                logging.debug(f"Voices data: {voices}")
                return [
                    {
                        "id": voice["ShortName"],
                        "name": voice["FriendlyName"],
                        "language_codes": [voice["Locale"]],
                        "gender": voice["Gender"],
                        "age": 0,  # Default age
                    }
                    for voice in voices
                ]
            except Exception as e:
                logging.exception("Exception occurred while fetching voices")
                raise e