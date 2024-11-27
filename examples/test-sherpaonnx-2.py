import logging
from pathlib import Path

from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS

client = SherpaOnnxClient(model_path=None, tokens_path=None, model_id=None)

# Initialize the SherpaOnnxTTS engine with the client
tts = SherpaOnnxTTS(client=client)

tts.set_output_device(2)

# Retrieve and display available voices
voices = tts.get_voices()
logging.info(f"Available voices: {voices}")

# Set the desired voice using its ISO code
#iso_code = "eng"  # Replace with a valid ISO code from the voices list
tts.set_voice()
#logging.info(f"Voice set to ISO code: {iso_code}")

# Define the text to be synthesized
text = (
"Title: The Silent Truth "
"The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace. "
)
logging.info(f"Text to synthesize: {text}")

# Specify the output file and format
output_file = "output_streamed.wav"  # Change to 'output_streamed.mp3' or other formats as needed
audio_format = "wav"  # Supported formats: 'wav', 'mp3', 'flac'

# # # pausng
try:
    ssml_text = tts.ssml.add(text)
    tts.speak_streamed(ssml_text)
    # Pause after 5 seconds
except Exception:
    pass
#
# time.sleep(3)
# # Demonstrate saving audio to a file
try:
    text = "Test saving speech to file for sherpaonnx"
    ssml_text = tts.ssml.add(text)
    output_file = Path("output_sherpaonnx.wav")
    tts.speak_streamed(ssml_text, str(output_file), audio_format="wav")
#     # or you could do
     #tts.speak(ssml_text)
except Exception:
    pass

def my_callback(word: str, start_time: float, end_time: float) -> None:
    end_time - start_time

def on_start() -> None:
    pass

def on_end() -> None:
    pass

try:
    text = "Hello, This is a word timing test with sherpaonnx"
    tts.connect("onStart", on_start)
    tts.connect("onEnd", on_end)
    tts.start_playback_with_callbacks(text, callback=my_callback)
except Exception:
    pass
