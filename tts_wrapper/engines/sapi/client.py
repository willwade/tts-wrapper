import comtypes.client
import logging
import os
import platform
import math
import weakref
from queue import Queue
from threading import Thread
from typing import Any, List, Tuple, Union
from .ssml import SAPISSML
import re
import comtypes
import winreg
from comtypes import COMMETHOD, HRESULT, IUnknown, GUID, windll, WinError
from ctypes import POINTER, c_void_p, c_wchar_p, c_ulong, c_int

SAPI4_CLSID = "{179F3D56-1B0B-42B2-A962-59B7EF59FE1B}"
SAPI5_CLSID = "SAPI.SpVoice"

def check_architecture_match(dll_path):
    """
    Check if the DLL matches the Python interpreter's architecture.
    """
    python_arch = platform.architecture()[0]
    dll_arch = "32-bit" if "x86" in dll_path.lower() else "64-bit"
    if ("64" in python_arch and dll_arch == "32-bit") or ("32" in python_arch and dll_arch == "64-bit"):
        raise OSError(f"Architecture mismatch: Python is {python_arch}, but DLL is {dll_arch}.")

class ISpVoice(comtypes.IUnknown):
    _iid_ = GUID("{EEE78591-FE22-11D0-8BEF-0060081841DE}")
    _methods_ = [
        COMMETHOD([], HRESULT, "SetOutput", ([], c_void_p, "pUnkOutput"), ([], c_int, "fAllowFormatChanges")),
        COMMETHOD([], HRESULT, "GetOutputObjectToken", ([], POINTER(c_void_p), "ppObjectToken")),
        COMMETHOD([], HRESULT, "Speak", ([], c_wchar_p, "pwcs"), ([], c_ulong, "dwFlags"), ([], POINTER(c_ulong), "pulStreamNumber")),
        COMMETHOD([], HRESULT, "Pause"),
        COMMETHOD([], HRESULT, "Resume"),
    ]

class UnsupportedPlatformError(Exception):
    """Exception raised when the platform is unsupported."""
    pass

def find_sapi4_dll_path() -> str:
    """
    Locates and returns the path to the SAPI 4 DLL (speech.dll).
    Returns:
        str: Full path to the SAPI 4 DLL.
    """
    sapi4_path = os.path.join(os.getenv("WINDIR"), "Speech", "speech.dll")
    if not os.path.exists(sapi4_path):
        raise FileNotFoundError("SAPI 4 speech.dll not found in C:\\Windows\\Speech.")
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
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ) as key:
            clsid, _ = winreg.QueryValueEx(key, None)  # Default value contains the CLSID
            return clsid
    except FileNotFoundError:
        raise Exception("SAPI 4 CLSID not found in the registry. Ensure SAPI 4 is installed.")

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
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ):
            print(f"CLSID {clsid} is registered.")
    except FileNotFoundError:
        raise Exception(f"CLSID {clsid} is not registered. Ensure SAPI 4 is installed.")

    try:
        # Check or set AppID
        appid_key_path = f"SOFTWARE\\Classes\\AppID\\{appid}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path, 0, winreg.KEY_READ):
            print(f"AppID {appid} is already configured.")
    except FileNotFoundError:
        # Create AppID key and set DllSurrogate
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path) as appid_key:
            winreg.SetValueEx(appid_key, "DllSurrogate", 0, winreg.REG_SZ, "")
            print(f"AppID {appid} configured with DllSurrogate.")

    # Link CLSID to AppID
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_SET_VALUE) as clsid_key:
        winreg.SetValueEx(clsid_key, "AppID", 0, winreg.REG_SZ, appid)
        print(f"CLSID {clsid} linked to AppID {appid}.")

    # Register speech.dll as the COM server
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"speech.dll not found at {dll_path}.")
    try:
        os.system(f'regsvr32 /s "{dll_path}"')
        print(f"{dll_path} registered successfully.")
    except Exception as e:
        raise Exception(f"Failed to register {dll_path}: {e}")

    print("SAPI 4 surrogacy setup completed.")

class SAPIClient:
    def __init__(self, sapi_version: int = 5):
        """
        Initialize the SAPI client for SAPI4 or SAPI5.
        Args:
            sapi_version (int): SAPI version to use (4 or 5).
        """
        if platform.system() != "Windows":
            raise UnsupportedPlatformError("SAPI is only supported on Windows.")
        comtypes.CoInitialize()
        self._ssml = SAPISSML()
        if sapi_version == 4:
            try:
                clsid = 'A910187F-0C7A-45AC-92CC-59EDAFB77B53'
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
                raise Exception(f"Error initializing SAPI 4: {e}")
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
        else:
            raise NotImplementedError("Events are not supported for SAPI 4.")

    def get_voices(self) -> List[dict[str, Any]]:
        """
        Retrieve available voices.
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
                "age": int(voice.GetAttribute("Age")) if voice.GetAttribute("Age") else 0,
            }
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
            raise KeyError(f"Unknown property: {name}")

    def synth(self, ssml: str) -> Tuple[bytes, List[dict]]:
        """
        Synthesize SSML into audio and return raw data with word timings.
        Args:
            ssml (str): SSML-formatted text to synthesize.
        Returns:
            Tuple[bytes, List[dict]]: Audio bytes and word timing metadata.
        """
        logging.debug("SAPI synthesis to bytes started.")
        audio_queue = Queue()
        word_timings = []
        if not self._is_ssml(ssml):
            ssml = self._convert_to_ssml(ssml)

        def audio_writer():
            comtypes.CoInitialize()
            format = comtypes.client.CreateObject("SAPI.SpAudioFormat")
            format.Type = 34  # SAFT44kHz16BitMono
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            stream.Format = format
            #print(f"stream format: {stream.Format.Type}")
            self._tts.AudioOutputStream = stream
            self._tts.Speak(ssml)

            audio_queue.put(stream.GetData())

        thread = Thread(target=audio_writer)
        thread.start()
        thread.join()

        audio_tuple = audio_queue.get()
        audio_bytes = bytes(audio_tuple)

        logging.debug("SAPI synthesis completed.")
        return audio_bytes, word_timings

    def _is_ssml(self, text: str) -> bool:
        return bool(re.match(r"^\s*<speak>", text, re.IGNORECASE))

    def _convert_to_ssml(self, text: str) -> str:
        words = text.split()
        ssml_parts = ["<speak>"]
        for i, word in enumerate(words):
            ssml_parts.append(f'<mark name="word{i}"/>{word}')
        ssml_parts.append("</speak>")
        return " ".join(ssml_parts)


    def synth_streaming(self, ssml: str) -> Tuple[Queue, List[dict]]:
        """
        Stream synthesis and return a queue for audio and word timings.
        Args:
            ssml (str): SSML-formatted text to synthesize.
        Returns:
            Tuple[Queue, List[dict]]: Audio queue and word timing metadata.
        """

        comtypes.CoInitialize()
        logging.debug("SAPI streaming synthesis started.")
        audio_queue = Queue()
        word_timings = []
        
        if not self._is_ssml(ssml):
            ssml = self._convert_to_ssml(ssml)

        def audio_writer():
            stream = comtypes.client.CreateObject("SAPI.SpMemoryStream")
            self._tts.AudioOutputStream = stream
            self._tts.Speak(ssml)
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