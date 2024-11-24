import ctypes
from ctypes import c_char_p, c_bool, POINTER, c_uint8, c_int
import wave
import struct

# Load the SpeechBridge dynamic library
lib = ctypes.cdll.LoadLibrary("./SpeechBridge.dylib")

# Define the function signature for synthToBytes
lib.synthToBytes.argtypes = [c_char_p, c_bool, ctypes.CFUNCTYPE(None, c_char_p), ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_char)) ]
lib.synthToBytes.restype = POINTER(c_uint8)



def log_callback(log_message_ptr):
    if log_message_ptr:
        log_message = ctypes.cast(log_message_ptr, ctypes.c_char_p).value.decode("utf-8")
        print(f"DEBUG LOG: {log_message}")

log_callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_char))(log_callback)

def word_timing_callback(word_timings_ptr):
    if word_timings_ptr:
        word_timings_json = ctypes.cast(word_timings_ptr, c_char_p).value.decode("utf-8")
        print("Word Timings JSON:", word_timings_json)
    else:
        print("No word timings received.")

word_callback = ctypes.CFUNCTYPE(None, c_char_p)(word_timing_callback)

# Call the Swift function
text = "Hello, this is a test synthesis."
result_ptr = lib.synthToBytes(text.encode("utf-8"), False, word_callback, log_callback)

if result_ptr:
    # Extract length and audio data
    length_ptr = ctypes.cast(result_ptr, POINTER(c_int))
    length = length_ptr.contents.value

    # Get the address of the buffer and extract audio data
    audio_data_ptr = ctypes.addressof(result_ptr.contents) + ctypes.sizeof(c_int)
    audio_data = ctypes.string_at(audio_data_ptr, length)

    print(f"Audio data received, length: {length}")

    # Save the audio data as a WAV file
    def save_wav(filename, audio_data, sample_rate=16000, channels=1, sample_width=2):
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

    save_wav("output.wav", audio_data)
    print("Audio saved to output.wav")
else:
    print("No audio data received or synthesis failed.")