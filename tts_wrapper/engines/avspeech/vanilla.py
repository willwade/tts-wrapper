import ctypes

speech_bridge = ctypes.CDLL("./SpeechBridge.dylib")
result = speech_bridge.synthesizeSpeech(
    b"Hello, this is a test.", b"./output.wav"
)

if result == 0:
    print("Audio saved to output.wav")
else:
    print("Failed to synthesize speech")