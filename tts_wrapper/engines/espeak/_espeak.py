import ctypes
from ctypes import POINTER, c_int, c_short, c_uint, c_void_p, c_char_p, CFUNCTYPE, Structure
from ctypes.util import find_library
import logging

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

    def __init__(self):
        """Initialize eSpeak library and load functions."""
        self.dll = self._load_library()
        self._initialize_functions()
        self.synth_callback = None
        self.word_timings = []
        self._initialize_espeak()

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
        raise RuntimeError("Failed to load eSpeak library.")

    def _initialize_functions(self):
        """Bind library functions with proper signatures."""
        self.dll.espeak_Initialize.restype = c_int
        self.dll.espeak_Initialize.argtypes = [c_int, c_int, c_char_p, c_int]

        self.dll.espeak_SetVoiceByName.restype = c_int
        self.dll.espeak_SetVoiceByName.argtypes = [c_char_p]

        self.dll.espeak_SetParameter.restype = c_int
        self.dll.espeak_SetParameter.argtypes = [c_int, c_int, c_int]

        self.dll.espeak_Synth.restype = c_int
        self.dll.espeak_Synth.argtypes = [
            c_char_p, ctypes.c_size_t, c_uint, c_void_p, c_uint, c_uint, c_void_p, c_void_p
        ]

        self.dll.espeak_SetSynthCallback.restype = None
        self.dll.espeak_SetSynthCallback.argtypes = [CFUNCTYPE(c_int, POINTER(c_short), c_int, POINTER(EspeakEvent))]

        self.dll.espeak_Terminate.restype = c_int

    def _initialize_espeak(self):
        """Initialize eSpeak with default settings."""
        result = self.dll.espeak_Initialize(1, 500, None, 0)
        if result == -1:
            raise RuntimeError("Failed to initialize eSpeak library.")

    def set_voice(self, voice: str):
        """Set the voice by name."""
        self.dll.espeak_SetVoiceByName(c_char_p(voice.encode("utf-8")))

    def set_rate(self, rate: int):
        """Set the speech rate."""
        self.dll.espeak_SetParameter(1, rate, 0)

    def set_pitch(self, pitch: int):
        """Set the pitch."""
        self.dll.espeak_SetParameter(3, pitch, 0)

    def set_volume(self, volume: int):
        """Set the volume."""
        self.dll.espeak_SetParameter(2, volume, 0)

    def _synth_callback(self, wav, numsamples, events) -> int:
        """Callback function for synthesis events."""
        if numsamples == 0 and not events:
            return 0  # Synthesis completed.

        i = 0
        while True:
            # Access the event at index `i`
            current_event = ctypes.cast(events, POINTER(EspeakEvent))[i]

            logging.debug(f"Event: type={current_event.type}, text_position={current_event.text_position}, "
                f"length={current_event.length}, audio_position={current_event.audio_position}, "
                f"unique_id={current_event.unique_identifier}")
            if current_event.type == self.EVENT_LIST_TERMINATED:
                break

            if current_event.type == self.EVENT_WORD:
                word = {
                    "start_time": current_event.audio_position / 1000.0,  # Convert ms to seconds
                    "text_position": current_event.text_position,
                    "length": current_event.length,
                }
                logging.debug(
                    f"Word Event: text_position={current_event.text_position}, "
                    f"length={current_event.length}, audio_position={current_event.audio_position}"
                )
                self.word_timings.append(word)
            elif current_event.type == self.EVENT_SENTENCE:
                logging.debug(f"Sentence Event: text_position={current_event.text_position}")
            elif current_event.type == self.EVENT_MARK:
                # Handle MARK events
                mark_name = current_event.id.name.decode("utf-8") if current_event.id.name else "Unnamed Mark"
                logging.debug(f"Mark Event: id={current_event.id.name.decode('utf-8') if current_event.id.name else 'Unnamed'}")
            elif current_event.type == self.EVENT_PHONEME:
                # Handle PHONEME events
                phoneme = current_event.id.string.decode("utf-8")
                logging.debug(f"Phoneme Event: phoneme={current_event.id.string.decode('utf-8')}")

            i += 1  # Move to the next event

        return 0

    def speak_and_wait(self, text: str, ssml: bool = False):
        """Speak the given text and wait for it to complete."""
        self.word_timings = [] #clear word timings
        self.speak(text, ssml=ssml)
        self.dll.espeak_Synchronize()

    def speak(self, text: str, ssml: bool = False):
        """Speak the given text, with optional SSML support."""
        self.word_timings = [] #clear word timings
        callback_type = CFUNCTYPE(c_int, POINTER(c_short), c_int, POINTER(EspeakEvent))
        self.synth_callback = callback_type(self._synth_callback)
        self.dll.espeak_SetSynthCallback(self.synth_callback)

        flags = self.SSML_FLAG if ssml else self.CHARS_UTF8
        self.dll.espeak_Synth(
            c_char_p(text.encode("utf-8")), len(text) * 2, 0, None, 0, flags, None, None
        )

    def speak_debug(self, text: str, ssml: bool = False):
        """Speak text with detailed debugging of positions."""
        logging.debug("Input Text: %s", text)
        words = text.split()
        for idx, word in enumerate(words):
            logging.debug(f"Word {idx}: '{word}', Start Position={text.find(word)}, Length={len(word)}")

        self.speak(text, ssml=ssml)

    def terminate(self):
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