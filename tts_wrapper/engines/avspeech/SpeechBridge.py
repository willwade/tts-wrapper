import ctypes
from ctypes import c_char_p, c_bool, POINTER, c_uint8, c_int
import wave
import struct
import json

# Load the SpeechBridge dynamic library
lib = ctypes.cdll.LoadLibrary("./SpeechBridge.dylib")

# Define function signatures for logging and callbacks
log_callback_type = ctypes.CFUNCTYPE(None, c_char_p)
word_callback_type = ctypes.CFUNCTYPE(None, c_char_p)
byte_callback_type = ctypes.CFUNCTYPE(None, c_uint8, c_int)

def log_callback(log_message_ptr):
    if log_message_ptr:
        log_message = ctypes.cast(log_message_ptr, ctypes.c_char_p).value.decode("utf-8")
        print(f"DEBUG LOG: {log_message}")

def word_timing_callback(word_timings_ptr):
    if word_timings_ptr:
        word_timings_json = ctypes.cast(word_timings_ptr, c_char_p).value.decode("utf-8")
        print("Word Timings JSON:", word_timings_json)
    else:
        print("No word timings received.")

def byte_callback(data_ptr, length):
    """Handle audio data chunks for streaming synthesis."""
    chunk = ctypes.string_at(data_ptr, length)
    print(f"Received audio chunk of size: {len(chunk)}")
    with open("output_stream.wav", "ab") as f:
        f.write(chunk)

# Instantiate callbacks
log_callback = log_callback_type(log_callback)
word_callback = word_callback_type(word_timing_callback)
byte_callback = byte_callback_type(byte_callback)

# Define TTSManager functionality
class TTSManager:
    @staticmethod
    def set_voice(voice_identifier):
        """Set the voice by its identifier."""
        lib.setVoice.argtypes = [c_char_p]
        lib.setVoice.restype = None
        lib.setVoice(voice_identifier.encode("utf-8"))

    @staticmethod
    def get_voice():
        """Get the current voice identifier."""
        lib.getVoice.argtypes = []
        lib.getVoice.restype = c_char_p
        voice_ptr = lib.getVoice()
        if voice_ptr:
            return ctypes.cast(voice_ptr, c_char_p).value.decode("utf-8")
        return None

    @staticmethod
    def get_voices():
        """Get all available voices as a JSON string."""
        lib.getVoices.argtypes = []
        lib.getVoices.restype = c_char_p
        voices_ptr = lib.getVoices()
        if voices_ptr:
            voices_json = ctypes.cast(voices_ptr, ctypes.c_char_p).value.decode("utf-8")
            return json.loads(voices_json)
        return []

# Define synthesis functionality
class Synthesizer:
    @staticmethod
    def synthesize_to_bytes(text, is_ssml=False, streaming=False, byte_callback=byte_callback, word_callback=word_callback, log_callback=log_callback):
        """Synthesize text into audio bytes."""
        # Update the argtypes to match the updated Swift function
        lib.synthToBytes.argtypes = [
            c_char_p,  # Text
            c_bool,    # isSSML
            c_bool,    # Streaming flag
            byte_callback_type,  # Byte callback (optional)
            word_callback_type,  # Word callback
            log_callback_type,   # Log callback
        ]
        lib.synthToBytes.restype = POINTER(c_uint8)

        if streaming and not byte_callback:
            raise ValueError("streaming=True requires a byte_callback.")

        result_ptr = lib.synthToBytes(
            text.encode("utf-8"), is_ssml, streaming, byte_callback, word_callback, log_callback
        )
        if streaming:
            print("Streaming synthesis started.")
            return None, None

        if result_ptr:
            metadata_ptr = ctypes.cast(result_ptr, POINTER(c_int))
            length = metadata_ptr[0]

            # Get audio data
            audio_data_ptr = ctypes.addressof(result_ptr.contents) + ctypes.sizeof(c_int)
            audio_data = ctypes.string_at(audio_data_ptr, length)

            # Assume a fixed sample rate
            sample_rate = 22050
            return audio_data, sample_rate
        else:
            print("No audio data received or synthesis failed.")
            return None, None

    @staticmethod
    def save_wav(filename, audio_data, sample_rate=16000, channels=1, sample_width=2):
        """Save audio bytes as a WAV file."""
        num_samples = len(audio_data) // sample_width
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',  # Chunk ID
            36 + len(audio_data),  # Chunk Size
            b'WAVE',  # Format
            b'fmt ',  # Subchunk1 ID
            16,  # Subchunk1 Size (PCM)
            1,  # Audio Format (1 = PCM)
            channels,  # Number of channels
            sample_rate,  # Sample rate
            sample_rate * channels * sample_width,  # Byte rate
            channels * sample_width,  # Block align
            sample_width * 8,  # Bits per sample
            b'data',  # Subchunk2 ID
            len(audio_data)  # Subchunk2 Size
        )

        with open(filename, "wb") as wav_file:
            wav_file.write(header)
            wav_file.write(audio_data)

# Example usage
if __name__ == "__main__":
    # Voice Management
    print("Available Voices:")
    for voice in TTSManager.get_voices():
        print(f"ID: {voice['id']}, Name: {voice['name']}, Language: {voice['language']}")

    current_voice = TTSManager.get_voice()
    print(f"Current Voice: {current_voice}")

    # Set a new voice
    TTSManager.set_voice("com.apple.ttsbundle.siri_Aaron_en-US_compact")
    print(f"Updated Voice: {TTSManager.get_voice()}")

    # Synthesize text - on streaming
    text = "Hello, this is a test synthesis."
    audio_data, sample_rate = Synthesizer.synthesize_to_bytes(text, streaming=False)

    if audio_data:
        print(f"Audio data received, length: {len(audio_data)}, sample rate: {sample_rate}")
        Synthesizer.save_wav("output.wav", audio_data, sample_rate)
        print("Audio saved to output.wav")