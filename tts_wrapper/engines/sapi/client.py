from __future__ import annotations

import logging
import math
import os
import platform
import re
import weakref
import winreg
from ctypes import POINTER, c_int, c_ulong, c_void_p, c_wchar_p
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable

import comtypes
import comtypes.client
from comtypes import COMMETHOD, GUID, HRESULT, windll

from tts_wrapper.engines.utils import (
    estimate_word_timings,  # Import the timing estimation function
)
from tts_wrapper.tts import AbstractTTS

from .ssml import SAPISSML

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

SAPI4_CLSID = "{179F3D56-1B0B-42B2-A962-59B7EF59FE1B}"
SAPI5_CLSID = "SAPI.SpVoice"


def check_architecture_match(dll_path):
    """
    Check if the DLL matches the Python interpreter's architecture.
    """
    python_arch = platform.architecture()[0]
    dll_arch = "32-bit" if "x86" in dll_path.lower() else "64-bit"
    if ("64" in python_arch and dll_arch == "32-bit") or (
        "32" in python_arch and dll_arch == "64-bit"
    ):
        msg = f"Architecture mismatch: Python is {python_arch}, but DLL is {dll_arch}."
        raise OSError(msg)


class ISpVoice(comtypes.IUnknown):
    _iid_ = GUID("{EEE78591-FE22-11D0-8BEF-0060081841DE}")
    _methods_ = [
        COMMETHOD(
            [],
            HRESULT,
            "SetOutput",
            ([], c_void_p, "pUnkOutput"),
            ([], c_int, "fAllowFormatChanges"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "GetOutputObjectToken",
            ([], POINTER(c_void_p), "ppObjectToken"),
        ),
        COMMETHOD(
            [],
            HRESULT,
            "Speak",
            ([], c_wchar_p, "pwcs"),
            ([], c_ulong, "dwFlags"),
            ([], POINTER(c_ulong), "pulStreamNumber"),
        ),
        COMMETHOD([], HRESULT, "Pause"),
        COMMETHOD([], HRESULT, "Resume"),
    ]


class UnsupportedPlatformError(Exception):
    """Exception raised when the platform is unsupported."""


def find_sapi4_dll_path() -> str:
    """
    Locates and returns the path to the SAPI 4 DLL (speech.dll).
    Returns:
        str: Full path to the SAPI 4 DLL.
    """
    sapi4_path = os.path.join(os.getenv("WINDIR"), "Speech", "speech.dll")
    if not os.path.exists(sapi4_path):
        msg = "SAPI 4 speech.dll not found in C:\\Windows\\Speech."
        raise FileNotFoundError(msg)
    return sapi4_path


def find_sapi4_clsid() -> str:
    """
    Locates and returns the CLSID for SAPI 4 by searching the registry.
    Returns:
        str: The CLSID of the SAPI 4 COM object.
    """
    try:
        # Registry path for SAPI 4 (may vary based on installation)
        clsid_key_path = r"SOFTWARE\Classes\SAPI4\CLSID"

        # Open the registry key
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ
        ) as key:
            clsid, _ = winreg.QueryValueEx(
                key, None
            )  # Default value contains the CLSID
            return clsid
    except FileNotFoundError:
        msg = "SAPI 4 CLSID not found in the registry. Ensure SAPI 4 is installed."
        raise Exception(msg)


def get_appid_for_clsid(clsid):
    try:
        registry_path = f"CLSID\\{clsid}\\AppID"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, registry_path) as key:
            appid, _ = winreg.QueryValueEx(key, None)  # Default value of the key
            return appid
    except FileNotFoundError:
        return None


def configure_sapi4_surrogacy(clsid: str, appid: str, dll_path: str) -> None:
    """
    Configures COM surrogacy for SAPI 4 if not already set up.

    Args:
        clsid (str): The CLSID of the SAPI 4 COM object.
        appid (str): The AppID for the COM object.
        dll_path (str): Full path to the speech.dll.
    """
    try:
        # Check if CLSID is registered
        clsid_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}"
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ
        ):
            print(f"CLSID {clsid} is registered.")
    except FileNotFoundError:
        msg = f"CLSID {clsid} is not registered. Ensure SAPI 4 is installed."
        raise Exception(msg)

    try:
        # Check or set AppID
        appid_key_path = f"SOFTWARE\\Classes\\AppID\\{appid}"
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, appid_key_path, 0, winreg.KEY_READ
        ):
            print(f"AppID {appid} is already configured.")
    except FileNotFoundError:
        # Create AppID key and set DllSurrogate
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path) as appid_key:
            winreg.SetValueEx(appid_key, "DllSurrogate", 0, winreg.REG_SZ, "")
            print(f"AppID {appid} configured with DllSurrogate.")

    # Link CLSID to AppID
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_SET_VALUE
    ) as clsid_key:
        winreg.SetValueEx(clsid_key, "AppID", 0, winreg.REG_SZ, appid)
        print(f"CLSID {clsid} linked to AppID {appid}.")

    # Register speech.dll as the COM server
    if not os.path.exists(dll_path):
        msg = f"speech.dll not found at {dll_path}."
        raise FileNotFoundError(msg)
    try:
        os.system(f'regsvr32 /s "{dll_path}"')
        print(f"{dll_path} registered successfully.")
    except Exception as e:
        msg = f"Failed to register {dll_path}: {e}"
        raise Exception(msg)

    print("SAPI 4 surrogacy setup completed.")


class SAPIClient(AbstractTTS):
    def __init__(self, sapi_version: int = 5):
        """
        Initialize the SAPI client for SAPI4 or SAPI5.
        Args:
            sapi_version (int): SAPI version to use (4 or 5).
        """
        super().__init__()
        if platform.system() != "Windows":
            msg = "SAPI is only supported on Windows."
            raise UnsupportedPlatformError(msg)
        comtypes.CoInitialize()
        self.ssml = SAPISSML()
        self.audio_rate = 16000  # Default sample rate for SAPI
        if sapi_version == 4:
            try:
                clsid = "A910187F-0C7A-45AC-92CC-59EDAFB77B53"
                dll_path = find_sapi4_dll_path()  # Find DLL path

                # Configure COM surrogacy (if needed)
                appid = get_appid_for_clsid(clsid)
                if appid:
                    print(f"AppID for CLSID {clsid} is {appid}")
                else:
                    print(f"No AppID found for CLSID {clsid}")
                configure_sapi4_surrogacy(clsid, appid, dll_path)

                # Load the DLL explicitly
                self._dll = windll.LoadLibrary(dll_path)
                # Load SAPI 4 speech.dll using windll
            except Exception as e:
                msg = f"Error initializing SAPI 4: {e}"
                raise Exception(msg)
        elif sapi_version == 5:
            self._tts = comtypes.client.CreateObject(SAPI5_CLSID)
        else:
            msg = "Unsupported SAPI version. Use 4 or 5."
            raise ValueError(msg)
        self._sapi_version = sapi_version
        self._event_sink = None
        self._initialize_events()

        # Set default voice
        if self._sapi_version == 5:
            try:
                # Get the first available voice
                voices = self._tts.GetVoices()
                if voices and voices.Count > 0:
                    self._tts.Voice = voices.Item(0)
                    logging.info(
                        f"Set default voice: {voices.Item(0).GetDescription()}"
                    )
            except Exception as e:
                logging.warning(f"Failed to set default voice: {e}")

    def _initialize_events(self):
        """Bind events to the TTS engine for real-time updates."""
        if self._sapi_version == 5:
            self._event_sink = SAPI5EventSink(self)
            self._advise = comtypes.client.GetEvents(self._tts, self._event_sink)
        else:
            msg = "Events are not supported for SAPI 4."
            raise NotImplementedError(msg)

    def get_voices(self, langcodes: str = "bcp47") -> list[dict[str, Any]]:
        """
        Retrieve available voices.

        Args:
            langcodes: Format for language codes (not used in SAPI)

        Returns:
            List[dict]: A list of voices with metadata.
        """
        voices = self._tts.GetVoices()
        return [
            {
                "id": voice.Id,
                "name": voice.GetDescription(),
                "language_codes": [voice.GetAttribute("Language")],
                "gender": voice.GetAttribute("Gender"),
                "age": (
                    int(voice.GetAttribute("Age")) if voice.GetAttribute("Age") else 0
                ),
            }
            for voice in voices
        ]

    def set_voice(self, voice_id: str, lang: str | None = None) -> None:
        """
        Set the active voice by ID.

        Args:
            voice_id: The ID of the voice to set
            lang: Optional language code (not used in SAPI)
        """
        for voice in self._tts.GetVoices():
            if voice.Id == voice_id:
                self._tts.Voice = voice
                return
        msg = f"Voice with ID {voice_id} not found."
        raise ValueError(msg)

    def set_property(self, name: str, value: str | float) -> None:
        print("property set")
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
            msg = f"Unknown property: {name}"
            raise KeyError(msg)

    def synth_raw(self, text: str) -> tuple[bytes, list[dict]]:
        """
        Synthesize text into audio and return raw data with word timings.

        Args:
            text: Text to synthesize

        Returns:
            Tuple[bytes, List[dict]]: Audio bytes and word timing metadata
        """
        logging.debug("SAPI synthesis to bytes started.")
        audio_queue: Queue = Queue()

        # Convert to SSML if needed
        if not self._is_ssml(text):
            text = self._convert_to_ssml(text)

        def audio_writer():
            comtypes.CoInitialize()
            format = comtypes.client.CreateObject("SAPI.SpAudioFormat")
            format.Type = 34  # SAFT44kHz16BitMono
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            stream.Format = format
            self._tts.AudioOutputStream = stream
            self._tts.Speak(text)

            audio_queue.put(stream.GetData())

        thread = Thread(target=audio_writer)
        thread.start()
        thread.join()

        audio_tuple = audio_queue.get()
        audio_bytes = bytes(audio_tuple)

        logging.debug("SAPI synthesis completed.")

        # Estimate word timings based on text
        word_timings = estimate_word_timings(text)

        return audio_bytes, word_timings

    def synth_to_bytes(self, text: Any, voice_id: str | None = None) -> bytes:
        """
        Transform written text to audio bytes.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis

        Returns:
            Raw audio bytes
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        # Get audio data with word timings
        audio_bytes, _ = self.synth_raw(str(text))
        return audio_bytes

    def synth(
        self,
        text: Any,
        output_file: str | Path,
        output_format: str = "wav",
        voice_id: str | None = None,
    ) -> None:
        """
        Synthesize text to audio and save to a file.

        Args:
            text: The text to synthesize
            output_file: Path to save the audio file
            output_format: Format to save as (only "wav" is supported)
            voice_id: Optional voice ID to use for this synthesis
        """
        # Check format
        if output_format.lower() != "wav":
            msg = f"Unsupported format: {output_format}. Only 'wav' is supported."
            raise ValueError(msg)

        # Get audio bytes
        audio_bytes = self.synth_to_bytes(text, voice_id)

        # Save to file
        with open(output_file, "wb") as f:
            f.write(audio_bytes)

    def synth_to_bytestream(
        self, text: Any, voice_id: str | None = None, format: str = "wav"
    ) -> Generator[bytes, None, None]:
        """Synthesizes text to an in-memory bytestream and yields audio data chunks.

        Args:
            text: The text to synthesize
            voice_id: Optional voice ID to use for this synthesis
            format: The desired audio format (e.g., 'wav', 'mp3', 'flac')

        Returns:
            A generator yielding bytes objects containing audio data
        """
        import io

        # Generate the full audio content
        audio_content = self.synth_to_bytes(text, voice_id)

        # Create a BytesIO object from the audio content
        audio_stream = io.BytesIO(audio_content)

        # Define chunk size (adjust as needed)
        chunk_size = 4096  # 4KB chunks

        # Yield chunks of audio data
        while True:
            chunk = audio_stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def _is_ssml(self, text: str) -> bool:
        return bool(re.match(r"^\s*<speak>", text, re.IGNORECASE))

    def _convert_to_ssml(self, text: str) -> str:
        words = text.split()
        ssml_parts = ["<speak>"]
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="word{i}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)

    def connect(self, event_name: str, callback: Callable[[], None]) -> None:
        """Connect a callback to an event.

        Args:
            event_name: Name of the event to connect to (e.g., 'onStart', 'onEnd')
            callback: Function to call when the event occurs
        """
        if not hasattr(self, "_callbacks"):
            self._callbacks = {}
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        self._callbacks[event_name].append(callback)

    def start_playback_with_callbacks(
        self, text: str, callback: Callable | None = None, voice_id: str | None = None
    ) -> None:
        """Start playback with word timing callbacks.

        Args:
            text: The text to synthesize
            callback: Function to call for each word timing
            voice_id: Optional voice ID to use for this synthesis
        """
        # Set voice if provided
        if voice_id:
            self.set_voice(voice_id)

        # Trigger onStart callbacks
        if hasattr(self, "_callbacks") and "onStart" in self._callbacks:
            for cb in self._callbacks["onStart"]:
                cb()

        # Get audio bytes and word timings
        audio_bytes, word_timings = self.synth_raw(str(text))

        # Call the callback for each word timing if provided
        if callback is not None:
            for timing in word_timings:
                if isinstance(timing, tuple) and len(timing) == 3:
                    # Tuple format: (word, start_time, end_time)
                    callback(timing[0], timing[1], timing[2])
                elif (
                    isinstance(timing, dict)
                    and "word" in timing
                    and "start" in timing
                    and "end" in timing
                ):
                    # Dict format: {"word": word, "start": start_time, "end": end_time}
                    callback(timing["word"], timing["start"], timing["end"])

        # Trigger onEnd callbacks
        if hasattr(self, "_callbacks") and "onEnd" in self._callbacks:
            for cb in self._callbacks["onEnd"]:
                cb()

    def synth_streaming(self, ssml: str) -> tuple[Queue, list[dict]]:
        """
        Stream synthesis and return a queue for audio and word timings.
        Args:
            ssml (str): SSML-formatted text to synthesize.
        Returns:
            Tuple[Queue, List[dict]]: Audio queue and word timing metadata.
        """
        print("start sapi synth_streaming")
        comtypes.CoInitialize()
        logging.debug("SAPI streaming synthesis started.")
        audio_queue = Queue()
        word_timings = []

        if not self._is_ssml(ssml):
            ssml = self._convert_to_ssml(ssml)

        word_timings = estimate_word_timings(ssml)

        def audio_writer():
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            self._tts.AudioOutputStream = stream
            # self._tts.Speak(ssml)
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
