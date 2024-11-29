import asyncio
import requests
import logging
from typing import Any, List

import aiohttp

from ._constants import SEC_MS_GEC_VERSION, VOICE_LIST, WSS_HEADERS, WSS_URL
from ._drm import DRM
from ._typing import TTSChunk, Voice
import uuid


class EdgeTTSClient:
    """Client for Microsoft Edge TTS API."""

    def __init__(self, proxy: str | None = None):
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

    async def synth(self, ssml: str, voice: str) -> tuple[bytes, list[dict]]:
        """Synthesize speech using WebSocket via aiohttp."""
        url = f"{WSS_URL}&Sec-MS-GEC={DRM.generate_sec_ms_gec()}&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}&ConnectionId={self._connect_id()}"
        logging.info("Starting WebSocket synthesis...")
        logging.debug(f"WebSocket URL: {url}")

        audio_data = bytearray()
        metadata = []

        try:
            async with aiohttp.ClientSession() as session:
                logging.info("Opening WebSocket connection...")
                async with session.ws_connect(url, headers=WSS_HEADERS) as websocket:
                    # Send SSML request
                    logging.info("Sending SSML to WebSocket...")
                    await websocket.send_str(ssml)
                    logging.info("SSML sent successfully.")

                    # Handle responses
                    async for message in asyncio.wait_for(websocket, timeout=30):
                        logging.info(f"Received message of type: {message.type}")
                        if message.type == aiohttp.WSMsgType.TEXT:
                            logging.debug(f"Received text message: {message.data}")
                            if is_metadata_message(message.data):  # Replace with logic
                                metadata.append(parse_metadata(message.data))
                        elif message.type == aiohttp.WSMsgType.BINARY:
                            logging.debug(f"Received binary audio chunk: {len(message.data)} bytes")
                            audio_data.extend(message.data)
                        elif message.type == aiohttp.WSMsgType.CLOSE:
                            logging.info("WebSocket connection closed")
                            break
                        else:
                            logging.warning(f"Unexpected WebSocket message type: {message.type}")

                    logging.info("WebSocket synthesis complete")
        except Exception as e:
            logging.exception("Error during WebSocket synthesis")
            raise

        return bytes(audio_data), metadata

    async def synth_streaming(self, ssml: str, voice: str) -> tuple[bytes, list[TTSChunk]]:
        """Synthesize speech and return audio and word timing metadata."""
        async with aiohttp.ClientSession() as session, session.ws_connect(
            f"{WSS_URL}&Sec-MS-GEC={DRM.generate_sec_ms_gec()}"
            f"&Sec-MS-GEC-Version={SEC_MS_GEC_VERSION}",
            headers=WSS_HEADERS,
            proxy=self.proxy,
        ) as ws:
                await ws.send_str(ssml)

                audio_data = bytearray()
                metadata = []
                async for message in ws:
                    if message.type == aiohttp.WSMsgType.BINARY:
                        audio_data.extend(message.data)
                    elif message.type == aiohttp.WSMsgType.TEXT:
                        try:
                            parsed_message: TTSChunk = message.json()
                            metadata.append(parsed_message)
                        except ValueError:
                            continue
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