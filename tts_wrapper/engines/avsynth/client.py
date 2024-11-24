import ctypes
import logging
import queue
from typing import Any, List, Dict, Tuple


class AVSynthClient:
    """Client interface for the AVSynth TTS engine."""

    def __init__(self, dylib_path: str = "./SpeechBridge.dylib") -> None:
        """Initialize the AVSynth library client."""
        self.lib = ctypes.cdll.LoadLibrary(dylib_path)
        logging.debug("AVSynth client initialized")

        # Define function signatures
        self.lib.synthToBytes.argtypes = [
            ctypes.c_char_p,  # text
            ctypes.c_bool,  # is_ssml
            ctypes.CFUNCTYPE(None, ctypes.c_char_p),  # word_callback
            ctypes.CFUNCTYPE(None, ctypes.c_char_p),  # log_callback
        ]
        self.lib.synthToBytes.restype = ctypes.POINTER(ctypes.c_uint8)

        self.lib.getVoices.argtypes = []
        self.lib.getVoices.restype = ctypes.c_char_p

        self.lib.setVoice.argtypes = [ctypes.c_char_p]
        self.lib.setVoice.restype = None

    def synth(self, ssml: str, voice: str) -> Tuple[bytes, List[Dict]]:
        """Synthesize speech using AVSynth and return raw audio and word timings."""
        word_timings = []

        def word_callback(word_data_ptr):
            if word_data_ptr:
                word_data = ctypes.cast(word_data_ptr, ctypes.c_char_p).value.decode("utf-8")
                word_timings.append(word_data)

        def log_callback(log_message_ptr):
            if log_message_ptr:
                log_message = ctypes.cast(log_message_ptr, ctypes.c_char_p).value.decode("utf-8")
                logging.debug(f"AVSynth Log: {log_message}")

        # Set voice
        self.lib.setVoice(voice.encode("utf-8"))

        # Synthesize
        result_ptr = self.lib.synthToBytes(
            ssml.encode("utf-8"),
            True,  # is_ssml
            ctypes.CFUNCTYPE(None, ctypes.c_char_p)(word_callback),
            ctypes.CFUNCTYPE(None, ctypes.c_char_p)(log_callback),
        )

        if result_ptr:
            metadata_ptr = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_int))
            length = metadata_ptr[0]

            audio_data_ptr = ctypes.addressof(result_ptr.contents) + ctypes.sizeof(ctypes.c_int)
            audio_data = ctypes.string_at(audio_data_ptr, length)
            return audio_data, word_timings
        else:
            logging.error("Synthesis failed.")
            return b"", []

    def synth_streaming(self, ssml: str, voice: str) -> Tuple[queue.Queue, List[Dict]]:
        """Stream synthesis using AVSynth and return a queue and word timings."""
        word_timings = []
        audio_queue = queue.Queue()

        def word_callback(word_data_ptr):
            if word_data_ptr:
                word_data = ctypes.cast(word_data_ptr, ctypes.c_char_p).value.decode("utf-8")
                word_timings.append(word_data)

        def log_callback(log_message_ptr):
            if log_message_ptr:
                log_message = ctypes.cast(log_message_ptr, ctypes.c_char_p).value.decode("utf-8")
                logging.debug(f"AVSynth Log: {log_message}")

        # Set voice
        self.lib.setVoice(voice.encode("utf-8"))

        # Streaming logic (if supported by the AVSynth library)
        raise NotImplementedError("Streaming synthesis is not yet implemented.")

        return audio_queue, word_timings

    def get_voices(self) -> List[Dict[str, Any]]:
        """Fetches available voices from AVSynth."""
        voices_json_ptr = self.lib.getVoices()
        if voices_json_ptr:
            voices_json = ctypes.cast(voices_json_ptr, ctypes.c_char_p).value.decode("utf-8")
            return [
                {"id": voice["id"], "name": voice["name"], "language_codes": voice["language_codes"]}
                for voice in voices_json
            ]
        else:
            logging.error("Failed to fetch voices.")
            return []