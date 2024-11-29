import comtypes.client
import logging
import math
import weakref
from queue import Queue
from threading import Thread
from typing import Any, List, Tuple, Union

SAPI4_CLSID = "{EEE78591-FE22-11D0-8BEF-0060081841DE}"
SAPI5_CLSID = "SAPI.SpVoice"


class SAPIClient:
    def __init__(self, sapi_version: int = 5):
        """
        Initialize the SAPI client for SAPI4 or SAPI5.
        Args:
            sapi_version (int): SAPI version to use (4 or 5).
        """
        if sapi_version == 4:
            self._tts = comtypes.client.CreateObject(SAPI4_CLSID)
        elif sapi_version == 5:
            self._tts = comtypes.client.CreateObject(SAPI5_CLSID)
        else:
            raise ValueError("Unsupported SAPI version. Use 4 or 5.")
        self._sapi_version = sapi_version
        self._event_sink = None
        self._initialize_events()

    def _initialize_events(self):
        """Bind events to the TTS engine for real-time updates."""
        if self._sapi_version == 5:
            self._event_sink = SAPI5EventSink(self)
            self._advise = comtypes.client.GetEvents(self._tts, self._event_sink)

    def get_voices(self) -> List[dict[str, Any]]:
        """
        Retrieve available voices.
        Returns:
            List[dict]: A list of voices with metadata.
        """
        voices = self._tts.GetVoices()
        return [
            {"id": voice.Id, "name": voice.GetDescription()}
            for voice in voices
        ]

    def set_voice(self, voice_id: str) -> None:
        """
        Set the active voice by ID.
        Args:
            voice_id (str): The ID of the voice to set.
        """
        for voice in self._tts.GetVoices():
            if voice.Id == voice_id:
                self._tts.Voice = voice
                return
        raise ValueError(f"Voice with ID {voice_id} not found.")

    def set_property(self, name: str, value: Union[str, int, float]) -> None:
        """
        Set a property for the TTS engine.
        Args:
            name (str): Property name ('rate', 'volume', etc.).
            value: Property value.
        """
        if name == "rate":
            self._tts.Rate = int(math.log(value / 130.0, 1.0))
        elif name == "volume":
            self._tts.Volume = int(value * 100)
        else:
            raise KeyError(f"Unknown property: {name}")

    def synth(self, text: str) -> Tuple[bytes, List[dict]]:
        """
        Synthesize text into audio and return raw data with word timings.
        Args:
            text (str): Text to synthesize.
        Returns:
            Tuple[bytes, List[dict]]: Audio bytes and word timing metadata.
        """
        logging.debug("SAPI synthesis to bytes started.")
        audio_queue = Queue()
        word_timings = []

        def audio_writer():
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            self._tts.AudioOutputStream = stream
            self._tts.Speak(text)
            audio_queue.put(stream.GetData())

        thread = Thread(target=audio_writer)
        thread.start()
        thread.join()

        audio_bytes = audio_queue.get()
        logging.debug("SAPI synthesis completed.")
        return audio_bytes, word_timings

    def synth_streaming(self, text: str) -> Tuple[Queue, List[dict]]:
        """
        Stream synthesis and return a queue for audio and word timings.
        Args:
            text (str): Text to synthesize.
        Returns:
            Tuple[Queue, List[dict]]: Audio queue and word timing metadata.
        """
        logging.debug("SAPI streaming synthesis started.")
        audio_queue = Queue()
        word_timings = []

        def audio_writer():
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            self._tts.AudioOutputStream = stream
            self._tts.Speak(text)
            audio_queue.put(stream.GetData())
            audio_queue.put(None)  # End of stream marker

        thread = Thread(target=audio_writer)
        thread.start()
        return audio_queue, word_timings


class SAPI5EventSink:
    def __init__(self, driver):
        self._driver = weakref.proxy(driver)

    def StartStream(self, stream_number, stream_position):
        logging.debug(f"Stream started: {stream_number}, Position: {stream_position}")

    def EndStream(self, stream_number, stream_position):
        logging.debug(f"Stream ended: {stream_number}, Position: {stream_position}")

    def Word(self, stream_number, stream_position, character_position, length):
        logging.debug(
            f"Word event: Stream {stream_number}, Position {stream_position}, "
            f"Char Position {character_position}, Length {length}"
        )