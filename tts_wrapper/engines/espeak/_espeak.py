import ctypes
import logging
import queue
import struct
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_char_p,
    c_int,
    c_short,
    c_ubyte,
    c_uint,
    c_void_p,
)
from typing import Any


class EventID(ctypes.Union):
    """Union for event ID in EspeakEvent."""

    _fields_ = [
        ("number", ctypes.c_int),        # Used for WORD and SENTENCE events
        ("name", ctypes.c_char_p),      # Used for MARK and PLAY events
        ("string", ctypes.c_char * 8),  # Used for phoneme names
    ]


class EspeakEvent(Structure):
    """Structure for eSpeak events."""

    _fields_ = [
        ("type", ctypes.c_int),                # Event type (e.g., word, sentence, etc.)
        ("unique_identifier", ctypes.c_uint),  # Message identifier
        ("text_position", ctypes.c_int),       # Start position in the text
        ("length", ctypes.c_int),              # Length of the text segment
        ("audio_position", ctypes.c_int),      # Time in milliseconds within the audio
        ("sample", ctypes.c_int),              # Sample ID (internal use)
        ("user_data", ctypes.c_void_p),        # Pointer supplied by the calling program
        ("id", EventID),                       # Union for event ID
    ]


class EspeakLib:
    """Low-level interface for eSpeak library."""

    EVENT_LIST_TERMINATED = 0
    EVENT_WORD = 1
    EVENT_SENTENCE = 2
    EVENT_MARK = 3
    EVENT_PLAY = 4
    EVENT_END = 5
    EVENT_MSG_TERMINATED = 6
    EVENT_PHONEME = 7
    EVENT_SAMPLERATE = 8

    # Character encoding flags
    CHARS_AUTO = 0     # Automatically detect character encoding
    CHARS_UTF8 = 1     # UTF-8 encoding
    CHARS_8BIT = 2     # ISO-8859 character set
    CHARS_WCHAR = 3    # Wide characters

    # SSML support
    SSML_FLAG = 0x10   # Enable SSML processing

    def __init__(self) -> None:
        """Initialize eSpeak library and load functions."""
        self.dll = self._load_library()
        self._initialize_functions()
        self.synth_callback = None
        self.word_timings = []
        self._initialize_espeak()
        self.generated_audio = bytearray()

    def _load_library(self):
        """Load eSpeak library dynamically."""
        paths = [
            "/opt/homebrew/lib/libespeak-ng.1.dylib",
            "/usr/local/lib/libespeak-ng.1.dylib",
            "/usr/local/lib/libespeak.dylib",
            "libespeak-ng.so.1",
            "/usr/local/lib/libespeak-ng.so.1",
            "libespeak.so.1",
            r"C:\Program Files\eSpeak NG\libespeak-ng.dll",
            r"C:\Program Files (x86)\eSpeak NG\libespeak-ng.dll",
        ]
        for path in paths:
            try:
                return ctypes.cdll.LoadLibrary(path)
            except OSError:
                continue
        msg = "Failed to load eSpeak library."
        raise RuntimeError(msg)

    def _initialize_functions(self) -> None:
        """Bind library functions with proper signatures."""
        self.dll.espeak_Initialize.restype = c_int
        self.dll.espeak_Initialize.argtypes = [c_int, c_int, c_char_p, c_int]

        self.dll.espeak_SetVoiceByName.restype = c_int
        self.dll.espeak_SetVoiceByName.argtypes = [c_char_p]

        self.dll.espeak_SetParameter.restype = c_int
        self.dll.espeak_SetParameter.argtypes = [c_int, c_int, c_int]

        self.dll.espeak_Synth.restype = c_int
        self.dll.espeak_Synth.argtypes = [
            c_char_p, ctypes.c_size_t, c_uint, c_void_p, c_uint, c_uint, c_void_p, c_void_p,
        ]

        self.dll.espeak_SetSynthCallback.restype = None
        self.dll.espeak_SetSynthCallback.argtypes = [CFUNCTYPE(c_int, POINTER(c_short), c_int, POINTER(EspeakEvent))]

        self.dll.espeak_Terminate.restype = c_int

    def _initialize_espeak(self) -> None:
        """Initialize eSpeak with default settings."""
        result = self.dll.espeak_Initialize(1, 500, None, 0)
        if result == -1:
            msg = "Failed to initialize eSpeak library."
            raise RuntimeError(msg)

    def set_voice(self, voice: str) -> None:
        """Set the voice by name."""
        self.dll.espeak_SetVoiceByName(c_char_p(voice.encode("utf-8")))

    def set_rate(self, rate: int) -> None:
        """Set the speech rate."""
        self.dll.espeak_SetParameter(1, rate, 0)

    def set_pitch(self, pitch: int) -> None:
        """Set the pitch."""
        self.dll.espeak_SetParameter(3, pitch, 0)

    def set_volume(self, volume: int) -> None:
        """Set the volume."""
        self.dll.espeak_SetParameter(2, volume, 0)

    def get_available_voices(self) -> list[dict[str, Any]]:
        """Retrieve available voices from eSpeak."""
        # Define the VOICE structure
        class VOICE(Structure):
            _fields_ = [
                ("name", c_char_p),
                ("languages", c_char_p),
                ("identifier", c_char_p),
                ("gender", c_ubyte),
                ("age", c_ubyte),
                ("variant", c_ubyte),
                ("xx1", c_ubyte),
                ("score", c_int),
                ("spare", c_void_p),
            ]

        # Set the return type of espeak_ListVoices
        self.dll.espeak_ListVoices.restype = POINTER(POINTER(VOICE))

        # Call espeak_ListVoices
        voices_ptr = self.dll.espeak_ListVoices(None)
        voices = []

        i = 0
        while voices_ptr[i]:  # Check for NULL terminator
            voice = voices_ptr[i].contents  # Dereference the pointer

            raw_languages = voice.languages.decode("utf-8")
            language_codes = []
            for lang in raw_languages.split("\x05"):
                if lang:
                    language_codes.append(lang.strip())

            voices.append({
                "id": voice.identifier.decode("utf-8") if voice.identifier else voice.name.decode("utf-8"),
                "name": voice.name.decode("utf-8") if voice.name else "unknown",
                "language_codes": language_codes,
                "gender": "Male" if voice.gender == 1 else "Female" if voice.gender == 2 else "Neutral",
                "age": voice.age,
            })
            i += 1

        return voices

    def get_default_voice(self) -> dict[str, Any]:
        """Retrieve the default voice from eSpeak.
        If unavailable, fallback to a known default.
        """
        self.dll.espeak_GetCurrentVoice.restype = POINTER(VOICE)
        current_voice_ptr = self.dll.espeak_GetCurrentVoice()
        if current_voice_ptr and current_voice_ptr.contents.name:
            current_voice = current_voice_ptr.contents
            return {
                "id": current_voice.identifier.decode("utf-8") if current_voice.identifier else current_voice.name.decode("utf-8"),
                "name": current_voice.name.decode("utf-8"),
                "language_codes": [current_voice.languages.decode("utf-8") if current_voice.languages else ""],
                "gender": "male" if current_voice.gender == 1 else "female" if current_voice.gender == 2 else "unknown",
                "age": current_voice.age,
            }
        # Fallback to a known default
        return {
            "id": "gmw/en",
            "name": "English (default)",
            "language_codes": ["en"],
            "gender": "unknown",
            "age": 0,
        }

    def _parse_languages(self, languages: bytes) -> list[str]:
        """Parse language codes from the languages field."""
        lang_list = []
        offset = 0
        while offset < len(languages):
            priority = languages[offset]
            offset += 1
            if priority == 0:  # End of the list
                break
            lang_end = languages.find(b"\x00", offset)
            lang = languages[offset:lang_end].decode("utf-8")
            lang_list.append(lang)
            offset = lang_end + 1
        return lang_list

    def _synth_callback(self, wav, numsamples, events) -> int:
        """Callback function for synthesis events (streaming support)."""
        if numsamples > 0 and wav:
            # Convert 16-bit samples to bytes
            audio_chunk = struct.pack(f"{numsamples}h", *wav[:numsamples])

            # If a streaming queue exists, add the chunk to the queue
            if hasattr(self, "stream_queue") and self.stream_queue is not None:
                self.stream_queue.put(audio_chunk)

        if numsamples == 0 and not events:
            # End of synthesis, signal streaming completion
            if hasattr(self, "stream_queue") and self.stream_queue is not None:
                self.stream_queue.put(None)  # Sentinel to indicate end of streaming

        i = 0
        while True:
            # Process synthesis events (same as before)
            current_event = ctypes.cast(events, POINTER(EspeakEvent))[i]

            if current_event.type == self.EVENT_LIST_TERMINATED:
                break

            if current_event.type == self.EVENT_WORD:
                word = {
                    "start_time": current_event.audio_position / 1000.0,  # Convert ms to seconds
                    "text_position": current_event.text_position,
                    "length": current_event.length,
                }
                self.word_timings.append(word)

            i += 1  # Move to the next event

        return 0

    def speak_streamed(self, text: str, ssml: bool = False) -> None:
        """Speak the given text and stream audio chunks."""
        self.word_timings = []
        self.generated_audio = bytearray()

        # Create a queue for audio chunks
        self.stream_queue = queue.Queue()

        # Start synthesis
        callback_type = CFUNCTYPE(c_int, POINTER(c_short), c_int, POINTER(EspeakEvent))
        self.synth_callback = callback_type(self._synth_callback)
        self.dll.espeak_SetSynthCallback(self.synth_callback)

        flags = self.SSML_FLAG if ssml else self.CHARS_UTF8
        self.dll.espeak_Synth(
            c_char_p(text.encode("utf-8")), len(text) * 2, 0, None, 0, flags, None, None,
        )

    def speak_and_wait(self, text: str, ssml: bool = False) -> None:
        """Speak the given text and wait for it to complete."""
        self.word_timings = [] #clear word timings
        self.generated_audio = bytearray() #clear generated audio
        self.speak(text, ssml=ssml)
        self.dll.espeak_Synchronize()

    def speak(self, text: str, ssml: bool = False) -> None:
        """Speak the given text, with optional SSML support."""
        self.word_timings = [] #clear word timings
        self.generated_audio = bytearray() #clear generated audio
        callback_type = CFUNCTYPE(c_int, POINTER(c_short), c_int, POINTER(EspeakEvent))
        self.synth_callback = callback_type(self._synth_callback)
        self.dll.espeak_SetSynthCallback(self.synth_callback)

        flags = self.SSML_FLAG if ssml else self.CHARS_UTF8
        self.dll.espeak_Synth(
            c_char_p(text.encode("utf-8")), len(text) * 2, 0, None, 0, flags, None, None,
        )

    def speak_debug(self, text: str, ssml: bool = False) -> None:
        """Speak text with detailed debugging of positions."""
        logging.debug("Input Text: %s", text)
        words = text.split()
        for idx, word in enumerate(words):
            logging.debug(f"Word {idx}: '{word}', Start Position={text.find(word)}, Length={len(word)}")

        self.speak(text, ssml=ssml)

    def terminate(self) -> None:
        """Terminate the eSpeak library."""
        self.dll.espeak_Terminate()


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    espeak = EspeakLib()
    espeak.set_voice("en")
    espeak.set_rate(150)
    espeak.set_pitch(50)
    espeak.set_volume(80)

    logging.debug("SSML Example:")
    espeak.speak_and_wait("<speak>Hello, <mark name='pause'/> world!</speak>", ssml=True)

    logging.debug("\nPlain Text Example:")
    espeak.speak_and_wait("Hello, this is a plain text example.")

    logging.debug("\nSpeak Debug:")
    espeak.speak_debug("Hello world, this is a test.", ssml=False)
    espeak.terminate()
